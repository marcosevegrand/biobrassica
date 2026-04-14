from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
import stripe

from apps.orders.models import Order, OrderItem
from apps.payments.services import stripe_service
from tests.factories.catalog import ProductFactory
from tests.factories.orders import OrderFactory
from tests.factories.payments import PaymentFactory


pytestmark = [pytest.mark.django_db, pytest.mark.contract, pytest.mark.stripe]


def test_create_checkout_session_sends_expected_payload_for_single_item(monkeypatch):
    order = OrderFactory(
        status=Order.Status.PAYMENT_PENDING,
        subtotal=Decimal('19.00'),
        total=Decimal('19.00'),
        email='marco@example.com',
    )
    product = ProductFactory(price=Decimal('19.00'), translation={'name': 'Azeite Bio'})
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name='Azeite Bio',
        price=Decimal('19.00'),
        quantity=1,
    )
    payment = PaymentFactory(order=order)
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            id='cs_test_contract',
            payment_intent='pi_test_contract',
            url='https://checkout.stripe.com/pay/cs_test_contract',
            expires_at=1_700_000_000,
        )

    monkeypatch.setattr(stripe.checkout.Session, 'create', fake_create)

    result = stripe_service.create_checkout_session(
        order=order,
        payment=payment,
        success_url='https://loja.lvh.me/success',
        cancel_url='https://loja.lvh.me/cancel',
    )

    assert captured['mode'] == 'payment'
    assert captured['customer_email'] == 'marco@example.com'
    assert captured['payment_method_types'] == ['card', 'mb_way']
    assert captured['metadata'] == {
        'order_id': str(order.pk),
        'payment_id': str(payment.pk),
    }
    assert captured['line_items'] == [
        {
            'quantity': 1,
            'price_data': {
                'currency': 'eur',
                'unit_amount': 1900,
                'product_data': {
                    'name': f'Azeite Bio (Encomenda #{order.pk:07d})',
                },
            },
        },
    ]
    assert result == {
        'session_id': 'cs_test_contract',
        'payment_intent_id': 'pi_test_contract',
        'checkout_url': 'https://checkout.stripe.com/pay/cs_test_contract',
        'expires_at': datetime.fromtimestamp(1_700_000_000, tz=timezone.utc),
    }


def test_create_checkout_session_adds_summary_line_for_multiple_items(monkeypatch):
    order = OrderFactory(status=Order.Status.PAYMENT_PENDING)
    first_product = ProductFactory(price=Decimal('4.00'), translation={'name': 'Produto Um'})
    second_product = ProductFactory(price=Decimal('5.00'), translation={'name': 'Produto Dois'})
    OrderItem.objects.create(
        order=order,
        product=first_product,
        product_name='Produto Um',
        price=Decimal('4.00'),
        quantity=1,
    )
    OrderItem.objects.create(
        order=order,
        product=second_product,
        product_name='Produto Dois',
        price=Decimal('5.00'),
        quantity=2,
    )
    payment = PaymentFactory(order=order)
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            id='cs_test_multi',
            payment_intent='',
            url='https://checkout.stripe.com/pay/cs_test_multi',
            expires_at=None,
        )

    monkeypatch.setattr(stripe.checkout.Session, 'create', fake_create)

    result = stripe_service.create_checkout_session(
        order=order,
        payment=payment,
        success_url='https://loja.lvh.me/success',
        cancel_url='https://loja.lvh.me/cancel',
    )

    assert len(captured['line_items']) == 3
    assert captured['line_items'][-1] == {
        'quantity': 1,
        'price_data': {
            'currency': 'eur',
            'unit_amount': 0,
            'product_data': {
                'name': f'Encomenda #{order.pk:07d}',
            },
        },
    }
    assert result['payment_intent_id'] == ''
    assert result['expires_at'] is None