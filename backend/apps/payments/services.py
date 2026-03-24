import ipaddress
import logging
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.services import transition_order_status
from apps.payments.models import Payment

logger = logging.getLogger(__name__)

PAYMENT_SUCCESS_STATUSES = {'paid', 'success', 'completed', 'ok'}
PAYMENT_FAILURE_STATUSES = {'failed', 'error', 'cancelled', 'canceled', 'declined', 'refused', 'expired'}

EMAIL_RE = re.compile(r'([A-Z0-9._%+-]+)@([A-Z0-9.-]+\.[A-Z]{2,})', re.IGNORECASE)
PHONE_RE = re.compile(r'(?<!\d)(\+?\d[\d\s-]{6,}\d)(?!\d)')
SENSITIVE_KEY_RE = re.compile(r'(secret|token|password|anti[_-]?phishing|key)', re.IGNORECASE)


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


def normalize_provider_status(value: str | None) -> str:
    return (value or '').strip().lower().replace(' ', '_')


def parse_provider_amount(value) -> Decimal | None:
    if value in (None, ''):
        return None

    normalized = str(value).strip().replace('EUR', '').replace('€', '').replace(',', '.')
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        return None


def parse_provider_datetime(value):
    if not value:
        return None
    if hasattr(value, 'tzinfo'):
        return value
    parsed = parse_datetime(str(value).strip())
    return parsed


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
                    f'Método: {payment.get_method_display()}\n'
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


def get_default_mbway_expiry(reference_time=None):
    base_time = reference_time or timezone.now()
    return base_time + timedelta(minutes=settings.MBWAY_PAYMENT_EXPIRY_MINUTES)


def _raise_payment_validation_error(error):
    if hasattr(error, 'message_dict'):
        message = '; '.join(
            f'{field}: {", ".join(messages)}'
            for field, messages in error.message_dict.items()
        )
    else:
        message = '; '.join(error.messages)
    raise PaymentTransitionError(message)


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


def expire_pending_payment(payment, *, reason='mbway expired'):
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


def configure_mbway_payment(payment, *, phone, request_id, transaction_id=''):
    payment.ifthenpay_request_id = request_id
    payment.mbway_phone = phone
    payment.mbway_transaction_id = transaction_id
    payment.expires_at = get_default_mbway_expiry()
    try:
        payment.full_clean()
    except ValidationError as error:
        _raise_payment_validation_error(error)
    payment.save(update_fields=['ifthenpay_request_id', 'mbway_phone', 'mbway_transaction_id', 'expires_at'])
    return payment


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
    payment.ifthenpay_request_id = ''
    payment.mb_entity = ''
    payment.mb_reference = ''
    payment.mbway_phone = ''
    payment.mbway_transaction_id = ''
    payment.checkout_url = ''
    payment.last_error = ''
    payment.paid_at = None
    payment.expires_at = get_default_mbway_expiry() if method == Payment.Method.MBWAY else None
    try:
        payment.full_clean()
    except ValidationError as error:
        _raise_payment_validation_error(error)
    payment.save()

    if order.status != Order.Status.PAYMENT_PENDING:
        transition_order_status(order, Order.Status.PAYMENT_PENDING)

    return payment


class IfThenPayService:
    """
    Wraps ifthenpay's REST API for Multibanco, MBWay, and Credit Card payments.

    Requires these settings:
        IFTHENPAY_BACKOFFICE_KEY
        IFTHENPAY_MB_ENTITY
        IFTHENPAY_MB_SUBENTITY
        IFTHENPAY_MBWAY_KEY
        IFTHENPAY_CCARD_KEY
        IFTHENPAY_ANTI_PHISHING_KEY
        IFTHENPAY_CALLBACK_URL
    """

    MB_URL = 'https://ifthenpay.com/api/multibanco/reference/init'
    MBWAY_URL = 'https://ifthenpay.com/api/mbway/payment'
    MBWAY_STATUS_URL = 'https://ifthenpay.com/api/mbway/status'
    CCARD_URL = 'https://ifthenpay.com/api/creditcard/init'

    def create_multibanco_reference(self, order_id: str, amount: Decimal) -> dict:
        """
        Generate a Multibanco payment reference.
        Returns: {entity, reference, request_id} or raises exception.
        """
        payload = {
            'mbKey': f'{settings.IFTHENPAY_MB_ENTITY}-{settings.IFTHENPAY_MB_SUBENTITY}',
            'orderId': str(order_id),
            'amount': str(amount),
        }

        response = requests.post(self.MB_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return {
            'entity': data.get('Entity', ''),
            'reference': data.get('Reference', ''),
            'request_id': data.get('RequestId', str(order_id)),
            'expires_at': parse_provider_datetime(data.get('ExpiryDate') or data.get('Expiry')),
        }

    def create_mbway_payment(self, order_id: str, amount: Decimal, phone: str) -> dict:
        """
        Push an MBWay payment request to the user's phone.
        Returns: {request_id, status}
        """
        payload = {
            'mbWayKey': settings.IFTHENPAY_MBWAY_KEY,
            'orderId': str(order_id),
            'amount': str(amount),
            'mobileNumber': phone,
            'description': f'Biobrassica Encomenda #{order_id}',
        }

        response = requests.post(self.MBWAY_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return {
            'request_id': data.get('RequestId', ''),
            'status': data.get('Status', ''),
            'transaction_id': data.get('TransactionId', ''),
        }

    def check_mbway_status(self, request_id: str) -> str:
        """Check the status of an MBWay payment."""
        payload = {
            'mbWayKey': settings.IFTHENPAY_MBWAY_KEY,
            'requestId': request_id,
        }

        response = requests.post(self.MBWAY_STATUS_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return data.get('Status', 'pending')

    def create_credit_card_payment(self, order_id: str, amount: Decimal, return_url: str) -> dict:
        """
        Generate a credit card payment URL (redirect to ifthenpay hosted page).
        Returns: {payment_url, request_id}
        """
        payload = {
            'ccardKey': settings.IFTHENPAY_CCARD_KEY,
            'orderId': str(order_id),
            'amount': str(amount),
            'successUrl': return_url,
            'errorUrl': return_url,
            'cancelUrl': return_url,
            'language': 'pt',
        }

        response = requests.post(self.CCARD_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return {
            'payment_url': data.get('PaymentUrl', ''),
            'request_id': data.get('RequestId', ''),
        }


ifthenpay_service = IfThenPayService()
