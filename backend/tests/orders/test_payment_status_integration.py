from types import SimpleNamespace

import pytest
from django.urls import reverse

from apps.orders.models import Order
from apps.payments.models import Payment
from tests.factories.orders import OrderFactory
from tests.factories.payments import PaymentFactory


pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.stripe]


def _grant_guest_access(client, order):
    session = client.session
    session.save()
    session[f'guest_order_access:{order.pk}'] = str(order.access_token)
    session.save()


def _create_guest_order_with_payment():
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING, user=None)
    payment = PaymentFactory(
        order=order,
        status=Payment.Status.PENDING,
        stripe_session_id='cs_test_pending',
        stripe_payment_intent_id='pi_test_pending',
        checkout_url='https://checkout.stripe.com/pay/cs_test_pending',
    )
    return order, payment


def test_payment_status_polling_paid_session_marks_payment_paid_and_redirects_to_complete(shop_client, monkeypatch):
    order, payment = _create_guest_order_with_payment()
    _grant_guest_access(shop_client, order)
    scheduled = []

    monkeypatch.setattr(
        'apps.orders.views.stripe_service.retrieve_checkout_session',
        lambda session_id: SimpleNamespace(payment_status='paid', status='complete'),
    )
    monkeypatch.setattr('apps.payments.services.schedule_payment_notifications', lambda payment: scheduled.append(payment.pk))

    response = shop_client.get(
        reverse('orders:payment_status', kwargs={'order_id': order.pk}, urlconf='config.urls_shop'),
    )

    payment.refresh_from_db()
    order.refresh_from_db()

    assert response.status_code == 302
    assert response['Location'].endswith(
        reverse('orders:complete', kwargs={'order_id': order.pk}, urlconf='config.urls_shop')
    )
    assert payment.status == Payment.Status.PAID
    assert order.status == Order.Status.PAID
    assert scheduled == [payment.pk]


def test_payment_status_polling_expired_session_marks_payment_expired_and_renders_status_page(shop_client, monkeypatch):
    order, payment = _create_guest_order_with_payment()
    _grant_guest_access(shop_client, order)

    monkeypatch.setattr(
        'apps.orders.views.stripe_service.retrieve_checkout_session',
        lambda session_id: SimpleNamespace(payment_status='', status='expired'),
    )

    response = shop_client.get(
        reverse('orders:payment_status', kwargs={'order_id': order.pk}, urlconf='config.urls_shop'),
    )

    payment.refresh_from_db()
    order.refresh_from_db()

    assert response.status_code == 200
    assert payment.status == Payment.Status.EXPIRED
    assert order.status == Order.Status.PENDING
    assert payment.last_error == 'stripe checkout expired (poll)'
    assert payment.last_error in response.content.decode()


def test_payment_status_missing_payment_redirects_to_payment_select(shop_client):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING, user=None)
    _grant_guest_access(shop_client, order)

    response = shop_client.get(
        reverse('orders:payment_status', kwargs={'order_id': order.pk}, urlconf='config.urls_shop'),
    )

    assert response.status_code == 302
    assert response['Location'].endswith(
        reverse('orders:payment_select', kwargs={'order_id': order.pk}, urlconf='config.urls_shop')
    )


def test_payment_status_polling_exception_leaves_payment_pending_and_renders_page(shop_client, monkeypatch):
    order, payment = _create_guest_order_with_payment()
    _grant_guest_access(shop_client, order)

    def raise_error(session_id):
        raise RuntimeError('Stripe API unavailable')

    monkeypatch.setattr('apps.orders.views.stripe_service.retrieve_checkout_session', raise_error)

    response = shop_client.get(
        reverse('orders:payment_status', kwargs={'order_id': order.pk}, urlconf='config.urls_shop'),
    )

    payment.refresh_from_db()
    order.refresh_from_db()

    assert response.status_code == 200
    assert payment.status == Payment.Status.PENDING
    assert order.status == Order.Status.PAYMENT_PENDING
    assert 'Estado do Pagamento' in response.content.decode()
