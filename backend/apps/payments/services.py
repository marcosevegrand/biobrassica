import ipaddress
import logging
import re
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services import cancel_unpaid_order, transition_order_status
from apps.payments.models import Payment

logger = logging.getLogger(__name__)

PAYMENT_FAILURE_STATUSES = {'failed', 'error', 'cancelled', 'canceled', 'declined', 'refused', 'expired'}
STRIPE_CHECKOUT_EXPIRY_WINDOW = timedelta(hours=1)

EMAIL_RE = re.compile(r'([A-Z0-9._%+-]+)@([A-Z0-9.-]+\.[A-Z]{2,})', re.IGNORECASE)
PHONE_RE = re.compile(r'(?<!\d)(\+?\d[\d\s-]{6,}\d)(?!\d)')
SENSITIVE_KEY_RE = re.compile(r'(secret|token|password|key)', re.IGNORECASE)


class PaymentProcessingError(Exception):
    pass


class PaymentTransitionError(PaymentProcessingError):
    pass


def _mask_string(value, *, keep_start=2, keep_end=2):
    text = str(value or '').strip()
    if not text:
        return ''
    if len(text) <= keep_start + keep_end:
        return '*' * len(text)
    return f'{text[:keep_start]}***{text[-keep_end:]}'


def _redact_free_text(value):
    redacted = EMAIL_RE.sub(lambda match: f'{match.group(1)[:2]}***@{match.group(2)}', str(value))
    return PHONE_RE.sub(lambda match: _mask_string(match.group(1), keep_start=3, keep_end=2), redacted)


def sanitize_callback_payload(payload):
    sanitized = {}

    for key, value in dict(payload).items():
        current_value = value[0] if isinstance(value, list) and len(value) == 1 else value

        if isinstance(current_value, list):
            current_value = [_redact_free_text(item) for item in current_value]
        elif isinstance(current_value, dict):
            current_value = {
                nested_key: '[redacted]' if SENSITIVE_KEY_RE.search(str(nested_key)) else _redact_free_text(nested_value)
                for nested_key, nested_value in current_value.items()
            }
        elif SENSITIVE_KEY_RE.search(str(key)):
            current_value = '[redacted]'
        elif 'phone' in str(key).lower() or 'mobile' in str(key).lower():
            current_value = _mask_string(current_value, keep_start=3, keep_end=2)
        else:
            current_value = _redact_free_text(current_value)

        sanitized[key] = current_value

    return sanitized


def anonymize_ip_address(ip_address):
    candidate = (ip_address or '').split(',')[0].strip()
    if not candidate:
        return '0.0.0.0'

    try:
        parsed = ipaddress.ip_address(candidate)
    except ValueError:
        return '0.0.0.0'

    if parsed.version == 4:
        parts = candidate.split('.')
        return '.'.join(parts[:3] + ['0'])

    network = ipaddress.IPv6Network(f'{parsed}/64', strict=False)
    return str(network.network_address)


def send_payment_notifications(payment) -> None:
    order = payment.order
    lang = (order.language or 'pt').lower()
    if order.is_shipping:
        fulfillment_label = {
            'en': 'Shipping address',
            'fr': 'Adresse de livraison',
        }.get(lang, 'Morada de envio')
        fulfillment_value = order.shipping_address_display
    else:
        fulfillment_label = {
            'en': 'Pickup location',
            'fr': 'Lieu de retrait',
        }.get(lang, 'Local de levantamento')
        fulfillment_value = order.get_pickup_location_display()

    customer_subject = {
        'en': f'Payment confirmed for order #{order.pk}',
        'fr': f'Paiement confirmé pour la commande #{order.pk}',
    }.get(lang, f'Pagamento confirmado para a encomenda #{order.pk}')

    customer_body = {
        'en': (
            f'Hello {order.name},\n\n'
            f'Your payment for order #{order.pk} has been confirmed.\n'
            f'Total: {order.total:.2f}€\n'
            f'{fulfillment_label}: {fulfillment_value}\n\n'
            'We will contact you when the order is ready.'
        ),
        'fr': (
            f'Bonjour {order.name},\n\n'
            f'Le paiement de votre commande #{order.pk} a été confirmé.\n'
            f'Total : {order.total:.2f}€\n'
            f'{fulfillment_label} : {fulfillment_value}\n\n'
            'Nous vous contacterons lorsque la commande sera prête.'
        ),
    }.get(
        lang,
        (
            f'Olá {order.name},\n\n'
            f'O pagamento da sua encomenda #{order.pk} foi confirmado.\n'
            f'Total: {order.total:.2f}€\n'
            f'{fulfillment_label}: {fulfillment_value}\n\n'
            'Entraremos em contacto quando a encomenda estiver pronta.'
        ),
    )

    try:
        send_mail(
            customer_subject,
            customer_body,
            settings.DEFAULT_FROM_EMAIL,
            [order.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception('Failed to send customer confirmation for order %s', order.pk)

    if settings.STAFF_NOTIFICATION_EMAILS:
        try:
            send_mail(
                f'Pagamento confirmado #{order.pk}',
                (
                    f'Encomenda #{order.pk} paga com sucesso.\n'
                    f'Cliente: {order.name} <{order.email}>\n'
                    f'Total: {order.total:.2f}€\n'
                    f'Método: {payment.method_label}\n'
                    f'{fulfillment_label}: {fulfillment_value}'
                ),
                settings.DEFAULT_FROM_EMAIL,
                settings.STAFF_NOTIFICATION_EMAILS,
                fail_silently=False,
            )
        except Exception:
            logger.exception('Failed to send staff notification for order %s', order.pk)


def schedule_payment_notifications(payment) -> None:
    payment_id = payment.pk
    connection = transaction.get_connection()
    scheduled = getattr(connection, '_biobrassica_payment_notifications', None)
    if scheduled is None:
        scheduled = set()
        connection._biobrassica_payment_notifications = scheduled

    if payment_id in scheduled:
        return

    scheduled.add(payment_id)

    def _send_notifications():
        try:
            refreshed_payment = payment.__class__.objects.select_related('order').get(pk=payment_id)
            if refreshed_payment.status == Payment.Status.PAID:
                send_payment_notifications(refreshed_payment)
        finally:
            scheduled.discard(payment_id)

    transaction.on_commit(_send_notifications)


def _raise_payment_validation_error(error):
    if hasattr(error, 'message_dict'):
        message = '; '.join(
            f'{field}: {", ".join(messages)}'
            for field, messages in error.message_dict.items()
        )
    else:
        message = '; '.join(error.messages)
    raise PaymentTransitionError(message)


def _append_order_note(order, note):
    existing_notes = (order.notes or '').strip()
    if note in existing_notes:
        return False

    order.notes = f'{existing_notes}\n\n{note}' if existing_notes else note
    order.save(update_fields=['notes', 'updated_at'])
    return True


def transition_payment_status(payment, new_status, *, reason='', source=''):
    if payment.status == new_status:
        if reason and payment.last_error != reason:
            payment.last_error = reason
            payment.save(update_fields=['last_error'])
        return False

    if not payment.can_transition_to(new_status):
        raise PaymentTransitionError('Transição de estado inválida para o pagamento.')

    payment.status = new_status

    if new_status == Payment.Status.PAID:
        payment.paid_at = timezone.now()
        payment.last_error = ''
    elif new_status == Payment.Status.PENDING:
        payment.paid_at = None
        payment.last_error = ''
    else:
        payment.paid_at = None
        payment.last_error = reason

    try:
        payment.full_clean()
    except ValidationError as error:
        _raise_payment_validation_error(error)

    payment.save(update_fields=['status', 'paid_at', 'last_error'])
    if source:
        logger.info('Payment %s transitioned to %s via %s', payment.pk, new_status, source)
    return True


def mark_payment_paid(payment, *, source: str) -> bool:
    if payment.status == payment.Status.PAID:
        return False

    transition_payment_status(payment, payment.Status.PAID, source=source)

    if payment.order.status != Order.Status.PAID:
        transition_order_status(payment.order, Order.Status.PAID)

    logger.info('Payment %s marked as paid via %s', payment.pk, source)
    return True


def mark_payment_failed(payment, *, reason: str) -> bool:
    changed = transition_payment_status(payment, payment.Status.FAILED, reason=reason, source='payment_failure')

    if payment.order.status == Order.Status.PAYMENT_PENDING:
        transition_order_status(payment.order, Order.Status.PENDING)

    logger.warning('Payment %s marked as failed: %s', payment.pk, reason)
    return changed


def expire_pending_payment(payment, *, reason='payment expired'):
    if payment.status == Payment.Status.EXPIRED:
        return False

    changed = transition_payment_status(payment, Payment.Status.EXPIRED, reason=reason, source='payment_expiry')
    if payment.order.status == Order.Status.PAYMENT_PENDING:
        transition_order_status(payment.order, Order.Status.PENDING)
    return changed


def expire_stale_pending_payments(*, payment=None, now=None):
    reference_time = now or timezone.now()

    if payment is not None:
        if payment.status != Payment.Status.PENDING or not payment.expires_at or payment.expires_at > reference_time:
            return False

        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
            if locked_payment.status != Payment.Status.PENDING:
                return False
            if not locked_payment.expires_at or locked_payment.expires_at > reference_time:
                return False
            return expire_pending_payment(locked_payment)

    payment_ids = list(
        Payment.objects.filter(
            status=Payment.Status.PENDING,
            expires_at__isnull=False,
            expires_at__lte=reference_time,
        ).values_list('pk', flat=True)
    )
    expired_count = 0
    for payment_id in payment_ids:
        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment_id)
            if locked_payment.status != Payment.Status.PENDING:
                continue
            if not locked_payment.expires_at or locked_payment.expires_at > reference_time:
                continue
            if expire_pending_payment(locked_payment):
                expired_count += 1
    return expired_count


def reset_payment(order, method):
    payment, _ = Payment.objects.get_or_create(
        order=order,
        defaults={
            'method': method,
            'amount': order.total,
        },
    )

    if payment.status != Payment.Status.PENDING:
        transition_payment_status(payment, Payment.Status.PENDING, source='payment_reset')

    payment.method = method
    payment.amount = order.total
    payment.stripe_session_id = ''
    payment.stripe_payment_intent_id = ''
    payment.checkout_url = ''
    payment.last_error = ''
    payment.paid_at = None
    payment.expires_at = None
    try:
        payment.full_clean()
    except ValidationError as error:
        _raise_payment_validation_error(error)
    payment.save()

    if order.status != Order.Status.PAYMENT_PENDING:
        transition_order_status(order, Order.Status.PAYMENT_PENDING)

    return payment


def configure_stripe_checkout(payment, *, session_id, checkout_url, payment_intent_id='', expires_at=None):
    payment.stripe_session_id = session_id
    payment.stripe_payment_intent_id = payment_intent_id
    payment.checkout_url = checkout_url
    payment.expires_at = expires_at or (timezone.now() + STRIPE_CHECKOUT_EXPIRY_WINDOW)
    try:
        payment.full_clean()
    except ValidationError as error:
        _raise_payment_validation_error(error)
    payment.save(update_fields=['stripe_session_id', 'stripe_payment_intent_id', 'checkout_url', 'expires_at'])
    return payment


def mark_payment_refunded(payment, *, reason='stripe refund'):
    changed = transition_payment_status(payment, Payment.Status.REFUNDED, reason=reason, source='stripe_refund')

    order = payment.order
    if changed and order.status == Order.Status.PAID:
        cancel_unpaid_order(order)
    elif changed and order.status in {Order.Status.PREPARING, Order.Status.READY}:
        timestamp = timezone.localtime().strftime('%d/%m/%Y %H:%M')
        _append_order_note(order, f'Reembolso registado em {timestamp}: {reason}. Rever operação manualmente.')

    logger.info('Payment %s marked as refunded: %s', payment.pk, reason)
    return changed


class StripeService:
    def _client_options(self):
        return {'api_key': settings.STRIPE_SECRET_KEY}

    def create_checkout_session(self, *, order, payment, success_url: str, cancel_url: str) -> dict:
        # Get order items with product details
        order_items = order.items.all()
        
        # Build line items for each product in the order
        line_items = [
            {
                'quantity': item.quantity,
                'price_data': {
                    'currency': settings.STRIPE_CURRENCY,
                    'unit_amount': int((item.price * 100).quantize(Decimal('1'))),
                    'product_data': {
                        'name': item.product_name,
                    },
                },
            }
            for item in order_items
        ]
        
        # Format order number as #0000001
        order_number = f'#{order.pk:07d}'
        
        # Add an order summary line if there are multiple items
        if len(line_items) > 1:
            line_items.append({
                'quantity': 1,
                'price_data': {
                    'currency': settings.STRIPE_CURRENCY,
                    'unit_amount': 0,
                    'product_data': {
                        'name': f'Encomenda {order_number}',
                    },
                },
            })
        else:
            # For single item, just use the order number in the product name
            line_items[0]['price_data']['product_data']['name'] = f'{line_items[0]["price_data"]["product_data"]["name"]} (Encomenda {order_number})'
        
        session = stripe.checkout.Session.create(
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=order.email,
            payment_method_types=['card', 'mb_way'],
            metadata={
                'order_id': str(order.pk),
                'payment_id': str(payment.pk),
            },
            line_items=line_items,
            **self._client_options(),
        )
        return {
            'session_id': session.id,
            'payment_intent_id': getattr(session, 'payment_intent', '') or '',
            'checkout_url': session.url or '',
            'expires_at': datetime.fromtimestamp(session.expires_at, tz=dt_timezone.utc) if getattr(session, 'expires_at', None) else None,
        }

    def retrieve_checkout_session(self, session_id: str):
        return stripe.checkout.Session.retrieve(session_id, **self._client_options())

    def construct_webhook_event(self, payload: bytes, signature: str):
        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )


stripe_service = StripeService()
