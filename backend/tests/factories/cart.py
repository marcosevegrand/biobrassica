# pyright: reportPrivateImportUsage=false, reportIncompatibleVariableOverride=false

import factory

from apps.cart.models import Cart, CartItem
from tests.factories.accounts import UserFactory
from tests.factories.catalog import ProductFactory


class CartFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cart

    user = factory.SubFactory(UserFactory)


class CartItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1