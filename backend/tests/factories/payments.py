# pyright: reportPrivateImportUsage=false, reportIncompatibleVariableOverride=false

from decimal import Decimal

import factory

from apps.payments.models import Payment
from tests.factories.orders import OrderFactory


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    method = Payment.Method.MBWAY_MANUAL
    status = Payment.Status.PENDING
    amount = Decimal('19.00')
    provider_reference = factory.Sequence(lambda n: f'manual_{n}')
    provider_payment_id = factory.Sequence(lambda n: f'manual_pid_{n}')
    provider_data = factory.LazyFunction(dict)
    checkout_url = ''
    last_error = ''
    expires_at = None
    paid_at = None