import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import stripe

from apps.payments.models import Payment, PaymentCallback
from apps.payments.services import (
    finalize_successful_payment,
    PaymentTransitionError,
    anonymize_ip_address,
    build_ifthenpay_order_reference,
    expire_pending_payment,
    ifthenpay_mbway_service,
    mark_payment_failed,
    mark_payment_refunded,
    sanitize_callback_payload,
    stripe_service,
)

logger = logging.getLogger(__name__)


def _sanitize_stripe_event(event):
    data = event.get('data', {}).get('object', {})
    return sanitize_callback_payload({
        'id': event.get('id', ''),
        'type': event.get('type', ''),
        'customer_email': data.get('customer_details', {}).get('email', ''),
        'payment_intent': data.get('payment_intent', ''),
        'checkout_session_id': data.get('id', ''),
        'metadata': data.get('metadata', {}),
    })


def _lookup_stripe_payment(event_type, event_object):
    session_id = ''
    payment_intent_id = ''

    if event_type.startswith('checkout.session.'):
        session_id = event_object.get('id', '')
        payment_intent_id = event_object.get('payment_intent', '') or ''
    else:
        payment_intent_id = event_object.get('id', '') or event_object.get('payment_intent', '') or ''

    payment = None
    if session_id:
        payment = Payment.objects.filter(method=Payment.Method.STRIPE, provider_reference=session_id).first()
    if payment is None and payment_intent_id:
        payment = Payment.objects.filter(method=Payment.Method.STRIPE, provider_payment_id=payment_intent_id).first()
    return payment, session_id, payment_intent_id


@csrf_exempt
@require_POST
def stripe_callback(request):
    payload = request.body
    signature = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    ip_address = anonymize_ip_address(
        request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
    )

    try:
        event = stripe_service.construct_webhook_event(payload, signature)
    except (ValueError, stripe.error.SignatureVerificationError):
        PaymentCallback.objects.create(
            payment=None,
            raw_payload={'type': 'invalid', 'reason': 'signature verification failed'},
            provider_event_id='',
            ip_address=ip_address,
            is_valid=False,
            validation_message='invalid stripe signature',
        )
        return HttpResponse('invalid', status=400)

    event_type = event['type']
    event_id = event['id']
    event_object = event['data']['object']

    payment, session_id, payment_intent_id = _lookup_stripe_payment(event_type, event_object)
    sanitized_payload = _sanitize_stripe_event(event)

    try:
        _, created = PaymentCallback.objects.get_or_create(
            provider_event_id=event_id,
            defaults={
                'payment': payment,
                'raw_payload': sanitized_payload,
                'ip_address': ip_address,
                'is_valid': payment is not None,
                'validation_message': 'ok' if payment is not None else 'payment not found',
            },
        )
    except IntegrityError:
        return HttpResponse('ok')

    if not created:
        return HttpResponse('ok')

    if payment is None:
        logger.warning('Stripe webhook %s could not match a payment', event_id)
        return HttpResponse('ok')

    try:
        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
            updated_fields = []
            if session_id and locked_payment.provider_reference != session_id:
                locked_payment.provider_reference = session_id
                updated_fields.append('provider_reference')
            if payment_intent_id and locked_payment.provider_payment_id != payment_intent_id:
                locked_payment.provider_payment_id = payment_intent_id
                updated_fields.append('provider_payment_id')
            if updated_fields:
                locked_payment.save(update_fields=updated_fields)

            if event_type in {'checkout.session.completed', 'checkout.session.async_payment_succeeded'}:
                finalize_successful_payment(locked_payment, source='stripe_webhook')
            elif event_type == 'checkout.session.expired':
                expire_pending_payment(locked_payment, reason='stripe checkout expired')
            elif event_type in {'payment_intent.payment_failed', 'checkout.session.async_payment_failed'}:
                mark_payment_failed(locked_payment, reason='stripe payment failed')
            elif event_type == 'charge.refunded' and locked_payment.status in {Payment.Status.PAID, Payment.Status.REFUNDED}:
                mark_payment_refunded(locked_payment)
    except PaymentTransitionError:
        logger.warning('Blocked Stripe payment transition for payment %s', payment.pk)
        return HttpResponse('invalid', status=409)

    return HttpResponse('ok')


@require_GET
def ifthenpay_mbway_callback(request):
    payload = request.GET
    request_id = payload.get('requestId', '').strip()
    order_reference = payload.get('orderId', '').strip()
    callback_amount = payload.get('amount', '').strip()
    anti_phishing_key = payload.get('key', '').strip()
    payment_datetime = payload.get('payment_datetime', '').strip()
    provider_event_id = request_id or f'mbway:{order_reference}:{callback_amount}:{payment_datetime}'
    ip_address = anonymize_ip_address(
        request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')),
    )

    payment = None
    if request_id:
        payment = Payment.objects.filter(
            method=Payment.Method.IFTHENPAY_MBWAY,
            provider_reference=request_id,
        ).select_related('order').first()

    is_valid = True
    validation_message = 'ok'

    if anti_phishing_key != settings.IFTHENPAY_ANTI_PHISHING_KEY:
        is_valid = False
        validation_message = 'invalid ifthenpay anti-phishing key'
    elif payment is None:
        is_valid = False
        validation_message = 'payment not found'
    else:
        expected_order_reference = build_ifthenpay_order_reference(payment.order)
        if order_reference != expected_order_reference:
            is_valid = False
            validation_message = 'order reference mismatch'
        else:
            try:
                parsed_amount = Decimal(callback_amount)
            except (InvalidOperation, TypeError):
                is_valid = False
                validation_message = 'amount mismatch'
            else:
                if parsed_amount.quantize(Decimal('0.01')) != payment.amount.quantize(Decimal('0.01')):
                    is_valid = False
                    validation_message = 'amount mismatch'

    sanitized_payload = sanitize_callback_payload(dict(payload))

    try:
        _, created = PaymentCallback.objects.get_or_create(
            provider_event_id=provider_event_id,
            defaults={
                'payment': payment,
                'raw_payload': sanitized_payload,
                'ip_address': ip_address,
                'is_valid': is_valid,
                'validation_message': validation_message,
            },
        )
    except IntegrityError:
        return HttpResponse('ok')

    if not created or not is_valid or payment is None:
        return HttpResponse('ok')

    try:
        with transaction.atomic():
            locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
            provider_data = dict(locked_payment.provider_data or {})
            if payment_datetime:
                provider_data['payment_datetime'] = payment_datetime
                locked_payment.provider_data = provider_data
                locked_payment.save(update_fields=['provider_data'])
            finalize_successful_payment(locked_payment, source='ifthenpay_mbway_callback')
    except PaymentTransitionError:
        logger.warning('Blocked Ifthenpay MB WAY payment transition for payment %s', payment.pk)

    return HttpResponse('ok')
