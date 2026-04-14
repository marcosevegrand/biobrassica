from decimal import Decimal

import pytest
from playwright.sync_api import expect

from apps.catalog.models import Location
from tests.factories.catalog import ProductFactory


pytestmark = [
    pytest.mark.browser,
    pytest.mark.integration,
    pytest.mark.subdomain,
    pytest.mark.htmx,
    pytest.mark.django_db(transaction=True),
]


def _create_pickup_ready_product(*, name: str = 'Azeite Bio'):
    location = Location.objects.create(name='Loja Braga', is_active=True, order=0)
    product = ProductFactory(
        price=Decimal('9.50'),
        stock=10,
        is_active=True,
        translation={'name': name},
    )
    product.available_locations.add(location)
    return product


def test_cart_popup_can_open_close_and_dismiss(browser_page, shop_live_server_url):
    _create_pickup_ready_product()

    browser_page.goto(f'{shop_live_server_url}/pt/produtos/')

    cart_popup = browser_page.locator('#cart-popup')
    expect(cart_popup).to_be_hidden()

    browser_page.click('#cart-trigger')
    expect(cart_popup).to_be_visible()
    expect(cart_popup).to_contain_text('O seu carrinho está vazio.')

    browser_page.click('#cart-popup-close')
    expect(cart_popup).to_be_hidden()

    browser_page.click('#cart-trigger')
    expect(cart_popup).to_be_visible()
    browser_page.get_by_role('heading', name='Produtos').click()
    expect(cart_popup).to_be_hidden()


def test_htmx_add_to_cart_keeps_popup_open_and_updates_count(browser_page, shop_live_server_url):
    _create_pickup_ready_product()

    browser_page.goto(f'{shop_live_server_url}/pt/produtos/')

    product_card = browser_page.locator('div.group', has_text='Azeite Bio')
    add_button = product_card.get_by_role('button', name='Adicionar ao carrinho')
    cart_popup = browser_page.locator('#cart-popup')
    cart_count = browser_page.locator('#cart-count')

    add_button.click()

    expect(cart_popup).to_be_visible()
    expect(cart_popup).to_contain_text('Azeite Bio')
    expect(cart_count).to_be_visible()
    expect(cart_count).to_have_text('1')

    add_button.click()

    expect(cart_popup).to_be_visible()
    expect(cart_popup).to_contain_text('2 × 9.50€')
    expect(cart_count).to_have_text('2')