import pytest
from django.test import override_settings
from django.urls import reverse

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentCallback
from tests.factories.orders import OrderFactory
from tests.factories.payments import PaymentFactory


pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.ifthenpay]


@override_settings(
    PAYMENT_PROVIDER=Payment.Method.IFTHENPAY_MBWAY,
    IFTHENPAY_ANTI_PHISHING_KEY='anti-phishing-key',
)
def test_ifthenpay_mbway_callback_marks_payment_paid_and_records_callback(shop_client, monkeypatch):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING, email='marco@example.com')
    payment = PaymentFactory(
        order=order,
        method=Payment.Method.IFTHENPAY_MBWAY,
        provider_reference='mbway_request_ok',
        provider_payment_id='',
        provider_data={'order_reference': str(order.pk), 'mobile_number': '351#912345678'},
        checkout_url='',
    )
    scheduled = []

    monkeypatch.setattr('apps.payments.services.schedule_payment_notifications', lambda payment: scheduled.append(payment.pk))

    response = shop_client.get(
        reverse('ifthenpay_mbway_callback', urlconf='config.urls_shop'),
        data={
            'key': 'anti-phishing-key',
            'orderId': str(order.pk),
            'amount': '19.00',
            'requestId': 'mbway_request_ok',
            'payment_datetime': '03-01-2024 15:15:16',
        },
        HTTP_X_FORWARDED_FOR='203.0.113.42',
    )

    payment.refresh_from_db()
    order.refresh_from_db()
    callback = PaymentCallback.objects.get(provider_event_id='mbway_request_ok')

    assert response.status_code == 200
    assert payment.status == Payment.Status.PAID
    assert order.status == Order.Status.PAID
    assert payment.provider_data['payment_datetime'] == '2024-01-03 15:15:16'
    assert callback.payment == payment
    assert callback.is_valid is True
    assert callback.ip_address == '203.0.113.0'
    assert scheduled == [payment.pk]


@override_settings(
    PAYMENT_PROVIDER=Payment.Method.IFTHENPAY_MBWAY,
    IFTHENPAY_ANTI_PHISHING_KEY='anti-phishing-key',
)
def test_ifthenpay_mbway_callback_invalid_key_returns_200_and_records_invalid_callback(shop_client):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    payment = PaymentFactory(
        order=order,
        method=Payment.Method.IFTHENPAY_MBWAY,
        provider_reference='mbway_request_bad_key',
        provider_payment_id='',
        provider_data={'order_reference': str(order.pk), 'mobile_number': '351#912345678'},
        checkout_url='',
    )

    response = shop_client.get(
        reverse('ifthenpay_mbway_callback', urlconf='config.urls_shop'),
        data={
            'key': 'wrong-key',
            'orderId': str(order.pk),
            'amount': '19.00',
            'requestId': 'mbway_request_bad_key',
        },
    )

    payment.refresh_from_db()
    callback = PaymentCallback.objects.get(provider_event_id='mbway_request_bad_key')

    assert response.status_code == 200
    assert payment.status == Payment.Status.PENDING
    assert callback.is_valid is False
    assert callback.validation_message == 'invalid ifthenpay anti-phishing key'


@override_settings(
    PAYMENT_PROVIDER=Payment.Method.IFTHENPAY_MBWAY,
    IFTHENPAY_ANTI_PHISHING_KEY='anti-phishing-key',
)
def test_ifthenpay_mbway_callback_missing_request_id_is_recorded_as_invalid(shop_client):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    payment = PaymentFactory(
        order=order,
        method=Payment.Method.IFTHENPAY_MBWAY,
        provider_reference='mbway_request_missing_id',
        provider_payment_id='',
        provider_data={'order_reference': str(order.pk), 'mobile_number': '351#912345678'},
        checkout_url='',
    )

    response = shop_client.get(
        reverse('ifthenpay_mbway_callback', urlconf='config.urls_shop'),
        data={
            'key': 'anti-phishing-key',
            'orderId': str(order.pk),
            'amount': '19.00',
            'payment_datetime': '03-01-2024 15:15:16',
        },
    )

    payment.refresh_from_db()
    callback = PaymentCallback.objects.get(validation_message='missing requestId')

    assert response.status_code == 200
    assert payment.status == Payment.Status.PENDING
    assert callback.payment is None
    assert callback.provider_event_id.startswith('mbway:missing-request-id:')
    assert callback.is_valid is False
    assert callback.validation_message == 'missing requestId'

    second_response = shop_client.get(
        reverse('ifthenpay_mbway_callback', urlconf='config.urls_shop'),
        data={
            'key': 'anti-phishing-key',
            'orderId': str(order.pk),
            'amount': '19.00',
            'payment_datetime': '03-01-2024 15:15:16',
        },
    )

    assert second_response.status_code == 200
    assert PaymentCallback.objects.filter(provider_event_id=callback.provider_event_id).count() == 1


@override_settings(
    PAYMENT_PROVIDER=Payment.Method.IFTHENPAY_MBWAY,
    IFTHENPAY_ANTI_PHISHING_KEY='anti-phishing-key',
)
def test_ifthenpay_mbway_callback_amount_mismatch_returns_200_and_records_invalid_callback(shop_client):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    payment = PaymentFactory(
        order=order,
        method=Payment.Method.IFTHENPAY_MBWAY,
        provider_reference='mbway_request_bad_amount',
        provider_payment_id='',
        provider_data={'order_reference': str(order.pk), 'mobile_number': '351#912345678'},
        checkout_url='',
    )

    response = shop_client.get(
        reverse('ifthenpay_mbway_callback', urlconf='config.urls_shop'),
        data={
            'key': 'anti-phishing-key',
            'orderId': str(order.pk),
            'amount': '20.00',
            'requestId': 'mbway_request_bad_amount',
        },
    )

    payment.refresh_from_db()
    callback = PaymentCallback.objects.get(provider_event_id='mbway_request_bad_amount')

    assert response.status_code == 200
    assert payment.status == Payment.Status.PENDING
    assert callback.payment == payment
    assert callback.is_valid is False
    assert callback.validation_message == 'amount mismatch'


@override_settings(
    PAYMENT_PROVIDER=Payment.Method.IFTHENPAY_MBWAY,
    IFTHENPAY_ANTI_PHISHING_KEY='anti-phishing-key',
)
def test_ifthenpay_mbway_callback_invalid_payment_datetime_returns_200_and_records_invalid_callback(shop_client):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    payment = PaymentFactory(
        order=order,
        method=Payment.Method.IFTHENPAY_MBWAY,
        provider_reference='mbway_request_bad_datetime',
        provider_payment_id='',
        provider_data={'order_reference': str(order.pk), 'mobile_number': '351#912345678'},
        checkout_url='',
    )

    response = shop_client.get(
        reverse('ifthenpay_mbway_callback', urlconf='config.urls_shop'),
        data={
            'key': 'anti-phishing-key',
            'orderId': str(order.pk),
            'amount': '19.00',
            'requestId': 'mbway_request_bad_datetime',
            'payment_datetime': '2024/01/03 15:15:16',
        },
    )

    payment.refresh_from_db()
    callback = PaymentCallback.objects.get(provider_event_id='mbway_request_bad_datetime')

    assert response.status_code == 200
    assert payment.status == Payment.Status.PENDING
    assert callback.payment == payment
    assert callback.is_valid is False
    assert callback.validation_message == 'invalid payment_datetime'