import pytest
from django.urls import reverse

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentCallback
from tests.factories.orders import OrderFactory
from tests.factories.payments import PaymentFactory


pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.stripe]


def test_stripe_completed_webhook_marks_payment_paid_and_stores_sanitized_callback(shop_client, monkeypatch):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING, email='marco@example.com')
    payment = PaymentFactory(
        order=order,
        status=Payment.Status.PENDING,
        stripe_session_id='cs_webhook_ok',
        stripe_payment_intent_id='pi_webhook_ok',
    )
    scheduled = []

    monkeypatch.setattr(
        'apps.payments.views.stripe_service.construct_webhook_event',
        lambda payload, signature: {
            'id': 'evt_webhook_paid',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_webhook_ok',
                    'payment_intent': 'pi_webhook_ok',
                    'customer_details': {'email': 'marco@example.com'},
                    'metadata': {
                        'api_token': 'tok_secret',
                        'customer_note': 'contact marco@example.com',
                    },
                },
            },
        },
    )
    monkeypatch.setattr('apps.payments.views.schedule_payment_notifications', lambda payment: scheduled.append(payment.pk))

    response = shop_client.post(
        reverse('stripe_callback', urlconf='config.urls_shop'),
        data='{}',
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE='test-signature',
        HTTP_X_FORWARDED_FOR='203.0.113.42',
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    callback = PaymentCallback.objects.get(provider_event_id='evt_webhook_paid')

    assert response.status_code == 200
    assert payment.status == Payment.Status.PAID
    assert order.status == Order.Status.PAID
    assert callback.payment == payment
    assert callback.is_valid is True
    assert callback.ip_address == '203.0.113.0'
    assert callback.raw_payload['customer_email'] == 'ma***@example.com'
    assert callback.raw_payload['metadata']['api_token'] == '[redacted]'
    assert callback.raw_payload['metadata']['customer_note'] == 'contact ma***@example.com'
    assert scheduled == [payment.pk]


def test_invalid_stripe_signature_returns_400_and_records_invalid_callback(shop_client, monkeypatch):
    monkeypatch.setattr(
        'apps.payments.views.stripe_service.construct_webhook_event',
        lambda payload, signature: (_ for _ in ()).throw(ValueError('invalid signature')),
    )

    response = shop_client.post(
        reverse('stripe_callback', urlconf='config.urls_shop'),
        data='{}',
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE='invalid-signature',
        HTTP_X_FORWARDED_FOR='203.0.113.42',
    )

    callback = PaymentCallback.objects.get(payment=None)

    assert response.status_code == 400
    assert callback.is_valid is False
    assert callback.validation_message == 'invalid stripe signature'
    assert callback.ip_address == '203.0.113.0'


def test_stripe_expired_webhook_expires_payment_and_reverts_order(shop_client, monkeypatch):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    payment = PaymentFactory(
        order=order,
        status=Payment.Status.PENDING,
        stripe_session_id='cs_webhook_expired',
        stripe_payment_intent_id='pi_webhook_expired',
    )

    monkeypatch.setattr(
        'apps.payments.views.stripe_service.construct_webhook_event',
        lambda payload, signature: {
            'id': 'evt_webhook_expired',
            'type': 'checkout.session.expired',
            'data': {
                'object': {
                    'id': 'cs_webhook_expired',
                    'payment_intent': 'pi_webhook_expired',
                    'metadata': {},
                },
            },
        },
    )

    response = shop_client.post(
        reverse('stripe_callback', urlconf='config.urls_shop'),
        data='{}',
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE='test-signature',
    )

    payment.refresh_from_db()
    order.refresh_from_db()

    assert response.status_code == 200
    assert payment.status == Payment.Status.EXPIRED
    assert payment.last_error == 'stripe checkout expired'
    assert order.status == Order.Status.PENDING


def test_unknown_stripe_payment_is_recorded_without_failing_delivery(shop_client, monkeypatch):
    monkeypatch.setattr(
        'apps.payments.views.stripe_service.construct_webhook_event',
        lambda payload, signature: {
            'id': 'evt_unknown_payment',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_unknown',
                    'payment_intent': 'pi_unknown',
                    'customer_details': {'email': 'unknown@example.com'},
                    'metadata': {},
                },
            },
        },
    )

    response = shop_client.post(
        reverse('stripe_callback', urlconf='config.urls_shop'),
        data='{}',
        content_type='application/json',
        HTTP_STRIPE_SIGNATURE='test-signature',
    )

    callback = PaymentCallback.objects.get(provider_event_id='evt_unknown_payment')

    assert response.status_code == 200
    assert callback.payment is None
    assert callback.is_valid is False
    assert callback.validation_message == 'payment not found'