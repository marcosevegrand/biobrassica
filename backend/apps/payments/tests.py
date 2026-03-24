from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Any, cast

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentCallback
from apps.payments.services import PaymentTransitionError, mark_payment_failed


@override_settings(
    ROOT_URLCONF='config.urls_shop',
    IFTHENPAY_ANTI_PHISHING_KEY='secret-callback-key',
    DEFAULT_FROM_EMAIL='loja@biobrassica.pt',
    STAFF_NOTIFICATION_EMAILS=['ops@biobrassica.pt'],
)
class PaymentCallbackTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(
            name='Marco',
            email='marco@example.com',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal=Decimal('19.00'),
            total=Decimal('19.00'),
            status=Order.Status.PAYMENT_PENDING,
        )
        self.payment = Payment.objects.create(
            order=self.order,
            method=Payment.Method.MULTIBANCO,
            status=Payment.Status.PENDING,
            amount=self.order.total,
            ifthenpay_request_id='req-100',
            mb_entity='12345',
            mb_reference='543210987',
        )

    @patch('apps.payments.services.send_mail')
    def test_valid_callback_marks_order_paid_and_sends_notifications(self, send_mail):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(
                reverse('ifthenpay_callback'),
                {
                    'anti_phishing_key': 'secret-callback-key',
                    'request_id': 'req-100',
                    'entidade': '12345',
                    'referencia': '543210987',
                    'valor': '19.00',
                },
                HTTP_HOST='loja.lvh.me',
            )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(send_mail.call_count, 2)
        self.assertTrue(PaymentCallback.objects.get(payment=self.payment).is_valid)

    def test_invalid_payment_transition_blocked(self):
        self.payment.status = Payment.Status.PAID
        self.payment.paid_at = timezone.now()
        self.payment.save(update_fields=['status', 'paid_at'])

        with self.assertRaises(PaymentTransitionError):
            mark_payment_failed(self.payment, reason='late failure')

    def test_callback_rejects_missing_amount(self):
        response = self.client.get(
            reverse('ifthenpay_callback'),
            {
                'anti_phishing_key': 'secret-callback-key',
                'request_id': 'req-100',
                'entidade': '12345',
                'referencia': '543210987',
            },
            HTTP_HOST='loja.lvh.me',
        )

        callback = PaymentCallback.objects.get(payment=self.payment)
        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(callback.is_valid)
        self.assertEqual(callback.validation_message, 'missing amount')
        self.assertEqual(self.payment.status, Payment.Status.PENDING)

    def test_callback_payload_and_ip_are_stored_sanitized(self):
        self.client.get(
            reverse('ifthenpay_callback'),
            {
                'anti_phishing_key': 'secret-callback-key',
                'request_id': 'req-100',
                'entidade': '12345',
                'referencia': '543210987',
                'valor': '19.00',
                'customer_email': 'cliente@example.com',
                'mobileNumber': '912345678',
            },
            HTTP_HOST='loja.lvh.me',
            HTTP_X_FORWARDED_FOR='203.0.113.45',
        )

        callback = PaymentCallback.objects.get(payment=self.payment)

        self.assertEqual(callback.ip_address, '203.0.113.0')
        self.assertEqual(callback.raw_payload['anti_phishing_key'], '[redacted]')
        self.assertEqual(callback.raw_payload['mobileNumber'], '912***78')
        self.assertEqual(callback.raw_payload['customer_email'], 'cl***@example.com')

    @patch('apps.payments.services.send_mail')
    def test_already_paid_callback_is_idempotent_and_does_not_resend_notifications(self, send_mail):
        self.payment.status = Payment.Status.PAID
        self.payment.paid_at = timezone.now()
        self.payment.save(update_fields=['status', 'paid_at'])
        self.order.status = Order.Status.PAID
        self.order.save(update_fields=['status', 'updated_at'])

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(
                reverse('ifthenpay_callback'),
                {
                    'anti_phishing_key': 'secret-callback-key',
                    'request_id': 'req-100',
                    'entidade': '12345',
                    'referencia': '543210987',
                    'valor': '19.00',
                },
                HTTP_HOST='loja.lvh.me',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(send_mail.call_count, 0)

    @patch('apps.payments.services.send_mail')
    def test_callback_uses_entity_and_reference_when_request_id_is_missing(self, send_mail):
        other_order = Order.objects.create(
            name='Outro Cliente',
            email='outro@example.com',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.GUIMARAES,
            subtotal=Decimal('19.00'),
            total=Decimal('19.00'),
            status=Order.Status.PAYMENT_PENDING,
        )
        Payment.objects.create(
            order=other_order,
            method=Payment.Method.MULTIBANCO,
            status=Payment.Status.PENDING,
            amount=other_order.total,
            ifthenpay_request_id='req-200',
            mb_entity='99999',
            mb_reference='543210987',
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(
                reverse('ifthenpay_callback'),
                {
                    'anti_phishing_key': 'secret-callback-key',
                    'entidade': '12345',
                    'referencia': '543210987',
                    'valor': '19.00',
                },
                HTTP_HOST='loja.lvh.me',
            )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        other_order.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(other_order.status, Order.Status.PAYMENT_PENDING)
        self.assertEqual(send_mail.call_count, 2)


class PaymentConstraintTests(TestCase):
    def _create_order(self, *, email):
        return Order.objects.create(
            name='Marco',
            email=email,
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal=Decimal('19.00'),
            total=Decimal('19.00'),
            status=Order.Status.PAYMENT_PENDING,
        )

    def test_duplicate_non_empty_ifthenpay_request_id_is_rejected(self):
        first_order = self._create_order(email='primeiro@example.com')
        second_order = self._create_order(email='segundo@example.com')
        Payment.objects.create(
            order=first_order,
            method=Payment.Method.MBWAY,
            status=Payment.Status.PENDING,
            amount=first_order.total,
            ifthenpay_request_id='req-duplicate',
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    order=second_order,
                    method=Payment.Method.MBWAY,
                    status=Payment.Status.PENDING,
                    amount=second_order.total,
                    ifthenpay_request_id='req-duplicate',
                )

    def test_duplicate_multibanco_entity_reference_pair_is_rejected(self):
        first_order = self._create_order(email='primeiro@example.com')
        second_order = self._create_order(email='segundo@example.com')
        Payment.objects.create(
            order=first_order,
            method=Payment.Method.MULTIBANCO,
            status=Payment.Status.PENDING,
            amount=first_order.total,
            mb_entity='12345',
            mb_reference='543210987',
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Payment.objects.create(
                    order=second_order,
                    method=Payment.Method.MULTIBANCO,
                    status=Payment.Status.PENDING,
                    amount=second_order.total,
                    mb_entity='12345',
                    mb_reference='543210987',
                )

    def test_same_reference_with_different_entity_is_allowed(self):
        first_order = self._create_order(email='primeiro@example.com')
        second_order = self._create_order(email='segundo@example.com')
        Payment.objects.create(
            order=first_order,
            method=Payment.Method.MULTIBANCO,
            status=Payment.Status.PENDING,
            amount=first_order.total,
            mb_entity='12345',
            mb_reference='543210987',
        )
        Payment.objects.create(
            order=second_order,
            method=Payment.Method.MULTIBANCO,
            status=Payment.Status.PENDING,
            amount=second_order.total,
            mb_entity='67890',
            mb_reference='543210987',
        )

        self.assertEqual(Payment.objects.filter(mb_reference='543210987').count(), 2)


@override_settings(ROOT_URLCONF='config.urls_admin')
class PaymentAdminWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = cast(Any, user_model._default_manager).create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123',
        )
        self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
        self.client.force_login(self.admin_user)
        order = Order.objects.create(
            name='Marco',
            email='marco@example.com',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal=Decimal('19.00'),
            total=Decimal('19.00'),
            status=Order.Status.PAYMENT_PENDING,
        )
        self.payment = Payment.objects.create(
            order=order,
            method=Payment.Method.MULTIBANCO,
            status=Payment.Status.PENDING,
            amount=order.total,
            ifthenpay_request_id='req-admin-1',
            mb_entity='12345',
            mb_reference='543210987',
        )
        PaymentCallback.objects.create(
            payment=self.payment,
            raw_payload={'status': 'missing amount'},
            ip_address='203.0.113.0',
            is_valid=False,
            validation_message='missing amount',
        )

    def test_payment_admin_changelist_shows_workflow_cards(self):
        response = self.client.get(reverse('admin:payments_payment_changelist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pendentes')
        self.assertContains(response, 'Callbacks inválidos')

    def test_payment_change_form_shows_related_record_tools(self):
        response = self.client.get(reverse('admin:payments_payment_change', args=[self.payment.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Abrir encomenda')
        self.assertContains(response, 'Ver callbacks')
