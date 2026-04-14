from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from django.core.exceptions import ValidationError
from typing import cast
from decimal import Decimal
from django.contrib import admin

from apps.accounts.models import Address, User as AccountUser
from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment


User = AccountUser


@override_settings(ROOT_URLCONF='config.urls_shop')
class RegistrationViewTests(TestCase):
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
			price='9.50',
			quantity='750 ml',
			stock=10,
			is_active=True,
			allow_shipping=True,
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

	def test_register_redirects_to_shop_home(self):
		response = self.client.post(
			reverse('accounts:register'),
			{
				'email': 'nova@biobrassica.pt',
				'first_name': 'Nova',
				'last_name': 'Cliente',
				'phone': '912345678',
				'password1': 'S3guraPass123',
				'password2': 'S3guraPass123',
			},
			HTTP_HOST='loja.lvh.me',
		)

		self.assertRedirects(response, reverse('catalog:shop_home'))
		self.assertTrue(User.objects.filter(email='nova@biobrassica.pt').exists())

	def test_register_rejects_password_mismatch(self):
		response = self.client.post(
			reverse('accounts:register'),
			{
				'email': 'nova@biobrassica.pt',
				'first_name': 'Nova',
				'last_name': 'Cliente',
				'phone': '912345678',
				'password1': 'S3guraPass123',
				'password2': 'OutraPass123',
			},
			HTTP_HOST='loja.lvh.me',
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'As passwords não coincidem.')
		self.assertFalse(User.objects.filter(email='nova@biobrassica.pt').exists())

	def test_register_rejects_password_that_fails_django_validators(self):
		response = self.client.post(
			reverse('accounts:register'),
			{
				'email': 'nova@biobrassica.pt',
				'first_name': 'Nova',
				'last_name': 'Cliente',
				'phone': '912345678',
				'password1': '12345678',
				'password2': '12345678',
			},
			HTTP_HOST='loja.lvh.me',
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Esta palavra-passe é muito comum.')
		self.assertFalse(User.objects.filter(email='nova@biobrassica.pt').exists())

	def test_register_merges_anonymous_cart_into_new_user_cart(self):
		session = self.client.session
		session.save()
		anon_cart = Cart.objects.create(session_key=session.session_key)
		CartItem.objects.create(cart=anon_cart, product=self.product, quantity=2)

		response = self.client.post(
			reverse('accounts:register'),
			{
				'email': 'nova@biobrassica.pt',
				'first_name': 'Nova',
				'last_name': 'Cliente',
				'phone': '912345678',
				'password1': 'S3guraPass123',
				'password2': 'S3guraPass123',
			},
			HTTP_HOST='loja.lvh.me',
		)

		user = User.objects.get(email='nova@biobrassica.pt')
		user_cart = Cart.objects.get(user=user)
		merged_item = CartItem.objects.get(cart=user_cart, product=self.product)

		self.assertRedirects(response, reverse('catalog:shop_home'))
		self.assertEqual(merged_item.quantity, 2)
		self.assertFalse(Cart.objects.filter(pk=anon_cart.pk).exists())


@override_settings(ROOT_URLCONF='config.urls_shop')
class ProfileViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email='cliente@biobrassica.pt',
			username='cliente@biobrassica.pt',
			password='S3guraPass123',
			first_name='Cliente',
			last_name='Atual',
		)

	def test_profile_requires_login(self):
		response = self.client.get(reverse('accounts:profile'), HTTP_HOST='loja.lvh.me')

		self.assertRedirects(
			response,
			f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
			fetch_redirect_response=False,
		)

	def test_profile_post_updates_user_fields(self):
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('accounts:profile'),
			{
				'first_name': 'Marco',
				'last_name': 'Silva',
				'phone': '912345678',
				'preferred_language': 'en',
				'nif': '123456789',
			},
			HTTP_HOST='loja.lvh.me',
		)

		self.user = cast(AccountUser, User.objects.get(pk=self.user.pk))
		self.assertRedirects(response, reverse('accounts:profile'))
		self.assertEqual(self.user.first_name, 'Marco')
		self.assertEqual(self.user.last_name, 'Silva')
		self.assertEqual(self.user.phone, '912345678')
		self.assertEqual(self.user.preferred_language, 'en')
		self.assertEqual(self.user.nif, '123456789')

	def test_profile_post_normalizes_formatted_nif(self):
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('accounts:profile'),
			{
				'first_name': 'Marco',
				'last_name': 'Silva',
				'phone': '912345678',
				'preferred_language': 'en',
				'nif': '123 456 789',
			},
			HTTP_HOST='loja.lvh.me',
		)

		self.user = cast(AccountUser, User.objects.get(pk=self.user.pk))
		self.assertRedirects(response, reverse('accounts:profile'))
		self.assertEqual(self.user.nif, '123456789')

	def test_profile_post_shows_field_errors(self):
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('accounts:profile'),
			{
				'first_name': 'Marco',
				'last_name': 'Silva',
				'phone': '912345678',
				'preferred_language': 'en',
				'nif': '1234567890',
			},
			HTTP_HOST='loja.lvh.me',
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Indique um NIF português válido.')
		self.user = cast(AccountUser, User.objects.get(pk=self.user.pk))
		self.assertEqual(self.user.nif, '')

	def test_profile_post_rejects_invalid_nif_checksum(self):
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('accounts:profile'),
			{
				'first_name': 'Marco',
				'last_name': 'Silva',
				'phone': '912345678',
				'preferred_language': 'en',
				'nif': '123456780',
			},
			HTTP_HOST='loja.lvh.me',
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Indique um NIF português válido.')
		self.user = cast(AccountUser, User.objects.get(pk=self.user.pk))
		self.assertEqual(self.user.nif, '')

	def test_user_save_rejects_invalid_nif(self):
		with self.assertRaises(ValidationError):
			User.objects.create_user(
				email='invalido@biobrassica.pt',
				username='invalido@biobrassica.pt',
				password='S3guraPass123',
				nif='123456780',
			)

	def test_order_history_lists_only_current_user_orders(self):
		other_user = User.objects.create_user(
			email='outra@biobrassica.pt',
			username='outra@biobrassica.pt',
			password='S3guraPass123',
		)
		own_order = Order.objects.create(
			user=self.user,
			name='Cliente Atual',
			email=self.user.email,
			fulfillment_method=Order.FulfillmentMethod.PICKUP,
			pickup_location=Order.PickupLocation.BRAGA,
			subtotal='9.50',
			total='9.50',
		)
		other_order = Order.objects.create(
			user=other_user,
			name='Outro Cliente',
			email=other_user.email,
			fulfillment_method=Order.FulfillmentMethod.PICKUP,
			pickup_location=Order.PickupLocation.GUIMARAES,
			subtotal='4.00',
			total='4.00',
		)
		OrderItem.objects.create(order=own_order, product=None, product_name='Azeite bio', price='9.50', quantity=1)
		OrderItem.objects.create(order=other_order, product=None, product_name='Outro produto', price='4.00', quantity=1)

		self.client.force_login(self.user)
		response = self.client.get(reverse('accounts:order_history'), HTTP_HOST='loja.lvh.me')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'Encomenda #{own_order.pk}')
		self.assertContains(response, 'Azeite bio')
		self.assertNotContains(response, f'Encomenda #{other_order.pk}')
		self.assertNotContains(response, 'Outro produto')


@override_settings(ROOT_URLCONF='config.urls_admin')
class AccountsAdminWorkflowTests(TestCase):
	def setUp(self):
		self.admin_user = User.objects.create_superuser(
			email='admin@example.com',
			username='admin',
			password='testpass123',
		)
		self.customer = User.objects.create_user(
			email='cliente@biobrassica.pt',
			username='cliente',
			password='testpass123',
			first_name='Cliente',
			last_name='Ativo',
			phone='912345678',
			nif='123456789',
		)
		self.address = Address.objects.create(
			user=self.customer,
			name='Casa',
			line1='Rua das Flores 10',
			city='Braga',
			postal_code='4700-111',
			is_default=True,
		)
		Order.objects.create(
			user=self.customer,
			name='Cliente Ativo',
			email=self.customer.email,
			phone=self.customer.phone,
			fulfillment_method=Order.FulfillmentMethod.PICKUP,
			pickup_location=Order.PickupLocation.BRAGA,
			subtotal='15.00',
			total='15.00',
		)
		self.customer_without_default = User.objects.create_user(
			email='sem-morada@biobrassica.pt',
			username='sem-morada',
			password='testpass123',
		)

		self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
		self.client.force_login(self.admin_user)

	def test_user_admin_changelist_shows_customer_workflow_cards(self):
		response = self.client.get(reverse('admin:accounts_user_changelist'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Clientes ativos')
		self.assertContains(response, 'Sem telefone')
		self.assertContains(response, 'Sem morada predefinida')

	def test_user_change_form_shows_support_panels_and_tools(self):
		response = self.client.get(reverse('admin:accounts_user_change', args=[self.customer.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Resumo do cliente')
		self.assertContains(response, 'Serviço e acesso')
		self.assertContains(response, 'Ver encomendas')
		self.assertContains(response, 'Desativar acesso')

	def test_user_change_form_submit_action_deactivates_customer(self):
		response = self.client.post(
			reverse('admin:accounts_user_change', args=[self.customer.pk]),
			{'_deactivate_customer': '1'},
			follow=True,
		)

		self.customer.refresh_from_db()

		self.assertEqual(response.status_code, 200)
		self.assertFalse(self.customer.is_active)
		self.assertContains(response, 'Cliente desativado.')

	def test_address_change_form_shows_customer_context(self):
		response = self.client.get(reverse('admin:accounts_address_change', args=[self.address.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Resumo da morada')
		self.assertContains(response, 'Abrir cliente')
		self.assertContains(response, 'Histórico de encomendas')

	def test_user_admin_lifetime_revenue_excludes_refunded_orders(self):
		paid_order = Order.objects.create(
			user=self.customer,
			name='Cliente Ativo',
			email=self.customer.email,
			fulfillment_method=Order.FulfillmentMethod.PICKUP,
			pickup_location=Order.PickupLocation.BRAGA,
			subtotal='20.00',
			total='20.00',
			status=Order.Status.PAID,
		)
		Payment.objects.create(
			order=paid_order,
			method=Payment.Method.STRIPE,
			status=Payment.Status.PAID,
			amount='20.00',
		)
		refunded_order = Order.objects.create(
			user=self.customer,
			name='Cliente Ativo',
			email=self.customer.email,
			fulfillment_method=Order.FulfillmentMethod.PICKUP,
			pickup_location=Order.PickupLocation.BRAGA,
			subtotal='10.00',
			total='10.00',
			status=Order.Status.CANCELLED,
		)
		Payment.objects.create(
			order=refunded_order,
			method=Payment.Method.STRIPE,
			status=Payment.Status.REFUNDED,
			amount='10.00',
		)

		request = RequestFactory().get(reverse('admin:accounts_user_changelist'), HTTP_HOST='admin.lvh.me')
		request.user = self.admin_user
		user_admin = admin.site._registry[User]
		customer = user_admin.get_queryset(request).get(pk=self.customer.pk)

		self.assertEqual(customer.lifetime_revenue, Decimal('20.00'))
