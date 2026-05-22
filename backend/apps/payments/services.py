import ipaddress
import logging
import re
from decimal import Decimal
from typing import Literal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.core.site_content import get_bank_transfer_details, get_manual_mbway_details, payments_are_enabled

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r'([A-Z0-9._%+-]+)@([A-Z0-9.-]+\.[A-Z]{2,})', re.IGNORECASE)
PHONE_RE = re.compile(r'(?<!\d)(\+?\d[\d\s-]{6,}\d)(?!\d)')


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
        fulfillment_label = {'en': 'Shipping address', 'fr': 'Adresse de livraison'}.get(lang, 'Morada de envio')
        fulfillment_value = order.shipping_address_display
    else:
        fulfillment_label = {'en': 'Pickup location', 'fr': 'Lieu de retrait'}.get(lang, 'Local de levantamento')
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
            if refreshed_payment.status == Payment.Status.CONFIRMED:
                send_payment_notifications(refreshed_payment)
        finally:
            scheduled.discard(payment_id)

    transaction.on_commit(_send_notifications)


def send_manual_payment_rejection_notification(payment, *, reason='') -> None:
    order = payment.order
    lang = (order.language or 'pt').lower()
    safe_reason = _sanitize_payment_error(reason)

    subject = {
        'en': f'Payment not approved for order #{order.pk}',
        'fr': f'Paiement non validé pour la commande #{order.pk}',
    }.get(lang, f'Pagamento não validado para a encomenda #{order.pk}')

    reason_line = ''
    if safe_reason:
        reason_line = {
            'en': f'Reason: {safe_reason}\n\n',
            'fr': f'Raison : {safe_reason}\n\n',
        }.get(lang, f'Motivo: {safe_reason}\n\n')

    body = {
        'en': (
            f'Hello {order.name},\n\nWe could not validate the payment for order #{order.pk}.\n'
            f'{reason_line}The order was cancelled. Please place a new order or contact us.'
        ),
        'fr': (
            f'Bonjour {order.name},\n\nNous n’avons pas pu valider le paiement de votre commande #{order.pk}.\n'
            f'{reason_line}La commande a été annulée. Passez une nouvelle commande ou contactez-nous.'
        ),
    }.get(
        lang,
        (
            f'Olá {order.name},\n\nNão foi possível validar o pagamento da sua encomenda #{order.pk}.\n'
            f'{reason_line}A encomenda foi cancelada. Faça uma nova encomenda ou entre em contacto connosco.'
        ),
    )

    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=False)
    except Exception:
        logger.exception('Failed to send manual rejection email for order %s', order.pk)


def schedule_manual_payment_rejection_notification(payment, *, reason='') -> None:
    payment_id = payment.pk
    safe_reason = _sanitize_payment_error(reason)

    def _send_notification():
        refreshed_payment = payment.__class__.objects.select_related('order').get(pk=payment_id)
        if refreshed_payment.status == Payment.Status.CANCELLED and refreshed_payment.order.status == Order.Status.CANCELLED:
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
    return _redact_free_text(normalized_reason)[:255]


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

    if new_status == Payment.Status.CONFIRMED:
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


def mark_payment_confirmed(payment, *, source: str) -> bool:
    """Confirm a payment and sync the order's payment state.

    Requires payment.amount == payment.order.total — an underpaid or
    misconfigured payment cannot be confirmed.
    """
    if payment.status == payment.Status.CONFIRMED:
        return False
    if payment.amount != payment.order.total:
        raise PaymentTransitionError(_('O valor do pagamento não corresponde ao total da encomenda.'))
    transition_payment_status(payment, payment.Status.CONFIRMED, source=source)
    if payment.order.payment_state != Order.PaymentState.CONFIRMED:
        from apps.orders.services import transition_payment_state

        transition_payment_state(payment.order, Order.PaymentState.CONFIRMED)
    logger.info('Payment %s marked as confirmed via %s', payment.pk, source)
    return True


def finalize_successful_payment(payment, *, source: str) -> bool:
    changed = mark_payment_confirmed(payment, source=source)
    if changed:
        schedule_payment_notifications(payment)
    return changed


def cancel_payment(payment, *, reason: str, source: str = 'payment_cancellation') -> bool:
    changed = transition_payment_status(payment, payment.Status.CANCELLED, reason=reason, source=source)
    if payment.order.payment_state != Order.PaymentState.CANCELLED:
        from apps.orders.services import transition_payment_state

        transition_payment_state(payment.order, Order.PaymentState.CANCELLED)
    logger.warning('Payment %s cancelled: %s', payment.pk, reason)
    return changed


def reset_payment(order, method):
    from apps.orders.services import transition_payment_state

    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=order.pk)
        if locked_order.status == Order.Status.CANCELLED:
            raise PaymentTransitionError(_('A encomenda foi cancelada e já não aceita pagamentos.'))

        payment, _ = Payment.objects.select_for_update().get_or_create(
            order=locked_order,
            defaults={'method': method, 'amount': locked_order.total},
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

        from apps.core.models import ShopSettings

        settings_obj = ShopSettings.objects.filter(pk=1).first()
        timeout_minutes = getattr(settings_obj, 'payment_timeout_minutes', 30) if settings_obj else 30
        if timeout_minutes > 0:
            payment.expires_at = timezone.now() + timezone.timedelta(minutes=timeout_minutes)

        try:
            payment.full_clean()
        except ValidationError as error:
            _raise_payment_validation_error(error)
        payment.save()

        if locked_order.payment_state != Order.PaymentState.PENDING:
            transition_payment_state(locked_order, Order.PaymentState.PENDING)

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


class BasePaymentService:
    method = ''

    def is_available(self) -> bool:
        return True

    def checkout_option(self):
        raise NotImplementedError

    def payment_status_context(self, payment):
        raise NotImplementedError

    def initiate_payment(self, *, order, payment, success_url: str, cancel_url: str, status_url: str) -> str:
        raise NotImplementedError

    def refresh_pending_payment(self, payment) -> Literal['pending', 'confirmed', 'cancelled']:
        return 'pending'


class ManualMbWayService(BasePaymentService):
    method = Payment.Method.MBWAY_MANUAL

    def is_available(self) -> bool:
        return get_manual_mbway_details()['configured']

    def checkout_option(self):
        return {
            'method': self.method,
            'title': 'MB WAY',
            'badge': 'MBW',
            'description': gettext_lazy('Pague por MB WAY com validação manual no backoffice.'),
            'submit_label': gettext_lazy('Confirmar encomenda'),
        }

    def payment_status_context(self, payment):
        provider_data = _provider_data(payment)
        manual_mbway = get_manual_mbway_details()
        mbway_number = provider_data.get('mbway_number') or manual_mbway.get('number') or '—'
        order_reference = provider_data.get('order_reference') or f'#{payment.order.pk:07d}'

        if payment.order.status == Order.Status.CANCELLED:
            description = _('O pagamento MB WAY não foi validado e a encomenda foi cancelada.')
            state_label = _('Pagamento rejeitado')
        elif payment.status == Payment.Status.CANCELLED:
            description = _('O pagamento MB WAY foi cancelado. Pode voltar a escolher um método de pagamento para esta encomenda.')
            state_label = _('Pagamento cancelado')
        else:
            description = _(
                f'Transfira o valor por MB WAY para o número abaixo, indicando na descrição "Encomenda {order_reference}". '
                'A encomenda fica em espera até validarmos o pagamento.'
            )
            state_label = _('A aguardar validação manual')

        return {
            'title': 'MB WAY',
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


class ManualBankTransferService(BasePaymentService):
    method = Payment.Method.BANK_TRANSFER

    def _bank_details(self):
        return get_bank_transfer_details()

    def is_available(self) -> bool:
        details = self._bank_details()
        return bool(details['enabled'] and details['iban'] and details['beneficiary'])

    def checkout_option(self):
        return {
            'method': self.method,
            'title': gettext_lazy('Transferência bancária'),
            'badge': 'TRF',
            'description': gettext_lazy('Transfira o valor para o IBAN indicado e aguarde validação no backoffice.'),
            'submit_label': gettext_lazy('Confirmar encomenda'),
        }

    def payment_status_context(self, payment):
        provider_data = _provider_data(payment)
        bank = self._bank_details()
        beneficiary = provider_data.get('beneficiary') or bank['beneficiary'] or '—'
        iban = provider_data.get('iban') or bank['iban'] or '—'
        bic = provider_data.get('bic') or bank['bic']
        order_reference = provider_data.get('order_reference') or f'#{payment.order.pk:07d}'

        if payment.order.status == Order.Status.CANCELLED:
            description = _('A transferência não foi validada e a encomenda foi cancelada.')
            state_label = _('Pagamento rejeitado')
        elif payment.status == Payment.Status.CANCELLED:
            description = _('A transferência foi cancelada. Pode voltar a escolher um método de pagamento para esta encomenda.')
            state_label = _('Pagamento cancelado')
        else:
            description = _(
                f'Faça a transferência para os dados abaixo, indicando na descrição "Encomenda {order_reference}". '
                'A encomenda fica em espera até validarmos a receção.'
            )
            state_label = _('A aguardar receção da transferência')

        rows = [
            (_('Valor'), f'{payment.amount:.2f}€'),
            (_('Beneficiário'), beneficiary),
            (_('IBAN'), iban),
        ]
        if bic:
            rows.append((_('BIC/SWIFT'), bic))
        rows.extend([
            (_('Referência'), order_reference),
            (_('Estado'), state_label),
        ])

        return {
            'title': _('Transferência bancária'),
            'description': description,
            'action_url': '',
            'action_label': '',
            'detail_rows': rows,
        }

    def initiate_payment(self, *, order, payment, success_url: str, cancel_url: str, status_url: str) -> str:
        del success_url, cancel_url
        if not payments_are_enabled():
            raise PaymentDisabledError('Payments are temporarily disabled.')
        if not self.is_available():
            raise PaymentProcessingError(_('A transferência bancária não está disponível neste momento.'))
        bank = self._bank_details()
        configure_provider_payment(
            payment,
            provider_data={
                'beneficiary': bank['beneficiary'],
                'iban': bank['iban'],
                'bic': bank['bic'],
                'order_reference': f'#{order.pk:07d}',
            },
        )
        return status_url


manual_mbway_service = ManualMbWayService()
bank_transfer_service = ManualBankTransferService()

PAYMENT_SERVICES: dict[str, BasePaymentService] = {
    manual_mbway_service.method: manual_mbway_service,
    bank_transfer_service.method: bank_transfer_service,
}


def get_payment_service(method: str | None = None) -> BasePaymentService:
    if method is None:
        for service in PAYMENT_SERVICES.values():
            if service.is_available():
                return service
        raise UnsupportedPaymentProviderError('Nenhum método de pagamento disponível.')
    try:
        return PAYMENT_SERVICES[str(method)]
    except KeyError as error:
        raise UnsupportedPaymentProviderError(f'Unsupported payment method: {method}') from error


def available_payment_services() -> list[BasePaymentService]:
    return [service for service in PAYMENT_SERVICES.values() if service.is_available()]
