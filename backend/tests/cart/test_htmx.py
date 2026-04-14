from decimal import Decimal

import pytest
from django.urls import reverse

from apps.cart.models import CartItem
from apps.catalog.models import Location
from tests.factories.cart import CartFactory, CartItemFactory
from tests.factories.catalog import ProductFactory


pytestmark = [pytest.mark.django_db, pytest.mark.integration, pytest.mark.htmx]


def _create_pickup_location():
    return Location.objects.create(name='Loja Braga', is_active=True, order=0)


def _build_guest_cart(*, quantity=1):
    cart = CartFactory(session_key='htmx-session')
    location = _create_pickup_location()
    product = ProductFactory(
        stock=10,
        price=Decimal('9.50'),
        translation={'name': 'Azeite Bio'},
    )
    product.available_locations.add(location)
    cart_item = CartItemFactory(cart=cart, product=product, quantity=quantity)
    return cart, product, cart_item


def test_htmx_add_to_cart_returns_oob_fragments_and_opens_popup(shop_client):
    cart, product, _cart_item = _build_guest_cart(quantity=1)
    session = shop_client.session
    session.save()
    cart.session_key = session.session_key
    cart.save(update_fields=['session_key'])

    response = shop_client.post(
        reverse('cart:add', kwargs={'product_id': product.pk}, urlconf='config.urls_shop'),
        data={'quantity': 2},
        HTTP_HX_REQUEST='true',
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert 'id="cart-count"' in content
    assert 'id="cart-popup"' in content
    assert 'id="cart-summary"' in content
    assert 'id="cart-messages"' in content

    cart_item = CartItem.objects.get(cart=cart, product=product)
    assert cart_item.quantity == 3


def test_htmx_add_to_cart_invalid_quantity_returns_400_and_targets_messages(shop_client):
    cart, product, _cart_item = _build_guest_cart(quantity=1)
    session = shop_client.session
    session.save()
    cart.session_key = session.session_key
    cart.save(update_fields=['session_key'])

    response = shop_client.post(
        reverse('cart:add', kwargs={'product_id': product.pk}, urlconf='config.urls_shop'),
        data={'quantity': 'invalid'},
        HTTP_HX_REQUEST='true',
    )

    assert response.status_code == 400
    assert response['HX-Retarget'] == '#cart-messages'
    assert response['HX-Reswap'] == 'outerHTML'
    assert 'id="cart-messages"' in response.content.decode()


def test_htmx_remove_from_non_empty_cart_returns_delete_and_summary_fragment(shop_client):
    cart, product, first_item = _build_guest_cart(quantity=1)
    second_product = ProductFactory(
        stock=10,
        price=Decimal('4.25'),
        translation={'name': 'Grao Bio'},
    )
    CartItemFactory(cart=cart, product=second_product, quantity=1)
    session = shop_client.session
    session.save()
    cart.session_key = session.session_key
    cart.save(update_fields=['session_key'])

    response = shop_client.post(
        reverse('cart:remove', kwargs={'item_id': first_item.pk}, urlconf='config.urls_shop'),
        HTTP_HX_REQUEST='true',
    )

    assert response.status_code == 200
    assert response['HX-Reswap'] == 'delete'
    assert response.headers.get('HX-Retarget') is None
    assert 'id="cart-summary"' in response.content.decode()
    assert not CartItem.objects.filter(pk=first_item.pk).exists()
    assert cart.items.count() == 1


def test_htmx_remove_last_item_returns_empty_state_and_retargets_items(shop_client):
    cart, _product, cart_item = _build_guest_cart(quantity=1)
    session = shop_client.session
    session.save()
    cart.session_key = session.session_key
    cart.save(update_fields=['session_key'])

    response = shop_client.post(
        reverse('cart:remove', kwargs={'item_id': cart_item.pk}, urlconf='config.urls_shop'),
        HTTP_HX_REQUEST='true',
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert response['HX-Retarget'] == '#cart-items'
    assert response['HX-Reswap'] == 'innerHTML'
    assert 'O seu carrinho esta vazio.' in content or 'O seu carrinho est' in content
    assert 'Finalizar encomenda' not in content
    assert not CartItem.objects.filter(pk=cart_item.pk).exists()
