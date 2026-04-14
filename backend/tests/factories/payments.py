from decimal import Decimal

import factory

from apps.payments.models import Payment
from tests.factories.orders import OrderFactory


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    method = Payment.Method.STRIPE
    status = Payment.Status.PENDING
    amount = Decimal('19.00')
    stripe_session_id = factory.Sequence(lambda n: f'cs_test_{n}')
    stripe_payment_intent_id = factory.Sequence(lambda n: f'pi_test_{n}')
    checkout_url = factory.LazyAttribute(lambda obj: f'https://checkout.stripe.com/pay/{obj.stripe_session_id}')
    last_error = ''
    expires_at = None
    paid_at = None