from datetime import timedelta
from decimal import Decimal
from typing import Any, cast
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentCallback
from apps.payments.services import (
    finalize_successful_payment,
    PaymentTransitionError,
    StripeService,
    STRIPE_CHECKOUT_EXPIRY_WINDOW,
    configure_stripe_checkout,
    expire_stale_pending_payments,
    mark_payment_failed,
    mark_payment_refunded,
)


class PaymentValidationTests(TestCase):
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

    def test_payment_save_rejects_insecure_checkout_url(self):
        payment = Payment(
            order=self.order,
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=self.order.total,
            checkout_url='http://checkout.example.com/pay/session',
        )

        with self.assertRaises(ValidationError) as ctx:
            payment.save()

        self.assertIn('checkout_url', ctx.exception.message_dict)

    def test_payment_save_rejects_non_object_provider_data(self):
        payment = Payment(
            order=self.order,
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=self.order.total,
            provider_data=['invalid'],
        )

        with self.assertRaises(ValidationError) as ctx:
            payment.save()

        self.assertIn('provider_data', ctx.exception.message_dict)


@override_settings(
    ROOT_URLCONF='config.urls_shop',
    DEFAULT_FROM_EMAIL='loja@biobrassica.pt',
    STAFF_NOTIFICATION_EMAILS=['ops@biobrassica.pt'],
)
class PaymentWorkflowTests(TestCase):
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
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=self.order.total,
            stripe_session_id='cs_test_100',
            stripe_payment_intent_id='pi_test_100',
            checkout_url='https://checkout.stripe.com/pay/cs_test_100',
        )

    def test_invalid_payment_transition_blocked(self):
        self.payment.status = Payment.Status.PAID
        self.payment.paid_at = timezone.now()
        self.payment.save(update_fields=['status', 'paid_at'])

        with self.assertRaises(PaymentTransitionError):
            mark_payment_failed(self.payment, reason='late failure')

    @patch('apps.payments.services.send_mail')
    def test_finalize_successful_payment_schedules_notifications(self, send_mail):
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic():
                locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=self.payment.pk)
                changed = finalize_successful_payment(locked_payment, source='test_suite')

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertTrue(changed)
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(send_mail.call_count, 2)

    @override_settings(STRIPE_SECRET_KEY='sk_test_key', STRIPE_CURRENCY='eur')
    @patch('apps.payments.services.stripe.checkout.Session.create')
    def test_stripe_checkout_session_metadata_excludes_guest_access_token(self, session_create):
        order = Mock()
        order.pk = 42
        order.email = 'marco@example.com'
        order.access_token = 'secret-token'
        order.items.all.return_value = [
            Mock(quantity=2, price=Decimal('9.50'), product_name='Azeite bio'),
        ]
        payment = Mock(pk=7)
        session_create.return_value = type('StripeSession', (), {
            'id': 'cs_test_meta',
            'payment_intent': 'pi_test_meta',
            'url': 'https://checkout.stripe.com/pay/cs_test_meta',
            'expires_at': None,
        })()

        StripeService().create_checkout_session(
            order=order,
            payment=payment,
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel',
        )

        metadata = session_create.call_args.kwargs['metadata']
        self.assertEqual(metadata['order_id'], '42')
        self.assertEqual(metadata['payment_id'], '7')
        self.assertNotIn('access_token', metadata)

    def test_configure_stripe_checkout_sets_local_expiry(self):
        before_call = timezone.now()

        configure_stripe_checkout(
            self.payment,
            session_id='cs_test_200',
            payment_intent_id='pi_test_200',
            checkout_url='https://checkout.stripe.com/pay/cs_test_200',
        )

        self.payment.refresh_from_db()

        self.assertGreaterEqual(self.payment.expires_at, before_call + STRIPE_CHECKOUT_EXPIRY_WINDOW)

    def test_expire_stale_pending_payments_reverts_order_to_pending(self):
        self.payment.expires_at = timezone.now() - timedelta(minutes=5)
        self.payment.save(update_fields=['expires_at'])

        expired_count = expire_stale_pending_payments()

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(expired_count, 1)
        self.assertEqual(self.payment.status, Payment.Status.EXPIRED)
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_mark_payment_refunded_cancels_paid_order_and_restores_stock(self):
        from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation
        from apps.orders.models import OrderItem

        category = Category.objects.create(slug='mercearia-refund')
        CategoryTranslation.objects.create(
            category=category,
            language='pt',
            name='Mercearia',
            description='Categoria de mercearia',
        )
        product = Product.objects.create(
            category=category,
            slug='produto-refund',
            brand='Biobrassica',
            price=Decimal('4.00'),
            quantity='1 un',
            allow_shipping=True,
            stock=3,
            is_active=True,
            bio_code='PT-BIO-03',
        )
        ProductTranslation.objects.create(
            product=product,
            language='pt',
            name='Produto refund',
            description='Produto para testar refund.',
            allergens='Sem alergénios declarados.',
            ingredients='Ingrediente.',
        )
        paid_order = Order.objects.create(
            name='Refund',
            email='refund@example.com',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal=Decimal('8.00'),
            total=Decimal('8.00'),
            status=Order.Status.PAID,
        )
        refunded_payment = Payment.objects.create(
            order=paid_order,
            method=Payment.Method.STRIPE,
            status=Payment.Status.PAID,
            amount=paid_order.total,
            paid_at=timezone.now(),
            stripe_session_id='cs_refund_paid',
        )
        OrderItem.objects.create(
            order=paid_order,
            product=product,
            product_name='Produto refund',
            price=Decimal('4.00'),
            quantity=2,
        )
        product.stock = 1
        product.save(update_fields=['stock', 'updated_at'])

        changed = mark_payment_refunded(refunded_payment)

        refunded_payment.refresh_from_db()
        paid_order.refresh_from_db()
        product.refresh_from_db()

        self.assertTrue(changed)
        self.assertEqual(refunded_payment.status, Payment.Status.REFUNDED)
        self.assertEqual(paid_order.status, Order.Status.CANCELLED)
        self.assertEqual(product.stock, 3)

    def test_mark_payment_refunded_flags_preparing_order_for_manual_review(self):
        self.payment.status = Payment.Status.PAID
        self.payment.paid_at = timezone.now()
        self.payment.save(update_fields=['status', 'paid_at'])
        self.order.status = Order.Status.PREPARING
        self.order.notes = 'Separar cabaz.'
        self.order.save(update_fields=['status', 'notes', 'updated_at'])

        changed = mark_payment_refunded(self.payment)

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertTrue(changed)
        self.assertEqual(self.payment.status, Payment.Status.REFUNDED)
        self.assertEqual(self.order.status, Order.Status.PREPARING)
        self.assertIn('Reembolso registado', self.order.notes)

    def test_mark_payment_failed_sanitizes_and_truncates_last_error(self):
        reason = 'card declined for marco@example.com ' + ('x' * 400)

        changed = mark_payment_failed(self.payment, reason=reason)

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertTrue(changed)
        self.assertEqual(self.payment.status, Payment.Status.FAILED)
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertIn('ma***@example.com', self.payment.last_error)
        self.assertNotIn('marco@example.com', self.payment.last_error)
        self.assertLessEqual(len(self.payment.last_error), 255)


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

    def test_duplicate_non_empty_stripe_session_id_is_rejected(self):
        first_order = self._create_order(email='primeiro@example.com')
        second_order = self._create_order(email='segundo@example.com')
        Payment.objects.create(
            order=first_order,
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=first_order.total,
            stripe_session_id='cs_duplicate',
        )

        with self.assertRaises(ValidationError):
            Payment.objects.create(
                order=second_order,
                method=Payment.Method.STRIPE,
                status=Payment.Status.PENDING,
                amount=second_order.total,
                stripe_session_id='cs_duplicate',
            )

    def test_duplicate_non_empty_provider_event_id_is_rejected(self):
        PaymentCallback.objects.create(
            payment=None,
            raw_payload={'type': 'checkout.session.completed'},
            provider_event_id='evt_duplicate',
            ip_address='203.0.113.0',
            is_valid=True,
            validation_message='ok',
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentCallback.objects.create(
                    payment=None,
                    raw_payload={'type': 'checkout.session.completed'},
                    provider_event_id='evt_duplicate',
                    ip_address='203.0.113.0',
                    is_valid=True,
                    validation_message='ok',
                )


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
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=order.total,
            stripe_session_id='cs_admin_1',
            stripe_payment_intent_id='pi_admin_1',
        )
        PaymentCallback.objects.create(
            payment=self.payment,
            raw_payload={'type': 'checkout.session.completed'},
            provider_event_id='evt_admin_invalid',
            ip_address='203.0.113.0',
            is_valid=False,
            validation_message='signature verification failed',
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


@override_settings(
    ROOT_URLCONF='config.urls_shop',
    STRIPE_WEBHOOK_SECRET='whsec_test_secret',
    DEFAULT_FROM_EMAIL='loja@biobrassica.pt',
    STAFF_NOTIFICATION_EMAILS=['ops@biobrassica.pt'],
)
class StripeWebhookTests(TestCase):
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
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=self.order.total,
            stripe_session_id='cs_test_100',
            stripe_payment_intent_id='pi_test_100',
            checkout_url='https://checkout.stripe.com/pay/cs_test_100',
        )

    @patch('apps.payments.services.send_mail')
    @patch('apps.payments.views.stripe_service.construct_webhook_event')
    def test_stripe_completed_webhook_marks_order_paid(self, construct_event, send_mail):
        construct_event.return_value = {
            'id': 'evt_test_completed',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_100',
                    'payment_intent': 'pi_test_100',
                    'customer_details': {'email': 'marco@example.com'},
                    'metadata': {'order_id': str(self.order.pk)},
                },
            },
        }

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('stripe_callback'),
                data='{}',
                content_type='application/json',
                HTTP_HOST='loja.lvh.me',
                HTTP_STRIPE_SIGNATURE='test-signature',
            )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()
        callback = PaymentCallback.objects.get(provider_event_id='evt_test_completed')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertTrue(callback.is_valid)
        self.assertEqual(send_mail.call_count, 2)

    def test_invalid_stripe_signature_is_rejected(self):
        response = self.client.post(
            reverse('stripe_callback'),
            data='{}',
            content_type='application/json',
            HTTP_HOST='loja.lvh.me',
            HTTP_STRIPE_SIGNATURE='invalid-signature',
        )

        callback = PaymentCallback.objects.get(payment=None)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(callback.is_valid)
        self.assertEqual(callback.validation_message, 'invalid stripe signature')

    @patch('apps.payments.views.stripe_service.construct_webhook_event')
    def test_duplicate_stripe_event_is_idempotent(self, construct_event):
        PaymentCallback.objects.create(
            payment=self.payment,
            raw_payload={'type': 'checkout.session.completed'},
            provider_event_id='evt_test_duplicate',
            ip_address='203.0.113.0',
            is_valid=True,
            validation_message='ok',
        )
        construct_event.return_value = {
            'id': 'evt_test_duplicate',
            'type': 'checkout.session.completed',
            'data': {'object': {'id': 'cs_test_100', 'payment_intent': 'pi_test_100', 'metadata': {}}},
        }

        response = self.client.post(
            reverse('stripe_callback'),
            data='{}',
            content_type='application/json',
            HTTP_HOST='loja.lvh.me',
            HTTP_STRIPE_SIGNATURE='test-signature',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentCallback.objects.filter(provider_event_id='evt_test_duplicate').count(), 1)

    @patch('apps.payments.views.PaymentCallback.objects.get_or_create', side_effect=IntegrityError)
    @patch('apps.payments.views.stripe_service.construct_webhook_event')
    def test_duplicate_stripe_event_race_returns_ok(self, construct_event, get_or_create):
        construct_event.return_value = {
            'id': 'evt_test_duplicate_race',
            'type': 'checkout.session.completed',
            'data': {'object': {'id': 'cs_test_100', 'payment_intent': 'pi_test_100', 'metadata': {}}},
        }

        response = self.client.post(
            reverse('stripe_callback'),
            data='{}',
            content_type='application/json',
            HTTP_HOST='loja.lvh.me',
            HTTP_STRIPE_SIGNATURE='test-signature',
        )

        self.assertEqual(response.status_code, 200)
        get_or_create.assert_called_once()

    @patch('apps.payments.views.stripe_service.construct_webhook_event')
    def test_refunded_webhook_cancels_paid_order(self, construct_event):
        self.payment.status = Payment.Status.PAID
        self.payment.paid_at = timezone.now()
        self.payment.save(update_fields=['status', 'paid_at'])
        self.order.status = Order.Status.PAID
        self.order.save(update_fields=['status', 'updated_at'])
        construct_event.return_value = {
            'id': 'evt_test_refund',
            'type': 'charge.refunded',
            'data': {
                'object': {
                    'id': 'pi_test_100',
                    'payment_intent': 'pi_test_100',
                    'metadata': {},
                },
            },
        }

        response = self.client.post(
            reverse('stripe_callback'),
            data='{}',
            content_type='application/json',
            HTTP_HOST='loja.lvh.me',
            HTTP_STRIPE_SIGNATURE='test-signature',
        )

        self.payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.payment.status, Payment.Status.REFUNDED)
        self.assertEqual(self.order.status, Order.Status.CANCELLED)

    @patch('apps.payments.views.stripe_service.construct_webhook_event')
    def test_unknown_stripe_payment_is_recorded_without_failing_delivery(self, construct_event):
        construct_event.return_value = {
            'id': 'evt_unknown_payment',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_unknown',
                    'payment_intent': 'pi_unknown',
                    'customer_details': {'email': 'unknown@example.com'},
                    'metadata': {},
                },
            },
        }

        response = self.client.post(
            reverse('stripe_callback'),
            data='{}',
            content_type='application/json',
            HTTP_HOST='loja.lvh.me',
            HTTP_STRIPE_SIGNATURE='test-signature',
        )

        callback = PaymentCallback.objects.get(provider_event_id='evt_unknown_payment')

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(callback.payment)
        self.assertFalse(callback.is_valid)
        self.assertEqual(callback.validation_message, 'payment not found')
