from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, CategoryTranslation, Location, Product, ProductTranslation
from apps.orders.models import Order, OrderItem
from apps.orders.services import create_order_from_cart
from apps.payments.models import Payment


@override_settings(ROOT_URLCONF='config.urls_shop')
class OrderCheckoutFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='checkout@example.com',
            username='checkout',
            password='testpass123',
        )
        self.other_user = get_user_model().objects.create_user(
            email='other@example.com',
            username='other',
            password='testpass123',
        )
        self.client.force_login(self.user)
        self.braga_location = Location.objects.create(
            name='Loja Braga',
            pickup_location_code=Order.PickupLocation.BRAGA,
            is_active=True,
            order=1,
        )
        self.guimaraes_location = Location.objects.create(
            name='Loja Guimarães',
            pickup_location_code=Order.PickupLocation.GUIMARAES,
            is_active=True,
            order=2,
        )
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
        self.product.available_locations.add(self.braga_location)

    def _create_guest_cart(self):
        Cart.objects.filter(user=self.user).delete()
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        return cart

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_creates_order_moves_items_and_empties_cart(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_test_100',
            'payment_intent_id': 'pi_test_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_test_100',
        }
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

        # In the new streamlined flow, checkout_confirm redirects directly to Stripe
        self.assertRedirects(
            response,
            'https://checkout.stripe.com/pay/cs_test_100',
            fetch_redirect_response=False,
        )
        # Order status is now PAYMENT_PENDING after Stripe payment creation
        self.assertEqual(order.status, Order.Status.PAYMENT_PENDING)
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertEqual(OrderItem.objects.get(order=order).quantity, 2)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_stripe_payment_selection_creates_pending_payment(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_test_100',
            'payment_intent_id': 'pi_test_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_test_100',
        }
        self._create_guest_cart()
        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
        )
        order = Order.objects.get(email='marco@example.com')

        payment = Payment.objects.get(order=order)
        order.refresh_from_db()
        
        # In the new streamlined flow, checkout_confirm directly creates Stripe payment
        self.assertRedirects(
            response,
            'https://checkout.stripe.com/pay/cs_test_100',
            fetch_redirect_response=False,
        )
        self.assertEqual(payment.method, Payment.Method.STRIPE)
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.stripe_session_id, 'cs_test_100')
        self.assertEqual(payment.stripe_payment_intent_id, 'pi_test_100')
        self.assertEqual(payment.checkout_url, 'https://checkout.stripe.com/pay/cs_test_100')
        self.assertEqual(order.status, Order.Status.PAYMENT_PENDING)

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_payment_selection_rejects_non_stripe_methods(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_test_100',
            'payment_intent_id': 'pi_test_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_test_100',
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
                'payment_method': 'unsupported-provider',
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertContains(response, 'Selecione um método de pagamento válido.')
        # Payment from checkout_confirm should still exist (it's the Stripe one)
        # but the invalid payment selection should fail

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_order_pages_require_authenticated_owner(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_test_100',
            'payment_intent_id': 'pi_test_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_test_100',
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

        response = self.client.get(
            reverse('orders:payment_select', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
        )

        self.assertEqual(response.status_code, 200)

        isolated_client = Client()
        isolated_response = isolated_client.get(
            reverse('orders:payment_select', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
        )

        self.assertRedirects(
            isolated_response,
            f"{reverse('accounts:login')}?next={reverse('orders:payment_select', kwargs={'order_id': order.pk})}",
            fetch_redirect_response=False,
        )

        self.client.force_login(self.other_user)
        forbidden_response = self.client.get(
            reverse('orders:payment_select', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
        )

        self.assertEqual(forbidden_response.status_code, 404)
        self.client.force_login(self.user)

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_supports_shipping_when_all_products_allow_it(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_test_100',
            'payment_intent_id': 'pi_test_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_test_100',
        }
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
        # In the new streamlined flow, checkout_confirm redirects directly to Stripe
        self.assertRedirects(
            response,
            'https://checkout.stripe.com/pay/cs_test_100',
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

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_keeps_cart_and_cancels_order_when_stripe_setup_fails(self, create_checkout_session):
        create_checkout_session.side_effect = RuntimeError('boom')
        cart = self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        order = Order.objects.get(email='marco@example.com')

        self.assertRedirects(response, reverse('orders:checkout'))
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 1)
        self.assertFalse(Payment.objects.filter(order=order).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_rejects_inactive_products_left_in_cart(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_test_100',
            'payment_intent_id': 'pi_test_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_test_100',
        }
        cart = self._create_guest_cart()
        self.product.is_active = False
        self.product.save(update_fields=['is_active'])

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertRedirects(response, reverse('cart:detail'))
        self.assertFalse(Order.objects.filter(email='marco@example.com').exists())
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_rejects_preview_only_products_left_in_cart(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_test_100',
            'payment_intent_id': 'pi_test_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_test_100',
        }
        cart = self._create_guest_cart()
        self.product.is_preview_only = True
        self.product.save(update_fields=['is_preview_only'])

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertRedirects(response, reverse('cart:detail'))
        self.assertContains(response, 'Alguns produtos deixaram de estar disponíveis para compra e foram removidos do carrinho.')
        self.assertFalse(Order.objects.filter(email='marco@example.com').exists())
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    @override_settings(PAYMENTS_FORCE_DISABLED=True)
    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_rejects_when_payments_are_disabled(self, create_checkout_session):
        self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertRedirects(response, reverse('orders:checkout'))
        self.assertContains(response, 'Os pagamentos estão temporariamente indisponíveis.')
        self.assertFalse(Order.objects.filter(email='marco@example.com').exists())
        create_checkout_session.assert_not_called()

    @override_settings(PAYMENTS_FORCE_DISABLED=True)
    def test_payment_select_rejects_when_payments_are_disabled(self):
        user = get_user_model().objects.create_user(
            email='cliente@example.com',
            username='cliente',
            password='testpass123',
        )
        order = Order.objects.create(
            user=user,
            name='Cliente',
            email=user.email,
            phone='912345678',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal='19.00',
            total='19.00',
            status=Order.Status.PENDING,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('orders:payment_select', kwargs={'order_id': order.pk}),
            {'payment_method': Payment.Method.STRIPE},
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertRedirects(response, reverse('orders:payment_select', kwargs={'order_id': order.pk}))
        self.assertContains(response, 'Os pagamentos estão temporariamente indisponíveis.')
        self.assertFalse(Payment.objects.filter(order=order).exists())

    def test_checkout_confirm_shows_postal_code_field_errors(self):
        self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'fulfillment_method': Order.FulfillmentMethod.SHIPPING,
                'shipping_address_line1': 'Rua Central 100',
                'shipping_city': 'Braga',
                'shipping_postal_code': '4700100',
            },
            HTTP_HOST='loja.lvh.me',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Use o formato 1234-123.')
        self.assertFalse(Order.objects.filter(email='marco@example.com').exists())

    def test_checkout_confirm_shows_pickup_location_errors(self):
        self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'fulfillment_method': Order.FulfillmentMethod.PICKUP,
                'pickup_location': '',
            },
            HTTP_HOST='loja.lvh.me',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selecione um local de levantamento.')
        self.assertFalse(Order.objects.filter(email='marco@example.com').exists())

    def test_checkout_confirm_rejects_pickup_location_not_available_for_cart(self):
        self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'fulfillment_method': Order.FulfillmentMethod.PICKUP,
                'pickup_location': Order.PickupLocation.GUIMARAES,
            },
            HTTP_HOST='loja.lvh.me',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este local não está disponível para todos os produtos do carrinho.')
        self.assertFalse(Order.objects.filter(email='marco@example.com').exists())

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_uses_pickup_location_code_instead_of_location_name(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_pickup_code_100',
            'payment_intent_id': 'pi_pickup_code_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_pickup_code_100',
        }
        self.braga_location.name = 'Mercado Centro'
        self.braga_location.save(update_fields=['name'])
        self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Marco',
                'email': 'marco@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
        )

        order = Order.objects.get(email='marco@example.com')

        self.assertRedirects(
            response,
            'https://checkout.stripe.com/pay/cs_pickup_code_100',
            fetch_redirect_response=False,
        )
        self.assertEqual(order.pickup_location, Order.PickupLocation.BRAGA)

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_rejects_cart_mutation_after_snapshot(self, create_checkout_session):
        create_checkout_session.return_value = {
            'session_id': 'cs_snapshot_100',
            'payment_intent_id': 'pi_snapshot_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_snapshot_100',
        }
        cart = self._create_guest_cart()
        original_create_order_from_cart = create_order_from_cart

        def mutate_then_create(**kwargs):
            CartItem.objects.filter(cart=cart).update(quantity=3)
            return original_create_order_from_cart(**kwargs)

        with patch('apps.orders.views.create_order_from_cart', side_effect=mutate_then_create):
            response = self.client.post(
                reverse('orders:confirm'),
                {
                    'name': 'Marco',
                    'email': 'marco@example.com',
                    'pickup_location': Order.PickupLocation.BRAGA,
                },
                HTTP_HOST='loja.lvh.me',
            )

        cart_item = CartItem.objects.get(cart=cart)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'O carrinho foi atualizado durante o checkout.')
        self.assertFalse(Order.objects.filter(email='marco@example.com').exists())
        self.assertEqual(cart_item.quantity, 3)
        create_checkout_session.assert_not_called()

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_directly_creates_stripe_payment_with_correct_amount(self, create_checkout_session):
        """Direct checkout to Stripe (no payment_select page) - payment must have correct amount."""
        create_checkout_session.return_value = {
            'session_id': 'cs_direct_100',
            'payment_intent_id': 'pi_direct_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_direct_100',
        }
        self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'João Silva',
                'email': 'joao@example.com',
                'phone': '923456789',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
        )

        order = Order.objects.get(email='joao@example.com')
        payment = Payment.objects.get(order=order)

        # Verify payment was created with correct amount
        self.assertEqual(payment.amount, order.total)
        self.assertEqual(payment.amount, Decimal('19.00'))  # 2 items × 9.50
        self.assertEqual(payment.method, Payment.Method.STRIPE)
        self.assertEqual(payment.status, Payment.Status.PENDING)

        # Verify redirect to Stripe checkout
        self.assertRedirects(
            response,
            'https://checkout.stripe.com/pay/cs_direct_100',
            fetch_redirect_response=False,
        )

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_handles_stripe_exception(self, create_checkout_session):
        """Stripe errors should show user-friendly message and redirect to checkout."""
        create_checkout_session.side_effect = Exception('Stripe API error')
        self._create_guest_cart()

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Jane Doe',
                'email': 'jane@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        # Verify order and payment were still created (payment happens before Stripe call)
        order = Order.objects.filter(email='jane@example.com').first()
        self.assertIsNotNone(order)

        # Verify error message was shown
        self.assertContains(response, 'Não foi possível iniciar o pagamento. Tente novamente.')

    @patch('apps.orders.views.stripe_service.create_checkout_session')
    def test_checkout_confirm_stripe_session_has_correct_urls(self, create_checkout_session):
        """Verify Stripe session is created with correct success/cancel URLs."""
        create_checkout_session.return_value = {
            'session_id': 'cs_urls_100',
            'payment_intent_id': 'pi_urls_100',
            'checkout_url': 'https://checkout.stripe.com/pay/cs_urls_100',
        }
        self._create_guest_cart()

        self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'URL Test',
                'email': 'url@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
        )

        create_checkout_session.assert_called_once()
        call_kwargs = create_checkout_session.call_args[1]

        # Verify success and cancel URLs are provided
        self.assertIn('success_url', call_kwargs)
        self.assertIn('cancel_url', call_kwargs)
        self.assertIn(reverse('orders:payment_status', kwargs={'order_id': Order.objects.get(email='url@example.com').pk}), call_kwargs['success_url'])
        self.assertIn('session_id=', call_kwargs['success_url'])
        self.assertNotIn('token=', call_kwargs['success_url'])
        self.assertNotIn('token=', call_kwargs['cancel_url'])
        self.assertIn(reverse('orders:checkout_order', kwargs={'order_id': Order.objects.get(email='url@example.com').pk}), call_kwargs['cancel_url'])

    def test_empty_cart_blocks_checkout(self):
        """Empty cart should prevent checkout."""
        cart = Cart.objects.create(user=self.user)

        response = self.client.post(
            reverse('orders:confirm'),
            {
                'name': 'Empty Cart',
                'email': 'empty@example.com',
                'pickup_location': Order.PickupLocation.BRAGA,
            },
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertContains(response, 'O seu carrinho está vazio.')
        self.assertFalse(Order.objects.filter(email='empty@example.com').exists())

    def test_payment_amount_matches_order_total_with_multiple_items(self):
        """Payment amount should match order total for multiple items."""
        cart = self._create_guest_cart()
        # Add another product
        product2 = Product.objects.create(
            category=self.category,
            slug='pao-bio',
            brand='Biobrassica',
            price=Decimal('3.25'),
            quantity='um',
            stock=10,
            is_active=True,
            bio_code='PT-BIO-04',
        )
        ProductTranslation.objects.create(
            product=product2,
            language='pt',
            name='Pão bio',
        )
        product2.available_locations.add(self.braga_location)
        CartItem.objects.create(cart=cart, product=product2, quantity=1)

        with patch('apps.orders.views.stripe_service.create_checkout_session') as mock_stripe:
            mock_stripe.return_value = {
                'session_id': 'cs_multi_100',
                'payment_intent_id': 'pi_multi_100',
                'checkout_url': 'https://checkout.stripe.com/pay/cs_multi_100',
            }

            self.client.post(
                reverse('orders:confirm'),
                {
                    'name': 'Multi Item',
                    'email': 'multi@example.com',
                    'pickup_location': Order.PickupLocation.BRAGA,
                },
                HTTP_HOST='loja.lvh.me',
            )

            order = Order.objects.get(email='multi@example.com')
            payment = Payment.objects.get(order=order)

            # 2 × 9.50 + 1 × 3.25 = 22.25
            expected_total = Decimal('22.25')
            self.assertEqual(order.total, expected_total)
            self.assertEqual(payment.amount, expected_total)

    def test_complete_page_redirects_until_payment_is_confirmed(self):
        order = Order.objects.create(
            user=self.user,
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
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=order.total,
            stripe_session_id='cs_test_100',
            checkout_url='https://checkout.stripe.com/pay/cs_test_100',
        )

        response = self.client.get(
            reverse('orders:complete', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse('orders:payment_status', kwargs={'order_id': order.pk}),
            fetch_redirect_response=False,
        )

    @patch('apps.orders.views.stripe_service.retrieve_checkout_session')
    def test_payment_status_poll_expiry_uses_service_and_resets_order(self, retrieve_checkout_session):
        order = Order.objects.create(
            user=self.user,
            name='Marco',
            email='marco@example.com',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal=Decimal('19.00'),
            total=Decimal('19.00'),
            status=Order.Status.PAYMENT_PENDING,
        )
        payment = Payment.objects.create(
            order=order,
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=order.total,
            stripe_session_id='cs_expired_100',
            checkout_url='https://checkout.stripe.com/pay/cs_expired_100',
        )
        retrieve_checkout_session.return_value = type('StripeSession', (), {'payment_status': 'unpaid', 'status': 'expired'})()

        response = self.client.get(
            reverse('orders:payment_status', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
            follow=True,
        )

        payment.refresh_from_db()
        order.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, Payment.Status.EXPIRED)
        self.assertEqual(payment.last_error, 'stripe checkout expired (poll)')
        self.assertEqual(order.status, Order.Status.PENDING)

    @override_settings(DEFAULT_FROM_EMAIL='loja@biobrassica.pt', STAFF_NOTIFICATION_EMAILS=['ops@biobrassica.pt'])
    @patch('apps.payments.services.send_mail')
    @patch('apps.orders.views.stripe_service.retrieve_checkout_session')
    def test_payment_status_poll_paid_marks_order_paid_and_sends_notifications(self, retrieve_checkout_session, send_mail):
        order = Order.objects.create(
            user=self.user,
            name='Marco',
            email='marco@example.com',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal=Decimal('19.00'),
            total=Decimal('19.00'),
            status=Order.Status.PAYMENT_PENDING,
        )
        payment = Payment.objects.create(
            order=order,
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=order.total,
            stripe_session_id='cs_paid_100',
            checkout_url='https://checkout.stripe.com/pay/cs_paid_100',
        )
        retrieve_checkout_session.return_value = type('StripeSession', (), {'payment_status': 'paid', 'status': 'complete'})()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(
                reverse('orders:payment_status', kwargs={'order_id': order.pk}),
                HTTP_HOST='loja.lvh.me',
            )

        payment.refresh_from_db()
        order.refresh_from_db()

        self.assertRedirects(
            response,
            reverse('orders:complete', kwargs={'order_id': order.pk}),
            fetch_redirect_response=False,
        )
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(send_mail.call_count, 2)

    def test_payment_status_requires_authenticated_owner(self):
        order = Order.objects.create(
            user=self.user,
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
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=order.total,
            stripe_session_id='cs_exchange_100',
            checkout_url='https://checkout.stripe.com/pay/cs_exchange_100',
        )
        isolated_client = Client()

        first_response = isolated_client.get(
            reverse('orders:payment_status', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
        )

        self.assertRedirects(
            first_response,
            f"{reverse('accounts:login')}?next={reverse('orders:payment_status', kwargs={'order_id': order.pk})}",
            fetch_redirect_response=False,
        )

        self.client.force_login(self.other_user)
        second_response = self.client.get(
            reverse('orders:payment_status', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
        )

        self.assertEqual(second_response.status_code, 404)
        self.client.force_login(self.user)

    def test_checkout_order_redirects_pending_order_to_payment_status(self):
        order = Order.objects.create(
            user=self.user,
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
            method=Payment.Method.STRIPE,
            status=Payment.Status.PENDING,
            amount=order.total,
            stripe_session_id='cs_resume_100',
            checkout_url='https://checkout.stripe.com/pay/cs_resume_100',
        )

        response = self.client.get(
            reverse('orders:checkout_order', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
        )

        self.assertRedirects(
            response,
            reverse('orders:payment_status', kwargs={'order_id': order.pk}),
            fetch_redirect_response=False,
        )

    def test_checkout_order_redirects_unpaid_order_without_payment_to_payment_selection(self):
        order = Order.objects.create(
            user=self.user,
            name='Marco',
            email='marco@example.com',
            fulfillment_method=Order.FulfillmentMethod.PICKUP,
            pickup_location=Order.PickupLocation.BRAGA,
            subtotal=Decimal('19.00'),
            total=Decimal('19.00'),
            status=Order.Status.PENDING,
        )

        response = self.client.get(
            reverse('orders:checkout_order', kwargs={'order_id': order.pk}),
            HTTP_HOST='loja.lvh.me',
        )

        self.assertRedirects(
            response,
            reverse('orders:payment_select', kwargs={'order_id': order.pk}),
            fetch_redirect_response=False,
        )

    def test_checkout_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse('orders:checkout'), HTTP_HOST='loja.lvh.me')

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('orders:checkout')}",
            fetch_redirect_response=False,
        )
