from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.test import TestCase, override_settings

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment


@override_settings(ROOT_URLCONF='config.urls_shop')
class OrderCheckoutFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(slug='mercearia')
        CategoryTranslation.objects.create(
            category=self.category,
            language='pt',
            name='Mercearia',
            description='Categoria de mercearia',
        )
        self.product = Product.objects.create(
            category=self.category,
            slug='azeite-bio',
            brand='Biobrassica',
            price=Decimal('9.50'),
            quantity='750 ml',
            allow_shipping=True,
            stock=10,
            is_active=True,
            bio_code='PT-BIO-03',
        )
        ProductTranslation.objects.create(
            product=self.product,
            language='pt',
            name='Azeite bio',
            description='Azeite virgem extra biológico.',
            allergens='Sem alergénios declarados.',
            ingredients='Azeite virgem extra biológico.',
        )

    def _create_guest_cart(self):
        session = self.client.session
        session.save()

        cart = Cart.objects.create(session_key=session.session_key)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        return cart

    def test_checkout_confirm_creates_order_moves_items_and_empties_cart(self):
        cart = self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'phone': '912345678',
                'pickup_location': Order.PickupLocation.BRAGA,
                'notes': 'Sem sacos',
            },
            HTTP_HOST='loja.lvh.me',
        )

        order = Order.objects.get(email='marco@example.com')

        self.assertRedirects(
            response,
            f"{reverse('orders:payment_select', kwargs={'order_id': order.pk})}?token={order.access_token}",
            fetch_redirect_response=False,
        )
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertEqual(OrderItem.objects.get(order=order).quantity, 2)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    @patch('apps.orders.views.ifthenpay_service.create_mbway_payment')
    def test_mbway_payment_selection_creates_pending_payment(self, create_mbway_payment):
        create_mbway_payment.return_value = {
            'request_id': 'req-100',
            'transaction_id': 'tx-100',
        }
        self._create_guest_cart()
        self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
        )
        order = Order.objects.get(email='marco@example.com')

        response = self.client.post(
            reverse('orders:payment_select', kwargs={'order_id': order.pk}),
            {
                'token': str(order.access_token),
                'payment_method': Payment.Method.MBWAY,
                'mbway_phone': '912345678',
            },
            HTTP_HOST='loja.lvh.me',
        )

        payment = Payment.objects.get(order=order)
        order.refresh_from_db()
        self.assertRedirects(
            response,
            f"{reverse('orders:payment_status', kwargs={'order_id': order.pk})}?token={order.access_token}",
            fetch_redirect_response=False,
        )
        self.assertEqual(payment.method, Payment.Method.MBWAY)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.ifthenpay_request_id, 'req-100')
        self.assertEqual(payment.mbway_phone, '912345678')
        self.assertEqual(payment.mbway_transaction_id, 'tx-100')
        self.assertEqual(order.status, Order.Status.PAYMENT_PENDING)

    def test_payment_selection_rejects_non_mbway_methods(self):
        self._create_guest_cart()
        self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
        )
        order = Order.objects.get(email='marco@example.com')

        response = self.client.post(
            reverse('orders:payment_select', kwargs={'order_id': order.pk}),
            {
                'token': str(order.access_token),
                'payment_method': Payment.Method.MULTIBANCO,
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertContains(response, 'Selecione um método de pagamento válido.')
        self.assertFalse(Payment.objects.filter(order=order).exists())

    def test_guest_order_pages_require_access_token(self):
        self._create_guest_cart()
        self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
        )
        order = Order.objects.get(email='marco@example.com')

        response = self.client.get(
            reverse('orders:payment_select', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
        )

        self.assertEqual(response.status_code, 404)

    def test_checkout_confirm_supports_shipping_when_all_products_allow_it(self):
        cart = self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'fulfillment_method': Order.FulfillmentMethod.SHIPPING,
                'shipping_address_line1': 'Rua Central 100',
                'shipping_city': 'Braga',
                'shipping_postal_code': '4700-100',
            },
            HTTP_HOST='loja.lvh.me',
        )

        order = Order.objects.get(email='marco@example.com')
        self.assertRedirects(
            response,
            f"{reverse('orders:payment_select', kwargs={'order_id': order.pk})}?token={order.access_token}",
            fetch_redirect_response=False,
        )
        self.assertEqual(order.fulfillment_method, Order.FulfillmentMethod.SHIPPING)
        self.assertEqual(order.shipping_city, 'Braga')
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    def test_checkout_blocks_shipping_for_pickup_only_products(self):
        self.product.allow_shipping = False
        self.product.save(update_fields=['allow_shipping'])
        self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'fulfillment_method': Order.FulfillmentMethod.SHIPPING,
                'shipping_address_line1': 'Rua Central 100',
                'shipping_city': 'Braga',
                'shipping_postal_code': '4700-100',
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertContains(response, 'Este carrinho contém produtos disponíveis apenas para levantamento em loja.')
        self.assertFalse(Order.objects.filter(email='marco@example.com').exists())

    def test_complete_page_redirects_until_payment_is_confirmed(self):
        order = Order.objects.create(
            name='Marco',
            email='marco@example.com',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal=Decimal('19.00'),
            total=Decimal('19.00'),
            status=Order.Status.PAYMENT_PENDING,
        )
        Payment.objects.create(
            order=order,
            method=Payment.Method.MBWAY,
            status=Payment.Status.PENDING,
            amount=order.total,
            mbway_phone='912345678',
            ifthenpay_request_id='req-100',
        )

        response = self.client.get(
            reverse('orders:complete', kwargs={'order_id': order.pk}) + f'?token={order.access_token}',
            HTTP_HOST='loja.lvh.me',
        )

        self.assertRedirects(
            response,
            f"{reverse('orders:payment_status', kwargs={'order_id': order.pk})}?token={order.access_token}",
            fetch_redirect_response=False,
        )
