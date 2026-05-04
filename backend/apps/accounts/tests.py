from io import StringIO
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from typing import cast
from decimal import Decimal
from django.contrib import admin
from unittest.mock import patch

from apps.accounts.models import Address, User as AccountUser
from apps.cart.models import Cart, CartItem
from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment


User = AccountUser

GIF_BYTES = (
	b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
	b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


class UserValidationTests(TestCase):
	def test_user_save_normalizes_email_and_phone(self):
		user = User.objects.create_user(
			email=' Cliente@Biobrassica.PT ',
			username='cliente-normalizado',
			password='S3guraPass123',
			phone='+351 912 345 678',
		)

		self.assertEqual(user.email, 'cliente@biobrassica.pt')
		self.assertEqual(user.phone, '912 345 678')

	def test_user_save_rejects_invalid_phone(self):
		with self.assertRaises(ValidationError) as ctx:
			User.objects.create_user(
				email='cliente-invalido@biobrassica.pt',
				username='cliente-invalido',
				password='S3guraPass123',
				phone='12345',
			)

		self.assertIn('phone', ctx.exception.message_dict)


class AddressValidationTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			email='moradas@biobrassica.pt',
			username='moradas',
			password='S3guraPass123',
		)

	def test_address_full_clean_normalizes_country_code(self):
		address = Address(
			user=self.user,
			name='Casa',
			line1='Rua das Flores 10',
			city='Braga',
			postal_code='4700-111',
			country='pt',
		)

		address.full_clean()

		self.assertEqual(address.country, Address.Country.PORTUGAL)

	def test_address_full_clean_rejects_invalid_country(self):
		address = Address(
			user=self.user,
			name='Casa',
			line1='Rua das Flores 10',
			city='Braga',
			postal_code='4700-111',
			country='ES',
		)

		with self.assertRaises(ValidationError) as ctx:
			address.full_clean()

		self.assertIn('country', ctx.exception.message_dict)

	def test_address_full_clean_rejects_invalid_postal_code(self):
		address = Address(
			user=self.user,
			name='Casa',
			line1='Rua das Flores 10',
			city='Braga',
			postal_code='4700111',
		)

		with self.assertRaises(ValidationError) as ctx:
			address.full_clean()

		self.assertIn('postal_code', ctx.exception.message_dict)


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
			name='Azeite bio',
			brand='Biobrassica',
			description='Azeite virgem extra biológico.',
			allergens='Sem alergénios declarados.',
			price='9.50',
			quantity='750 ml',
			stock=10,
			is_active=True,
			allow_shipping=True,
			bio_code='PT-BIO-03',
			image=SimpleUploadedFile('azeite.gif', GIF_BYTES, content_type='image/gif'),
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
		# Anonymous carts no longer exist; this scenario is obsolete.
		self.skipTest('Anonymous carts removed; cart now requires login.')


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
		self.assertEqual(self.user.phone, '912 345 678')
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
		self.staff_user = User.objects.create_superuser(
			email='staff@biobrassica.pt',
			username='staff',
			password='testpass123',
		)

		self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
		self.client.force_login(self.admin_user)

	def test_user_admin_changelist_only_lists_customers(self):
		response = self.client.get(reverse('admin:accounts_user_changelist'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.customer.email)
		self.assertContains(response, self.customer_without_default.email)
		self.assertNotContains(response, self.staff_user.email)

	def test_user_change_form_is_flat_and_without_permission_fields(self):
		response = self.client.get(reverse('admin:accounts_user_change', args=[self.customer.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'name="email"', html=False)
		self.assertContains(response, 'name="phone"', html=False)
		self.assertContains(response, 'name="nif"', html=False)
		self.assertNotContains(response, 'Resumo do cliente')
		self.assertNotContains(response, 'name="is_staff"', html=False)
		self.assertNotContains(response, 'name="is_superuser"', html=False)

	def test_staff_admin_uses_separate_url(self):
		response = self.client.get(reverse('admin:accounts_staffaccount_changelist'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.staff_user.email)
		self.assertNotContains(response, self.customer.email)

	def test_address_change_form_is_flat(self):
		response = self.client.get(reverse('admin:accounts_address_change', args=[self.address.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'name="line1"', html=False)
		self.assertContains(response, 'name="country"', html=False)
		self.assertContains(response, 'Portugal')
		self.assertNotContains(response, 'Resumo da morada')

	def test_user_admin_queryset_excludes_staff(self):
		request = RequestFactory().get(reverse('admin:accounts_user_changelist'), HTTP_HOST='admin.lvh.me')
		request.user = self.admin_user
		user_admin = admin.site._registry[User]
		queryset = user_admin.get_queryset(request)

		self.assertTrue(queryset.filter(pk=self.customer.pk).exists())
		self.assertFalse(queryset.filter(pk=self.staff_user.pk).exists())


class ResetAdminPasswordCommandTests(TestCase):
	def test_reset_admin_password_updates_staff_account(self):
		user = User.objects.create_user(
			email='admin-reset@biobrassica.pt',
			username='admin-reset',
			password='OldPass123!',
			is_staff=True,
		)
		stdout = StringIO()

		with patch('apps.accounts.management.commands.reset_admin_password.getpass.getpass', side_effect=['NovaPass123!', 'NovaPass123!']):
			call_command('reset_admin_password', user.email, stdout=stdout)

		user.refresh_from_db()
		self.assertTrue(user.check_password('NovaPass123!'))
		self.assertIn(f'Password updated for {user.email}.', stdout.getvalue())

	def test_reset_admin_password_rejects_non_staff_account(self):
		user = User.objects.create_user(
			email='cliente-reset@biobrassica.pt',
			username='cliente-reset',
			password='OldPass123!',
			is_staff=False,
		)

		with self.assertRaises(CommandError):
			call_command('reset_admin_password', user.email)
