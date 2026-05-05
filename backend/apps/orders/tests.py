from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Category, Product
from apps.orders.models import Order, OrderItem


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
                'payment_state': Order.PaymentState.PENDING,
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
                'payment_state': Order.PaymentState.PENDING,
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
