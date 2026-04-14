from datetime import timedelta

import pytest
from django.utils import timezone

from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.services import (
    anonymize_ip_address,
    expire_stale_pending_payments,
    mark_payment_failed,
    mark_payment_paid,
    sanitize_callback_payload,
)
from tests.factories.orders import OrderFactory
from tests.factories.payments import PaymentFactory


pytestmark = [pytest.mark.django_db, pytest.mark.fast]


def test_sanitize_callback_payload_redacts_sensitive_values():
    payload = {
        'customer_email': 'marco@example.com',
        'phone': '+351 912 345 678',
        'secret_key': 'sk_test_secret',
        'metadata': {
            'api_token': 'tok_secret',
            'customer_note': 'Contact marco@example.com or +351912345678',
        },
        'tags': ['marco@example.com', '+351912345678'],
    }

    sanitized = sanitize_callback_payload(payload)

    assert sanitized['customer_email'] == 'ma***@example.com'
    assert sanitized['phone'] == '+35***78'
    assert sanitized['secret_key'] == '[redacted]'
    assert sanitized['metadata']['api_token'] == '[redacted]'
    assert sanitized['metadata']['customer_note'] == 'Contact ma***@example.com or +35***78'
    assert sanitized['tags'] == ['ma***@example.com', '+35***78']


@pytest.mark.stripe
def test_anonymize_ip_address_masks_ipv4_and_ipv6_values():
    assert anonymize_ip_address('203.0.113.42') == '203.0.113.0'
    assert anonymize_ip_address('2001:db8:abcd:0012:0000:0000:0000:0001') == '2001:db8:abcd:12::'


def test_anonymize_ip_address_returns_placeholder_for_invalid_values():
    assert anonymize_ip_address('not-an-ip') == '0.0.0.0'
    assert anonymize_ip_address('') == '0.0.0.0'


@pytest.mark.stripe
def test_mark_payment_paid_marks_payment_and_order_paid():
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    payment = PaymentFactory(order=order, status=Payment.Status.PENDING, paid_at=None)

    changed = mark_payment_paid(payment, source='unit_test')

    payment.refresh_from_db()
    order.refresh_from_db()

    assert changed is True
    assert payment.status == Payment.Status.PAID
    assert payment.paid_at is not None
    assert payment.last_error == ''
    assert order.status == Order.Status.PAID


@pytest.mark.stripe
def test_mark_payment_failed_restores_order_to_pending():
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    payment = PaymentFactory(order=order, status=Payment.Status.PENDING, last_error='')

    changed = mark_payment_failed(payment, reason='card declined')

    payment.refresh_from_db()
    order.refresh_from_db()

    assert changed is True
    assert payment.status == Payment.Status.FAILED
    assert payment.last_error == 'card declined'
    assert order.status == Order.Status.PENDING


@pytest.mark.stripe
def test_expire_stale_pending_payments_expires_single_stale_payment():
    now = timezone.now()
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    payment = PaymentFactory(
        order=order,
        status=Payment.Status.PENDING,
        expires_at=now - timedelta(minutes=5),
    )

    changed = expire_stale_pending_payments(payment=payment, now=now)

    payment.refresh_from_db()
    order.refresh_from_db()

    assert changed is True
    assert payment.status == Payment.Status.EXPIRED
    assert payment.last_error == 'payment expired'
    assert order.status == Order.Status.PENDING


@pytest.mark.stripe
def test_expire_stale_pending_payments_bulk_expires_only_overdue_payments():
    now = timezone.now()
    overdue_payment = PaymentFactory(
        order=OrderFactory(status=Order.Status.PAYMENT_PENDING),
        status=Payment.Status.PENDING,
        expires_at=now - timedelta(minutes=5),
    )
    active_payment = PaymentFactory(
        order=OrderFactory(status=Order.Status.PAYMENT_PENDING),
        status=Payment.Status.PENDING,
        expires_at=now + timedelta(minutes=5),
    )

    expired_count = expire_stale_pending_payments(now=now)

    overdue_payment.refresh_from_db()
    active_payment.refresh_from_db()

    assert expired_count == 1
    assert overdue_payment.status == Payment.Status.EXPIRED
    assert active_payment.status == Payment.Status.PENDING