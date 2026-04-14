from types import SimpleNamespace

import pytest

from apps.cart.models import Cart
from apps.cart.services import (
    adjust_cart_items_for_stock,
    cart_allows_shipping,
    get_cart_for_request,
    get_or_create_cart_for_request,
    merge_anonymous_cart_into_user_cart,
    remove_inactive_cart_items,
)
from tests.factories.accounts import UserFactory
from tests.factories.cart import CartFactory, CartItemFactory
from tests.factories.catalog import ProductFactory


pytestmark = [pytest.mark.django_db, pytest.mark.fast]


class SessionStub:
    def __init__(self, session_key=None):
        self.session_key = session_key

    def create(self):
        self.session_key = self.session_key or 'generated-session-key'


def make_request(*, user, session=None):
    return SimpleNamespace(user=user, session=session)


def test_get_cart_for_request_returns_user_cart_for_authenticated_user():
    user = UserFactory()
    cart = CartFactory(user=user, session_key=None)
    request = make_request(user=user, session=SessionStub('ignored-session'))

    resolved_cart = get_cart_for_request(request)

    assert resolved_cart == cart


def test_get_cart_for_request_returns_none_when_no_matching_cart_exists():
    anonymous_user = SimpleNamespace(is_authenticated=False)
    request = make_request(user=anonymous_user, session=SessionStub('missing-session'))

    resolved_cart = get_cart_for_request(request)

    assert resolved_cart is None


def test_get_or_create_cart_for_request_creates_anonymous_cart_from_session():
    anonymous_user = SimpleNamespace(is_authenticated=False)
    request = make_request(user=anonymous_user, session=SessionStub())

    cart = get_or_create_cart_for_request(request)

    assert cart.session_key == 'generated-session-key'
    assert cart.user is None
    assert Cart.objects.filter(session_key='generated-session-key').exists()


def test_get_or_create_cart_for_request_returns_existing_user_cart():
    user = UserFactory()
    cart = CartFactory(user=user, session_key=None)
    request = make_request(user=user, session=SessionStub())

    resolved_cart = get_or_create_cart_for_request(request)

    assert resolved_cart == cart
    assert Cart.objects.filter(user=user).count() == 1


def test_merge_anonymous_cart_into_user_cart_moves_new_products_and_sums_existing_quantity():
    user = UserFactory()
    user_cart = CartFactory(user=user, session_key=None)
    anonymous_cart = CartFactory(session_key='merge-session')
    shared_product = ProductFactory(translation={'name': 'Produto Partilhado'})
    extra_product = ProductFactory(translation={'name': 'Produto Extra'})
    CartItemFactory(cart=user_cart, product=shared_product, quantity=1)
    CartItemFactory(cart=anonymous_cart, product=shared_product, quantity=2)
    CartItemFactory(cart=anonymous_cart, product=extra_product, quantity=3)
    request = make_request(user=user, session=SessionStub('merge-session'))

    merged_cart = merge_anonymous_cart_into_user_cart(request, user)

    assert merged_cart == user_cart
    assert not Cart.objects.filter(pk=anonymous_cart.pk).exists()
    assert merged_cart.items.get(product=shared_product).quantity == 3
    assert merged_cart.items.get(product=extra_product).quantity == 3


def test_remove_inactive_cart_items_deletes_only_inactive_products():
    cart = CartFactory()
    active_product = ProductFactory(is_active=True)
    inactive_product = ProductFactory(is_active=False)
    CartItemFactory(cart=cart, product=active_product, quantity=1)
    CartItemFactory(cart=cart, product=inactive_product, quantity=2)

    deleted_count = remove_inactive_cart_items(cart)

    assert deleted_count == 1
    assert cart.items.filter(product=active_product).count() == 1
    assert cart.items.filter(product=inactive_product).count() == 0


def test_cart_allows_shipping_returns_false_when_any_item_blocks_shipping():
    shipping_product = ProductFactory(allow_shipping=True)
    pickup_only_product = ProductFactory(allow_shipping=False)
    first_item = CartItemFactory(product=shipping_product, quantity=1)
    second_item = CartItemFactory(product=pickup_only_product, quantity=1)

    allows_shipping = cart_allows_shipping([first_item, second_item])

    assert allows_shipping is False


def test_adjust_cart_items_for_stock_caps_quantity_and_reports_shortfall():
    cart = CartFactory()
    product = ProductFactory(stock=2, translation={'name': 'Produto Ajustado'})
    cart_item = CartItemFactory(cart=cart, product=product, quantity=5)

    changed, details = adjust_cart_items_for_stock([cart_item], lang='pt')

    cart_item.refresh_from_db()

    assert changed is True
    assert details == [
        {
            'product_name': 'Produto Ajustado',
            'requested': 5,
            'available': 2,
        },
    ]
    assert cart_item.quantity == 2


def test_adjust_cart_items_for_stock_deletes_item_when_stock_reaches_zero():
    cart = CartFactory()
    product = ProductFactory(stock=0, translation={'name': 'Sem Stock'})
    cart_item = CartItemFactory(cart=cart, product=product, quantity=2)

    changed, details = adjust_cart_items_for_stock([cart_item], lang='pt')

    assert changed is True
    assert details == [
        {
            'product_name': 'Sem Stock',
            'requested': 2,
            'available': 0,
        },
    ]
    assert not cart.items.filter(pk=cart_item.pk).exists()