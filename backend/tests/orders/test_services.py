from decimal import Decimal

import pytest

from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from apps.orders.services import StockValidationError, cancel_unpaid_order, create_order_from_cart
from tests.factories.cart import CartFactory, CartItemFactory
from tests.factories.catalog import ProductFactory
from tests.factories.orders import OrderFactory
from tests.factories.payments import PaymentFactory


pytestmark = [pytest.mark.django_db, pytest.mark.fast]


def test_create_order_from_cart_decrements_stock_and_clears_cart():
    cart = CartFactory()
    product = ProductFactory(
        price=Decimal('9.50'),
        stock=10,
        translation={'name': 'Azeite Bio'},
    )
    CartItemFactory(cart=cart, product=product, quantity=2)

    order = create_order_from_cart(
        cart=cart,
        cart_items=list(cart.items.select_related('product')),
        user=None,
        language='pt',
        name='Marco',
        email='marco@example.com',
        phone='912345678',
        fulfillment_method=Order.FulfillmentMethod.PICKUP,
        pickup_location=Order.PickupLocation.BRAGA,
        shipping_address_line1='',
        shipping_address_line2='',
        shipping_city='',
        shipping_postal_code='',
        notes='Sem sacos',
    )

    product.refresh_from_db()

    assert order.status == Order.Status.PENDING
    assert product.stock == 8
    assert cart.items.count() == 0
    assert order.items.count() == 1

    order_item = order.items.get()
    assert order_item.product == product
    assert order_item.product_name == 'Azeite Bio'
    assert order_item.quantity == 2
    assert order_item.price == Decimal('9.50')


def test_create_order_from_cart_raises_when_stock_is_insufficient():
    cart = CartFactory()
    product = ProductFactory(stock=1, translation={'name': 'Produto Escasso'})
    cart_item = CartItemFactory(cart=cart, product=product, quantity=2)

    with pytest.raises(StockValidationError) as exc_info:
        create_order_from_cart(
            cart=cart,
            cart_items=[cart_item],
            user=None,
            language='pt',
            name='Marco',
            email='marco@example.com',
            phone='912345678',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            shipping_address_line1='',
            shipping_address_line2='',
            shipping_city='',
            shipping_postal_code='',
            notes='',
        )

    product.refresh_from_db()

    assert 'Produto Escasso' in str(exc_info.value)
    assert product.stock == 1
    assert cart.items.count() == 1
    assert Order.objects.count() == 0


def test_cancel_unpaid_order_restores_stock_and_cancels_order():
    product = ProductFactory(stock=1)
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name='Produto Teste',
        price=Decimal('9.50'),
        quantity=2,
    )
    PaymentFactory(order=order, status=Payment.Status.PENDING)

    changed = cancel_unpaid_order(order)

    product.refresh_from_db()
    order.refresh_from_db()

    assert changed is True
    assert order.status == Order.Status.CANCELLED
    assert product.stock == 3