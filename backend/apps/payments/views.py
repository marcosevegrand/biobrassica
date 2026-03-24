import logging

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from apps.payments.models import Payment, PaymentCallback
from apps.payments.services import (
    PAYMENT_FAILURE_STATUSES,
    PaymentTransitionError,
    anonymize_ip_address,
    mark_payment_paid,
    normalize_provider_status,
    parse_provider_amount,
    sanitize_callback_payload,
    schedule_payment_notifications,
)

logger = logging.getLogger(__name__)


def _payload_value(payload, *keys):
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            if value:
                return value[0]
            continue
        if value not in (None, ''):
            return value
    return ''


def _lookup_payment(request_id, provider_entity, provider_reference):
    if request_id:
        payment = Payment.objects.filter(ifthenpay_request_id=request_id).first()
        if payment:
            return payment, 'ok'

    if not provider_reference:
        return None, 'payment not found'

    lookup = Payment.objects.filter(mb_reference=provider_reference)
    if provider_entity:
        lookup = lookup.filter(mb_entity=provider_entity)

    matches = list(lookup[:2])
    if len(matches) > 1:
        return None, 'ambiguous payment reference'
    if matches:
        return matches[0], 'ok'
    return None, 'payment not found'


@csrf_exempt
@require_GET
def ifthenpay_callback(request):
    """
    Callback endpoint for ifthenpay payment confirmations.
    ifthenpay sends a GET request with payment details when a payment is confirmed.
    """
    payload = dict(request.GET)
    ip_address = anonymize_ip_address(
        request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
    )
    sanitized_payload = sanitize_callback_payload(payload)

    anti_phishing = request.GET.get('anti_phishing_key', '')
    is_valid = anti_phishing == settings.IFTHENPAY_ANTI_PHISHING_KEY and anti_phishing != ''
    validation_message = 'ok'

    request_id = _payload_value(payload, 'request_id', 'RequestId', 'referencia', 'Reference')
    provider_reference = _payload_value(payload, 'referencia', 'Reference')
    provider_entity = _payload_value(payload, 'entidade', 'Entity')
    provider_status = normalize_provider_status(_payload_value(payload, 'status', 'Status', 'estado', 'Estado'))
    provider_amount = parse_provider_amount(_payload_value(payload, 'amount', 'Amount', 'valor', 'Valor'))

    payment = None
    payment_lookup_message = 'ok'
    if request_id or provider_reference:
        payment, payment_lookup_message = _lookup_payment(request_id, provider_entity, provider_reference)

    if not request_id and not provider_reference:
        is_valid = False
        validation_message = 'missing request identifier'
    elif not is_valid:
        validation_message = 'anti-phishing mismatch'
    elif payment is None:
        is_valid = False
        validation_message = payment_lookup_message
    elif provider_amount is None:
        is_valid = False
        validation_message = 'missing amount'
    elif provider_status and provider_status in PAYMENT_FAILURE_STATUSES:
        is_valid = False
        validation_message = f'provider reported {provider_status}'
    elif provider_amount != payment.amount:
        is_valid = False
        validation_message = 'amount mismatch'
    elif payment.method == Payment.Method.MULTIBANCO:
        if provider_reference and payment.mb_reference and provider_reference != payment.mb_reference:
            is_valid = False
            validation_message = 'reference mismatch'
        elif provider_entity and payment.mb_entity and provider_entity != payment.mb_entity:
            is_valid = False
            validation_message = 'entity mismatch'
    elif payment.status != Payment.Status.PAID and not payment.can_transition_to(Payment.Status.PAID):
        is_valid = False
        validation_message = 'payment transition blocked'

    PaymentCallback.objects.create(
        payment=payment,
        raw_payload=sanitized_payload,
        ip_address=ip_address,
        is_valid=is_valid,
        validation_message=validation_message,
    )

    if not is_valid:
        logger.warning('Invalid ifthenpay callback from %s: %s', ip_address, validation_message)
        return HttpResponse('invalid', status=400)

    assert payment is not None

    try:
        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
            if mark_payment_paid(locked_payment, source='ifthenpay_callback'):
                schedule_payment_notifications(locked_payment)
    except PaymentTransitionError:
        logger.warning('Blocked payment transition for callback on payment %s', payment.pk)
        return HttpResponse('invalid', status=409)

    return HttpResponse('ok')
