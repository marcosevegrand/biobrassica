import ipaddress
import json
import logging
import re
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from typing import Any, Literal, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.orders.models import Order
from apps.orders.services import cancel_unpaid_order, transition_order_status
from apps.payments.models import Payment
from apps.core.site_content import get_manual_mbway_details, payments_are_enabled

logger = logging.getLogger(__name__)

PAYMENT_FAILURE_STATUSES = {'failed', 'error', 'cancelled', 'canceled', 'declined', 'refused', 'expired'}
STRIPE_CHECKOUT_EXPIRY_WINDOW = timedelta(hours=1)
IFTHENPAY_TIMEOUT_SECONDS = 15

EMAIL_RE = re.compile(r'([A-Z0-9._%+-]+)@([A-Z0-9.-]+\.[A-Z]{2,})', re.IGNORECASE)
PHONE_RE = re.compile(r'(?<!\d)(\+?\d[\d\s-]{6,}\d)(?!\d)')
SENSITIVE_KEY_RE = re.compile(r'(secret|token|password|key)', re.IGNORECASE)


class PaymentProcessingError(Exception):
    pass


class PaymentTransitionError(PaymentProcessingError):
    pass


class PaymentDisabledError(PaymentProcessingError):
    pass


class UnsupportedPaymentProviderError(PaymentProcessingError):
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


def send_manual_payment_rejection_notification(payment, *, reason='') -> None:
    order = payment.order
    lang = (order.language or 'pt').lower()
    safe_reason = _sanitize_payment_error(reason)

    customer_subject = {
        'en': f'MB WAY payment not approved for order #{order.pk}',
        'fr': f'Paiement MB WAY non validé pour la commande #{order.pk}',
    }.get(lang, f'Pagamento MB WAY não validado para a encomenda #{order.pk}')

    reason_line = ''
    if safe_reason:
        reason_line = {
            'en': f'Reason: {safe_reason}\n\n',
            'fr': f'Raison : {safe_reason}\n\n',
        }.get(lang, f'Motivo: {safe_reason}\n\n')

    customer_body = {
        'en': (
            f'Hello {order.name},\n\n'
            f'We could not validate the MB WAY payment for order #{order.pk}.\n'
            f'{reason_line}'
            'The order was cancelled. If you still want the products, please place a new order or contact us.'
        ),
        'fr': (
            f'Bonjour {order.name},\n\n'
            f'Nous n’avons pas pu valider le paiement MB WAY de votre commande #{order.pk}.\n'
            f'{reason_line}'
            'La commande a été annulée. Si vous souhaitez toujours les produits, passez une nouvelle commande ou contactez-nous.'
        ),
    }.get(
        lang,
        (
            f'Olá {order.name},\n\n'
            f'Não foi possível validar o pagamento MB WAY da sua encomenda #{order.pk}.\n'
            f'{reason_line}'
            'A encomenda foi cancelada. Se continuar interessado nos produtos, faça uma nova encomenda ou entre em contacto connosco.'
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
        logger.exception('Failed to send manual MB WAY rejection email for order %s', order.pk)


def schedule_manual_payment_rejection_notification(payment, *, reason='') -> None:
    payment_id = payment.pk
    safe_reason = _sanitize_payment_error(reason)

    def _send_notification():
        refreshed_payment = payment.__class__.objects.select_related('order').get(pk=payment_id)
        if refreshed_payment.status == Payment.Status.FAILED and refreshed_payment.order.status == Order.Status.CANCELLED:
            send_manual_payment_rejection_notification(refreshed_payment, reason=safe_reason)

    transaction.on_commit(_send_notification)


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


def _format_amount(amount: Decimal) -> str:
    return f'{amount:.2f}'


def _sanitize_payment_error(reason: str) -> str:
    normalized_reason = ' '.join(str(reason or '').split())
    if not normalized_reason:
        return ''

    redacted_reason = _redact_free_text(normalized_reason)
    return redacted_reason[:255]


def _provider_data(payment) -> dict:
    data = payment.provider_data if isinstance(payment.provider_data, dict) else {}
    return dict(data)


def _store_provider_fields(
    payment,
    *,
    provider_reference='',
    provider_payment_id='',
    checkout_url='',
    expires_at=None,
    provider_data=None,
):
    payment.provider_reference = provider_reference
    payment.provider_payment_id = provider_payment_id
    payment.provider_data = provider_data or {}
    payment.checkout_url = checkout_url
    payment.expires_at = expires_at
    try:
        payment.full_clean()
    except ValidationError as error:
        _raise_payment_validation_error(error)
    payment.save(update_fields=['provider_reference', 'provider_payment_id', 'provider_data', 'checkout_url', 'expires_at'])
    return payment


def transition_payment_status(payment, new_status, *, reason='', source=''):
    safe_reason = _sanitize_payment_error(reason)

    if payment.status == new_status:
        if safe_reason and payment.last_error != safe_reason:
            payment.last_error = safe_reason
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
        payment.last_error = safe_reason

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


def finalize_successful_payment(payment, *, source: str) -> bool:
    changed = mark_payment_paid(payment, source=source)
    if changed:
        schedule_payment_notifications(payment)
    return changed


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
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order.pk)
        payment, _ = Payment.objects.select_for_update().get_or_create(
            order=locked_order,
            defaults={
                'method': method,
                'amount': locked_order.total,
            },
        )

        if payment.status != Payment.Status.PENDING:
            transition_payment_status(payment, Payment.Status.PENDING, source='payment_reset')

        payment.method = method
        payment.amount = locked_order.total
        payment.provider_reference = ''
        payment.provider_payment_id = ''
        payment.provider_data = {}
        payment.checkout_url = ''
        payment.last_error = ''
        payment.paid_at = None
        payment.expires_at = None
        try:
            payment.full_clean()
        except ValidationError as error:
            _raise_payment_validation_error(error)
        payment.save()

        if locked_order.status != Order.Status.PAYMENT_PENDING:
            transition_order_status(locked_order, Order.Status.PAYMENT_PENDING)

        return payment


def configure_provider_payment(
    payment,
    *,
    provider_reference='',
    provider_payment_id='',
    checkout_url='',
    expires_at=None,
    provider_data=None,
):
    return _store_provider_fields(
        payment,
        provider_reference=provider_reference,
        provider_payment_id=provider_payment_id,
        checkout_url=checkout_url,
        expires_at=expires_at,
        provider_data=provider_data,
    )


def configure_stripe_checkout(payment, *, session_id, checkout_url, payment_intent_id='', expires_at=None):
    return configure_provider_payment(
        payment,
        provider_reference=session_id,
        provider_payment_id=payment_intent_id,
        checkout_url=checkout_url,
        expires_at=expires_at or (timezone.now() + STRIPE_CHECKOUT_EXPIRY_WINDOW),
        provider_data=_provider_data(payment),
    )


def mark_payment_refunded(payment, *, reason='stripe refund'):
    changed = transition_payment_status(payment, Payment.Status.REFUNDED, reason=reason, source='stripe_refund')
    safe_reason = _sanitize_payment_error(reason)

    order = payment.order
    if changed and order.status == Order.Status.PAID:
        cancel_unpaid_order(order)
    elif changed and order.status in {Order.Status.PREPARING, Order.Status.READY}:
        timestamp = timezone.localtime().strftime('%d/%m/%Y %H:%M')
        _append_order_note(order, f'Reembolso registado em {timestamp}: {safe_reason}. Rever operação manualmente.')

    logger.info('Payment %s marked as refunded: %s', payment.pk, reason)
    return changed


class BasePaymentService:
    method = ''

    def checkout_option(self):
        raise NotImplementedError

    def payment_status_context(self, payment):
        raise NotImplementedError

    def initiate_payment(self, *, order, payment, success_url: str, cancel_url: str, status_url: str) -> str:
        raise NotImplementedError

    def refresh_pending_payment(self, payment) -> Literal['pending', 'paid', 'expired']:
        return 'pending'


class StripeService(BasePaymentService):
    method = Payment.Method.STRIPE

    def checkout_option(self):
        return {
            'method': self.method,
            'title': 'Stripe',
            'badge': 'STR',
            'description': _('Pagamento por cartão numa página segura hospedada pela Stripe'),
            'submit_label': _('Continuar para pagamento'),
        }

    def payment_status_context(self, payment):
        return {
            'title': 'Stripe',
            'description': _('Conclua o pagamento na página segura da Stripe. Depois de terminar, esta página é atualizada automaticamente pela confirmação do pagamento.'),
            'action_url': payment.checkout_url,
            'action_label': _('Abrir checkout seguro'),
            'detail_rows': [
                (_('Valor'), f'{payment.amount:.2f}€'),
                (_('Sessão'), payment.masked_provider_reference or '—'),
            ],
        }

    def _client_options(self):
        return {'api_key': settings.STRIPE_SECRET_KEY}

    def initiate_payment(self, *, order, payment, success_url: str, cancel_url: str, status_url: str) -> str:
        response = self.create_checkout_session(
            order=order,
            payment=payment,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        configure_stripe_checkout(
            payment,
            session_id=response['session_id'],
            payment_intent_id=response.get('payment_intent_id', ''),
            checkout_url=response['checkout_url'],
            expires_at=response.get('expires_at'),
        )
        return payment.checkout_url

    def refresh_pending_payment(self, payment):
        if payment.status != Payment.Status.PENDING or not payment.provider_reference:
            return 'pending'

        session = self.retrieve_checkout_session(payment.provider_reference)
        if getattr(session, 'payment_status', '') == 'paid':
            with transaction.atomic():
                locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
                finalize_successful_payment(locked_payment, source='stripe_checkout_poll')
            return 'paid'
        if getattr(session, 'status', '') == 'expired':
            with transaction.atomic():
                locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
                expire_pending_payment(locked_payment, reason='stripe checkout expired (poll)')
            return 'expired'
        return 'pending'

    def create_checkout_session(self, *, order, payment, success_url: str, cancel_url: str) -> dict:
        if not payments_are_enabled():
            raise PaymentDisabledError('Payments are temporarily disabled.')

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
            line_items=cast(Any, line_items),
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


def build_ifthenpay_order_reference(order) -> str:
    order_reference = str(order.pk)
    if len(order_reference) > 15:
        raise PaymentProcessingError('O identificador da encomenda excede o limite suportado pela Ifthenpay.')
    return order_reference


def normalize_mbway_mobile_number(phone: str) -> str:
    digits = re.sub(r'\D+', '', phone or '')
    if digits.startswith('00'):
        digits = digits[2:]

    if digits.startswith('351') and len(digits) == 12:
        subscriber_number = digits[3:]
    elif len(digits) == 9 and digits.startswith('9'):
        subscriber_number = digits
    else:
        raise PaymentProcessingError(_('Indique um telemóvel válido para receber o pedido MB WAY.'))

    if len(subscriber_number) != 9:
        raise PaymentProcessingError(_('Indique um telemóvel válido para receber o pedido MB WAY.'))

    return f'351#{subscriber_number}'


class IfthenpayMbWayService(BasePaymentService):
    method = Payment.Method.IFTHENPAY_MBWAY

    def checkout_option(self):
        return {
            'method': self.method,
            'title': 'Ifthenpay MB WAY',
            'badge': 'MBW',
            'description': _('Pedido de pagamento MB WAY enviado para o telemóvel indicado no checkout'),
            'submit_label': _('Criar pedido MB WAY'),
        }

    def payment_status_context(self, payment):
        provider_data = _provider_data(payment)
        mobile_number = provider_data.get('mobile_number') or payment.order.phone
        return {
            'title': 'Ifthenpay MB WAY',
            'description': _('Confirme o pedido MB WAY no seu telemóvel. Esta página mostra o estado do pagamento assim que a confirmação chegar.'),
            'action_url': '',
            'action_label': '',
            'detail_rows': [
                (_('Valor'), f'{payment.amount:.2f}€'),
                (_('Telemóvel'), _mask_string(mobile_number, keep_start=3, keep_end=2) or '—'),
                (_('Pedido'), payment.masked_provider_reference or '—'),
            ],
        }

    def initiate_payment(self, *, order, payment, success_url: str, cancel_url: str, status_url: str) -> str:
        if not payments_are_enabled():
            raise PaymentDisabledError('Payments are temporarily disabled.')

        mobile_number = normalize_mbway_mobile_number(order.phone)
        order_reference = build_ifthenpay_order_reference(order)
        payload = {
            'mbWayKey': settings.IFTHENPAY_MBWAY_KEY,
            'orderId': order_reference,
            'amount': _format_amount(order.total),
            'mobileNumber': mobile_number,
            'email': order.email,
            'description': f'Encomenda {order_reference}',
        }
        response_data = self._post_json('/spg/payment/mbway', payload)
        response_status = str(response_data.get('Status', '')).strip()
        if response_status != '000':
            raise PaymentProcessingError(
                response_data.get('Message') or _('Não foi possível iniciar o pedido MB WAY.')
            )

        request_id = str(response_data.get('RequestId', '')).strip()
        if not request_id:
            raise PaymentProcessingError(_('A Ifthenpay não devolveu o identificador do pedido MB WAY.'))

        configure_provider_payment(
            payment,
            provider_reference=request_id,
            provider_payment_id='',
            checkout_url='',
            expires_at=None,
            provider_data={
                'mobile_number': mobile_number,
                'order_reference': order_reference,
                'message': str(response_data.get('Message', '')).strip(),
            },
        )
        return status_url

    def _post_json(self, path: str, payload: dict) -> dict:
        body = json.dumps(payload).encode('utf-8')
        request = Request(
            f'{settings.IFTHENPAY_API_BASE_URL}{path}',
            data=body,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            method='POST',
        )
        try:
            with urlopen(request, timeout=IFTHENPAY_TIMEOUT_SECONDS) as response:
                raw_response = response.read().decode('utf-8')
        except HTTPError as error:
            response_body = error.read().decode('utf-8', errors='replace')
            logger.warning('Ifthenpay MB WAY request failed with HTTP %s: %s', error.code, response_body[:200])
            raise PaymentProcessingError(_('Não foi possível contactar a Ifthenpay.')) from error
        except URLError as error:
            logger.warning('Ifthenpay MB WAY request failed: %s', error)
            raise PaymentProcessingError(_('Não foi possível contactar a Ifthenpay.')) from error

        try:
            return json.loads(raw_response or '{}')
        except json.JSONDecodeError as error:
            logger.warning('Ifthenpay MB WAY returned invalid JSON: %s', raw_response[:200])
            raise PaymentProcessingError(_('A Ifthenpay devolveu uma resposta inválida.')) from error


class ManualMbWayService(BasePaymentService):
    method = Payment.Method.MBWAY_MANUAL

    def checkout_option(self):
        return {
            'method': self.method,
            'title': 'MB WAY manual',
            'badge': 'MBW',
            'description': _('Receba instruções para pagar por MB WAY e aguarde validação manual no backoffice.'),
            'submit_label': _('Confirmar encomenda'),
        }

    def payment_status_context(self, payment):
        provider_data = _provider_data(payment)
        manual_mbway = get_manual_mbway_details()
        mbway_number = provider_data.get('mbway_number') or manual_mbway.get('number') or '—'
        order_reference = provider_data.get('order_reference') or f'#{payment.order.pk:07d}'

        if payment.status == Payment.Status.FAILED or payment.order.status == Order.Status.CANCELLED:
            description = _(
                'O pagamento MB WAY não foi validado e a encomenda foi cancelada. Consulte o email enviado para mais detalhes.'
            )
            state_label = _('Pagamento rejeitado')
        else:
            description = _(
                'Transfira o valor por MB WAY para o número abaixo. A encomenda fica em espera até validarmos manualmente o pagamento.'
            )
            state_label = _('A aguardar validação manual')

        return {
            'title': 'MB WAY manual',
            'description': description,
            'action_url': '',
            'action_label': '',
            'detail_rows': [
                (_('Valor'), f'{payment.amount:.2f}€'),
                (_('Número MB WAY'), mbway_number),
                (_('Referência'), order_reference),
                (_('Estado'), state_label),
            ],
        }

    def initiate_payment(self, *, order, payment, success_url: str, cancel_url: str, status_url: str) -> str:
        del success_url, cancel_url

        if not payments_are_enabled():
            raise PaymentDisabledError('Payments are temporarily disabled.')

        manual_mbway = get_manual_mbway_details()
        if not manual_mbway['configured']:
            raise PaymentProcessingError(_('O pagamento MB WAY não está disponível neste momento.'))

        configure_provider_payment(
            payment,
            provider_data={
                'mbway_number': manual_mbway['number'],
                'order_reference': f'#{order.pk:07d}',
            },
        )
        return status_url


stripe_service = StripeService()
ifthenpay_mbway_service = IfthenpayMbWayService()
manual_mbway_service = ManualMbWayService()

PAYMENT_SERVICES: dict[str, BasePaymentService] = {
    stripe_service.method: stripe_service,
    ifthenpay_mbway_service.method: ifthenpay_mbway_service,
    manual_mbway_service.method: manual_mbway_service,
}


def get_payment_service(method: str | None = None) -> BasePaymentService:
    resolved_method = str(method or settings.PAYMENT_PROVIDER)
    try:
        return PAYMENT_SERVICES[resolved_method]
    except KeyError as error:
        raise UnsupportedPaymentProviderError(f'Unsupported payment provider: {resolved_method}') from error


