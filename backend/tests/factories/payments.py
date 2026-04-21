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
    provider_reference = factory.Sequence(lambda n: f'cs_test_{n}')
    provider_payment_id = factory.Sequence(lambda n: f'pi_test_{n}')
    provider_data = factory.LazyFunction(dict)
    checkout_url = factory.LazyAttribute(
        lambda obj: f'https://checkout.stripe.com/pay/{obj.provider_reference}'
        if obj.method == Payment.Method.STRIPE and obj.provider_reference
        else ''
    )
    last_error = ''
    expires_at = None
    paid_at = None