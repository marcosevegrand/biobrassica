# pyright: reportPrivateImportUsage=false, reportIncompatibleVariableOverride=false

from decimal import Decimal

import factory

from apps.orders.models import Order
from tests.factories.accounts import UserFactory


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = None
    name = factory.Sequence(lambda n: f'Cliente {n}')
    email = factory.Sequence(lambda n: f'cliente{n}@example.com')
    phone = '912345678'
    status = Order.Status.PENDING
    payment_state = Order.PaymentState.PENDING
    fulfillment_method = Order.FulfillmentMethod.PICKUP
    pickup_location = Order.PickupLocation.BRAGA
    shipping_address_line1 = ''
    shipping_address_line2 = ''
    shipping_city = ''
    shipping_postal_code = ''
    language = 'pt'
    subtotal = Decimal('19.00')
    total = Decimal('19.00')
    notes = ''


class UserOrderFactory(OrderFactory):
    user = factory.SubFactory(UserFactory)