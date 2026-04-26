from decimal import Decimal
from typing import Any, cast

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from playwright.sync_api import expect

from apps.catalog.models import Location
from apps.orders.models import Order
from tests.factories.cart import CartFactory, CartItemFactory
from tests.factories.catalog import ProductFactory


pytestmark = [
    pytest.mark.browser,
    pytest.mark.integration,
    pytest.mark.subdomain,
    pytest.mark.django_db(transaction=True),
]


def test_checkout_toggles_pickup_and_shipping_sections(browser_page, shop_live_server_url):
    user = cast(Any, get_user_model()._default_manager).create_user(
        email='browser-checkout@example.com',
        username='browser-checkout@example.com',
        password='testpass123',
    )
    cart = CartFactory(user=user, session_key='browser-checkout-session')
    location = Location.objects.create(
        name='Loja Braga',
        pickup_location_code=Order.PickupLocation.BRAGA,
        is_active=True,
        order=0,
    )
    product = ProductFactory(
        price=Decimal('9.50'),
        stock=10,
        is_active=True,
        allow_shipping=True,
        translation={'name': 'Cabaz Bio'},
    )
    product.available_locations.add(location)
    CartItemFactory(cart=cart, product=product, quantity=1)

    checkout_url = f'{shop_live_server_url}{reverse("orders:checkout", urlconf="config.urls_shop")}'
    browser_page.goto(checkout_url)

    browser_page.locator('input[name="username"]').fill(user.email)
    browser_page.locator('input[name="password"]').fill('testpass123')
    browser_page.get_by_role('button', name='Entrar').click()

    pickup_location = browser_page.locator('select[name="pickup_location"]')
    shipping_address = browser_page.locator('input[name="shipping_address_line1"]')
    shipping_city = browser_page.locator('input[name="shipping_city"]')
    shipping_method = browser_page.locator('input[name="fulfillment_method"][value="shipping"]')
    pickup_method = browser_page.locator('input[name="fulfillment_method"][value="pickup"]')

    expect(pickup_method).to_be_checked()
    expect(pickup_location).to_be_visible()
    expect(shipping_address).to_be_hidden()

    shipping_method.check(force=True)

    expect(shipping_method).to_be_checked()
    expect(shipping_address).to_be_visible()
    expect(shipping_city).to_be_visible()
    expect(pickup_location).to_be_hidden()