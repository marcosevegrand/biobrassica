from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, Location, Product
from apps.core.models import ShopSettings
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment


@override_settings(ROOT_URLCONF='config.urls_admin')
class OrderAdminTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123',
        )
        self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
        self.client.force_login(self.admin_user)

        self.category = Category.objects.create(slug='mercearia-admin-orders')
        self.product = Product.objects.create(
            category=self.category,
            slug='massa-admin',
            brand='Biobrassica',
            price='4.50',
            quantity='500 g',
            stock=10,
            is_active=False,
            bio_code='PT-BIO-03',
        )

    def test_admin_can_create_manual_order_with_items_and_stock_sync(self):
        response = self.client.post(
            reverse('admin:orders_order_add'),
            {
                'status': Order.Status.PENDING,
                'user': '',
                'name': 'Cliente Backoffice',
                'email': 'cliente@example.com',
                'phone': '912 345 678',
                'language': Order.Language.PT,
                'fulfillment_method': Order.FulfillmentMethod.PICKUP,
                'pickup_location': Order.PickupLocation.BRAGA,
                'notes': 'Criada no backoffice',
                'shipping_address_line1': '',
                'shipping_address_line2': '',
                'shipping_postal_code': '',
                'shipping_city': '',
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '0',
                'items-MIN_NUM_FORMS': '0',
                'items-MAX_NUM_FORMS': '1000',
                'items-0-product': str(self.product.pk),
                'items-0-product_name': '',
                'items-0-price': '',
                'items-0-quantity': '2',
                'items-0-id': '',
                '_save': 'Guardar',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.get()
        order_item = OrderItem.objects.get(order=order)
        self.product.refresh_from_db()

        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_state, Order.PaymentState.PENDING)
        self.assertEqual(order.subtotal, self.product.price * 2)
        self.assertEqual(order.total, self.product.price * 2)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.price, self.product.price)
        self.assertEqual(self.product.stock, 8)

    def test_admin_can_edit_manual_order_items_and_recalculate_totals(self):
        order = Order.objects.create(
            name='Cliente Backoffice',
            email='cliente@example.com',
            phone='912 345 678',
            language=Order.Language.PT,
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal='4.50',
            total='4.50',
            status=Order.Status.PENDING,
            payment_state=Order.PaymentState.PENDING,
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name='massa-admin',
            price='4.50',
            quantity=1,
        )
        self.product.stock = 9
        self.product.save(update_fields=['stock'])

        response = self.client.post(
            reverse('admin:orders_order_change', args=[order.pk]),
            {
                'status': Order.Status.PENDING,
                'user': '',
                'name': order.name,
                'email': order.email,
                'phone': order.phone,
                'language': order.language,
                'fulfillment_method': order.fulfillment_method,
                'pickup_location': order.pickup_location,
                'notes': '',
                'shipping_address_line1': '',
                'shipping_address_line2': '',
                'shipping_postal_code': '',
                'shipping_city': '',
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '1',
                'items-MIN_NUM_FORMS': '0',
                'items-MAX_NUM_FORMS': '1000',
                'items-0-id': str(item.pk),
                'items-0-order': str(order.pk),
                'items-0-product': str(self.product.pk),
                'items-0-product_name': 'massa-admin',
                'items-0-price': '4.50',
                'items-0-quantity': '3',
                '_save': 'Guardar',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()
        item.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(item.quantity, 3)
        self.assertEqual(order.total, self.product.price * 3)
        self.assertEqual(self.product.stock, 7)


@override_settings(ROOT_URLCONF='config.urls_shop')
class CheckoutFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email='cliente@example.com',
            username='cliente',
            password='testpass123',
            phone='912345678',
        )
        self.client.defaults['HTTP_HOST'] = 'loja.lvh.me'
        self.client.force_login(self.user)

        settings_obj = ShopSettings.load()
        settings_obj.mbway_enabled = True
        settings_obj.mbway_number = '912345678'
        settings_obj.payment_timeout_minutes = 30
        settings_obj.save()

        self.location = Location.objects.create(name='Loja Braga', is_active=True)
        self.category = Category.objects.create(slug='mercearia-checkout-orders')
        self.product = Product.objects.create(
            category=self.category,
            slug='cabaz-checkout',
            name='Cabaz Checkout',
            brand='Biobrassica',
            bio_code='PT-BIO-03',
            description='Cabaz semanal',
            allergens='Nenhum',
            price='5.00',
            quantity='1 un',
            stock=10,
            is_active=True,
            allow_pickup=True,
            image=SimpleUploadedFile(
                'product.gif',
                b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;',
                content_type='image/gif',
            ),
        )
        self.product.pickup_locations.add(self.location)

        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_checkout_starts_payment_without_intermediate_step(self):
        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Cliente Checkout',
                'email': 'cliente@example.com',
                'phone': '912345678',
                'fulfillment_method': Order.FulfillmentMethod.PICKUP,
                'pickup_location': self.location.pickup_location_code,
                'shipping_address_line1': '',
                'shipping_address_line2': '',
                'shipping_postal_code': '',
                'shipping_city': '',
                'notes': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)

        order = Order.objects.get()
        payment = Payment.objects.get(order=order)
        self.assertTrue(response['Location'].endswith(reverse('orders:payment_status', args=[order.pk])))
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.payment_state, Order.PaymentState.PENDING)
        self.assertEqual(payment.status, Payment.Status.PENDING)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(self.cart.items.count(), 0)

    def test_timeout_cancels_payment_and_order_without_restoring_stock(self):
        order = Order.objects.create(
            user=self.user,
            name='Cliente Timeout',
            email='cliente@example.com',
            phone='912345678',
            language=Order.Language.PT,
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=self.location.pickup_location_code,
            subtotal='10.00',
            total='10.00',
            status=Order.Status.PENDING,
            payment_state=Order.PaymentState.PENDING,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name='Cabaz Checkout',
            price='5.00',
            quantity=2,
        )
        self.product.stock = 8
        self.product.save(update_fields=['stock'])
        payment = Payment.objects.create(
            order=order,
            method=Payment.Method.MBWAY_MANUAL,
            status=Payment.Status.PENDING,
            amount='10.00',
            expires_at=timezone.now() - timezone.timedelta(minutes=5),
        )

        call_command('cancel_expired_payments')

        order.refresh_from_db()
        payment.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(payment.status, Payment.Status.CANCELLED)
        self.assertEqual(order.payment_state, Order.PaymentState.CANCELLED)
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.stock, 8)
