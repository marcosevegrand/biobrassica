from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.orders.models import Order
from apps.payments.models import Payment


@override_settings(ROOT_URLCONF='config.urls_admin')
class PaymentAdminTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123',
        )
        self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
        self.client.force_login(self.admin_user)

    def test_admin_can_create_manual_confirmed_payment_without_changing_order_status(self):
        order = Order.objects.create(
            name='Cliente Pagamento',
            email='cliente@example.com',
            phone='912 345 678',
            language=Order.Language.PT,
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal='12.00',
            total='12.00',
            status=Order.Status.PENDING,
        )

        response = self.client.post(
            reverse('admin:payments_payment_add'),
            {
                'order': str(order.pk),
                'method': Payment.Method.MBWAY_MANUAL,
                'status': Payment.Status.CONFIRMED,
                'amount': '12.00',
                'provider_reference': 'REF-123',
                'provider_payment_id': 'PAY-123',
                'checkout_url': '',
                'expires_at': '',
                'provider_data': '{}',
                'last_error': '',
                'paid_at': '',
                '_save': 'Guardar',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)

        payment = Payment.objects.get()
        order.refresh_from_db()

        self.assertEqual(payment.status, Payment.Status.CONFIRMED)
        self.assertEqual(order.payment_state, Order.PaymentState.CONFIRMED)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertIsNotNone(payment.paid_at)

    def test_admin_can_reopen_cancelled_payment_and_reset_order_payment_state(self):
        order = Order.objects.create(
            name='Cliente Pagamento',
            email='cliente@example.com',
            phone='912 345 678',
            language=Order.Language.PT,
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal='12.00',
            total='12.00',
            status=Order.Status.PENDING,
            payment_state=Order.PaymentState.PENDING,
        )
        payment = Payment.objects.create(
            order=order,
            method=Payment.Method.MBWAY_MANUAL,
            status=Payment.Status.CANCELLED,
            amount='12.00',
            last_error='Cancelado',
        )

        response = self.client.get(
            reverse('admin:payments_payment_status', args=[payment.pk, Payment.Status.PENDING]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        payment.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.last_error, '')
        self.assertEqual(order.payment_state, Order.PaymentState.PENDING)

    def test_admin_can_cancel_pending_payment_without_cancelling_order(self):
        order = Order.objects.create(
            name='Cliente Pagamento',
            email='cliente@example.com',
            phone='912 345 678',
            language=Order.Language.PT,
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal='12.00',
            total='12.00',
            status=Order.Status.PENDING,
            payment_state=Order.PaymentState.PENDING,
        )
        payment = Payment.objects.create(
            order=order,
            method=Payment.Method.MBWAY_MANUAL,
            status=Payment.Status.PENDING,
            amount='12.00',
        )

        response = self.client.get(
            reverse('admin:payments_payment_status', args=[payment.pk, Payment.Status.CANCELLED]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        payment.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(payment.status, Payment.Status.CANCELLED)
        self.assertEqual(order.payment_state, Order.PaymentState.CANCELLED)
        self.assertEqual(order.status, Order.Status.PENDING)
