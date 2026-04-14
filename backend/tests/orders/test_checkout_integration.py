from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.cart.models import CartItem
from apps.catalog.models import Location
from apps.orders.models import Order
from apps.payments.models import Payment
from tests.factories.cart import CartFactory, CartItemFactory
from tests.factories.catalog import ProductFactory


pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.stripe]


def _create_pickup_location():
    return Location.objects.create(name='Loja Braga', is_active=True, order=0)


def _build_guest_cart(*, quantity=2, stock=10):
    cart = CartFactory(session_key='checkout-session')
    location = _create_pickup_location()
    product = ProductFactory(
        stock=stock,
        price=Decimal('9.50'),
        translation={'name': 'Azeite Bio'},
    )
    product.available_locations.add(location)
    cart_item = CartItemFactory(cart=cart, product=product, quantity=quantity)
    return cart, product, cart_item


def _checkout_payload(**overrides):
    payload = {
        'name': 'Marco',
        'email': 'marco@example.com',
        'phone': '912345678',
        'fulfillment_method': Order.FulfillmentMethod.PICKUP,
        'pickup_location': Order.PickupLocation.BRAGA,
        'notes': 'Sem sacos',
    }
    payload.update(overrides)
    return payload


def test_checkout_confirm_creates_payment_pending_order_and_clears_cart(shop_client, monkeypatch):
    cart, product, _cart_item = _build_guest_cart(quantity=2, stock=10)
    session = shop_client.session
    session.save()
    cart.session_key = session.session_key
    cart.save(update_fields=['session_key'])

    def fake_create_checkout_session(**kwargs):
        assert kwargs['order'].email == 'marco@example.com'
        assert kwargs['payment'].status == Payment.Status.PENDING
        assert kwargs['success_url'].startswith('http://loja.lvh.me')
        assert kwargs['cancel_url'].startswith('http://loja.lvh.me')
        return {
            'session_id': 'cs_checkout_ok',
            'payment_intent_id': 'pi_checkout_ok',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_checkout_ok',
            'expires_at': timezone.now() + timedelta(hours=1),
        }

    monkeypatch.setattr('apps.orders.views.stripe_service.create_checkout_session', fake_create_checkout_session)

    response = shop_client.post(
        reverse('orders:confirm', urlconf='config.urls_shop'),
        data=_checkout_payload(),
    )

    order = Order.objects.get(email='marco@example.com')
    payment = Payment.objects.get(order=order)
    session = shop_client.session

    product.refresh_from_db()

    assert response.status_code == 302
    assert response['Location'] == 'https://checkout.stripe.com/pay/cs_checkout_ok'
    assert order.status == Order.Status.PAYMENT_PENDING
    assert payment.status == Payment.Status.PENDING
    assert payment.stripe_session_id == 'cs_checkout_ok'
    assert payment.stripe_payment_intent_id == 'pi_checkout_ok'
    assert payment.checkout_url == 'https://checkout.stripe.com/pay/cs_checkout_ok'
    assert order.items.count() == 1
    assert CartItem.objects.filter(cart=cart).count() == 0
    assert product.stock == 8
    assert session[f'guest_order_access:{order.pk}'] == str(order.access_token)


def test_checkout_confirm_restores_cart_and_cancels_order_when_stripe_fails(shop_client, monkeypatch):
    cart, product, cart_item = _build_guest_cart(quantity=2, stock=10)
    session = shop_client.session
    session.save()
    cart.session_key = session.session_key
    cart.save(update_fields=['session_key'])

    def fail_create_checkout_session(**_kwargs):
        raise RuntimeError('stripe unavailable')

    monkeypatch.setattr('apps.orders.views.stripe_service.create_checkout_session', fail_create_checkout_session)

    response = shop_client.post(
        reverse('orders:confirm', urlconf='config.urls_shop'),
        data=_checkout_payload(),
        follow=True,
    )

    order = Order.objects.get(email='marco@example.com')
    product.refresh_from_db()
    cart_item.refresh_from_db()

    assert response.redirect_chain[-1][0].endswith(reverse('orders:checkout', urlconf='config.urls_shop'))
    assert order.status == Order.Status.CANCELLED
    assert not Payment.objects.filter(order=order).exists()
    assert CartItem.objects.filter(cart=cart).count() == 1
    assert cart_item.quantity == 2
    assert product.stock == 10


def test_checkout_confirm_caps_cart_quantities_and_renders_error_when_stock_changed(shop_client):
    cart, product, cart_item = _build_guest_cart(quantity=5, stock=2)
    session = shop_client.session
    session.save()
    cart.session_key = session.session_key
    cart.save(update_fields=['session_key'])

    response = shop_client.post(
        reverse('orders:confirm', urlconf='config.urls_shop'),
        data=_checkout_payload(),
    )

    cart_item.refresh_from_db()

    assert response.status_code == 200
    assert Order.objects.count() == 0
    assert cart_item.quantity == 2
    assert 'Alguns produtos já não têm stock suficiente' in response.content.decode()
    assert CartItem.objects.filter(cart=cart).count() == 1
