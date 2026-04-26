from decimal import Decimal
from typing import Any, cast

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from apps.cart.models import CartItem
from apps.catalog.models import Location
from apps.orders.models import Order
from apps.payments.models import Payment
from tests.factories.cart import CartFactory, CartItemFactory
from tests.factories.catalog import ProductFactory


pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.ifthenpay]


def _create_pickup_location():
    return Location.objects.create(
        name='Loja Braga',
        pickup_location_code=Order.PickupLocation.BRAGA,
        is_active=True,
        order=0,
    )


def _build_guest_cart(*, quantity=2, stock=10):
    user = cast(Any, get_user_model()._default_manager).create_user(
        email=f'checkout-mbway-{quantity}-{stock}@example.com',
        username=f'checkout-mbway-{quantity}-{stock}',
        password='testpass123',
    )
    cart = CartFactory(user=user, session_key='checkout-mbway-session')
    location = _create_pickup_location()
    product = ProductFactory(
        stock=stock,
        price=Decimal('9.50'),
        translation={'name': 'Azeite Bio'},
    )
    product.available_locations.add(location)
    cart_item = CartItemFactory(cart=cart, product=product, quantity=quantity)
    return user, cart, product, cart_item


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


@override_settings(PAYMENT_PROVIDER=Payment.Method.IFTHENPAY_MBWAY, IFTHENPAY_MBWAY_KEY='mbway-test-key')
def test_checkout_confirm_creates_ifthenpay_mbway_payment_and_redirects_to_status(shop_client, monkeypatch):
    user, cart, product, _cart_item = _build_guest_cart(quantity=2, stock=10)
    shop_client.force_login(user)

    def fake_post_json(path, payload):
        assert path == '/spg/payment/mbway'
        assert payload['amount'] == '19.00'
        assert payload['orderId'].isdigit()
        assert payload['mobileNumber'] == '351#912345678'
        return {
            'Status': '000',
            'Message': 'Pending',
            'RequestId': 'mbway_request_ok',
        }

    monkeypatch.setattr('apps.payments.services.ifthenpay_mbway_service._post_json', fake_post_json)

    response = shop_client.post(
        reverse('orders:confirm', urlconf='config.urls_shop'),
        data=_checkout_payload(),
    )

    order = Order.objects.get(email='marco@example.com')
    payment = Payment.objects.get(order=order)

    product.refresh_from_db()

    assert response.status_code == 302
    assert response['Location'].endswith(
        reverse('orders:payment_status', kwargs={'order_id': order.pk}, urlconf='config.urls_shop')
    )
    assert payment.method == Payment.Method.IFTHENPAY_MBWAY
    assert payment.provider_reference == 'mbway_request_ok'
    assert payment.provider_payment_id == ''
    assert payment.checkout_url == ''
    assert payment.provider_data['mobile_number'] == '351#912345678'
    assert order.status == Order.Status.PAYMENT_PENDING
    assert CartItem.objects.filter(cart=cart).count() == 0
    assert product.stock == 8


@override_settings(PAYMENT_PROVIDER=Payment.Method.IFTHENPAY_MBWAY)
def test_checkout_confirm_requires_phone_for_ifthenpay_mbway(shop_client):
    user, cart, product, cart_item = _build_guest_cart(quantity=2, stock=10)
    shop_client.force_login(user)

    response = shop_client.post(
        reverse('orders:confirm', urlconf='config.urls_shop'),
        data=_checkout_payload(phone=''),
    )

    cart_item.refresh_from_db()
    product.refresh_from_db()

    assert response.status_code == 200
    assert 'Indique um telemóvel para receber o pedido MB WAY.' in response.content.decode()
    assert Order.objects.count() == 0
    assert CartItem.objects.filter(cart=cart).count() == 1
    assert product.stock == 10


@override_settings(PAYMENT_PROVIDER=Payment.Method.IFTHENPAY_MBWAY)
def test_checkout_renders_phone_as_required_for_ifthenpay_mbway(shop_client):
    user, cart, product, cart_item = _build_guest_cart(quantity=1, stock=10)
    shop_client.force_login(user)

    response = shop_client.get(reverse('orders:checkout', urlconf='config.urls_shop'))

    assert response.status_code == 200
    assert 'name="phone" required' in response.content.decode()