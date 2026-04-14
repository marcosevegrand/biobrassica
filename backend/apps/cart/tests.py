from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.cart.models import Cart, CartItem
from apps.cart.services import get_cart_items_queryset, get_cart_summary, merge_anonymous_cart_into_user_cart
from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation


@override_settings(ROOT_URLCONF='config.urls_shop')
class CartViewTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(slug='mercearia')
		CategoryTranslation.objects.create(
			category=self.category,
			language='pt',
			name='Mercearia',
			description='Categoria de mercearia',
		)
		self.product = self._create_product('azeite-bio', 'Azeite bio', Decimal('9.50'))

	def _create_product(self, slug, name, price):
		product = Product.objects.create(
			category=self.category,
			slug=slug,
			brand='Biobrassica',
			price=price,
			quantity='1 un',
			stock=25,
			is_active=True,
			allow_shipping=True,
			bio_code=f'PT-BIO-{Product.objects.count() + 3:02d}',
		)
		ProductTranslation.objects.create(
			product=product,
			language='pt',
			name=name,
			description=f'{name} descrição',
			allergens='Sem alergénios declarados.',
			ingredients=f'{name} ingredientes',
		)
		return product

	def test_add_to_cart_creates_anonymous_cart(self):
		response = self.client.post(
			reverse('cart:add', kwargs={'product_id': self.product.pk}),
			HTTP_HOST='loja.lvh.me',
		)

		cart = Cart.objects.get(session_key=self.client.session.session_key)
		item = CartItem.objects.get(cart=cart, product=self.product)

		self.assertRedirects(response, reverse('cart:detail'))
		self.assertIsNone(cart.user)
		self.assertEqual(item.quantity, 1)

	def test_repeated_add_increments_existing_item_quantity(self):
		self.client.post(
			reverse('cart:add', kwargs={'product_id': self.product.pk}),
			{'quantity': 2},
			HTTP_HOST='loja.lvh.me',
		)
		self.client.post(
			reverse('cart:add', kwargs={'product_id': self.product.pk}),
			{'quantity': 3},
			HTTP_HOST='loja.lvh.me',
		)

		item = CartItem.objects.get(product=self.product)
		self.assertEqual(item.quantity, 5)

	def test_add_to_cart_rejects_malformed_quantity(self):
		response = self.client.post(
			reverse('cart:add', kwargs={'product_id': self.product.pk}),
			{'quantity': 'abc'},
			HTTP_HOST='loja.lvh.me',
		)

		self.assertRedirects(response, reverse('cart:detail'))
		self.assertFalse(CartItem.objects.filter(product=self.product).exists())

	def test_repeated_add_caps_quantity_at_available_stock(self):
		self.product.stock = 4
		self.product.save(update_fields=['stock'])

		self.client.post(
			reverse('cart:add', kwargs={'product_id': self.product.pk}),
			{'quantity': 3},
			HTTP_HOST='loja.lvh.me',
		)
		self.client.post(
			reverse('cart:add', kwargs={'product_id': self.product.pk}),
			{'quantity': 3},
			HTTP_HOST='loja.lvh.me',
		)

		item = CartItem.objects.get(product=self.product)
		self.assertEqual(item.quantity, 4)

	def test_update_quantity_caps_value_at_available_stock(self):
		session = self.client.session
		session.save()
		cart = Cart.objects.create(session_key=session.session_key)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
		self.product.stock = 1
		self.product.save(update_fields=['stock'])

		response = self.client.post(
			reverse('cart:update', kwargs={'item_id': item.pk}),
			{'quantity': 5},
			HTTP_HOST='loja.lvh.me',
		)

		item.refresh_from_db()
		self.assertRedirects(response, reverse('cart:detail'))
		self.assertEqual(item.quantity, 1)

	def test_update_quantity_to_zero_deletes_item(self):
		session = self.client.session
		session.save()
		cart = Cart.objects.create(session_key=session.session_key)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

		response = self.client.post(
			reverse('cart:update', kwargs={'item_id': item.pk}),
			{'quantity': 0},
			HTTP_HOST='loja.lvh.me',
		)

		self.assertRedirects(response, reverse('cart:detail'))
		self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

	def test_update_quantity_rejects_malformed_value(self):
		session = self.client.session
		session.save()
		cart = Cart.objects.create(session_key=session.session_key)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

		response = self.client.post(
			reverse('cart:update', kwargs={'item_id': item.pk}),
			{'quantity': 'abc'},
			HTTP_HOST='loja.lvh.me',
		)

		item.refresh_from_db()
		self.assertRedirects(response, reverse('cart:detail'))
		self.assertEqual(item.quantity, 2)

	def test_remove_from_cart_deletes_item(self):
		session = self.client.session
		session.save()
		cart = Cart.objects.create(session_key=session.session_key)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)

		response = self.client.post(
			reverse('cart:remove', kwargs={'item_id': item.pk}),
			HTTP_HOST='loja.lvh.me',
		)

		self.assertRedirects(response, reverse('cart:detail'))
		self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

	def test_htmx_update_returns_smaller_fragments_and_syncs_summary(self):
		session = self.client.session
		session.save()
		cart = Cart.objects.create(session_key=session.session_key)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

		response = self.client.post(
			reverse('cart:update', kwargs={'item_id': item.pk}),
			{'quantity': 3},
			HTTP_HOST='loja.lvh.me',
			HTTP_HX_REQUEST='true',
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f'id="cart-item-{item.pk}"', html=False)
		self.assertContains(response, 'id="cart-summary"', html=False)
		self.assertContains(response, 'id="cart-count"', html=False)
		self.assertContains(response, 'id="cart-popup"', html=False)
		self.assertNotContains(response, 'id="cart-items"', html=False)
		self.assertEqual(response.headers.get('HX-Reswap'), None)

	def test_htmx_update_invalid_quantity_returns_cart_message(self):
		session = self.client.session
		session.save()
		cart = Cart.objects.create(session_key=session.session_key)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

		response = self.client.post(
			reverse('cart:update', kwargs={'item_id': item.pk}),
			{'quantity': 'abc'},
			HTTP_HOST='loja.lvh.me',
			HTTP_HX_REQUEST='true',
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'id="cart-messages"', html=False)
		self.assertContains(response, 'Indique uma quantidade válida.')
		self.assertContains(response, f'id="cart-item-{item.pk}"', html=False)

	def test_htmx_remove_returns_empty_state_and_hides_summary(self):
		session = self.client.session
		session.save()
		cart = Cart.objects.create(session_key=session.session_key)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)

		response = self.client.post(
			reverse('cart:remove', kwargs={'item_id': item.pk}),
			HTTP_HOST='loja.lvh.me',
			HTTP_HX_REQUEST='true',
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'O seu carrinho está vazio.')
		self.assertContains(response, 'id="cart-summary"', html=False)
		self.assertEqual(response.headers.get('HX-Retarget'), '#cart-items')
		self.assertEqual(response.headers.get('HX-Reswap'), 'innerHTML')
		self.assertNotContains(response, 'Finalizar encomenda')

	def test_htmx_remove_deletes_row_when_cart_still_has_other_items(self):
		second_product = self._create_product('grao-bio', 'Grão bio', Decimal('4.25'))
		session = self.client.session
		session.save()
		cart = Cart.objects.create(session_key=session.session_key)
		item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
		CartItem.objects.create(cart=cart, product=second_product, quantity=1)

		response = self.client.post(
			reverse('cart:remove', kwargs={'item_id': item.pk}),
			HTTP_HOST='loja.lvh.me',
			HTTP_HX_REQUEST='true',
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.headers.get('HX-Reswap'), 'delete')
		self.assertEqual(response.headers.get('HX-Retarget'), None)
		self.assertContains(response, 'id="cart-summary"', html=False)

	def test_cart_total_and_item_count_aggregate_all_items(self):
		second_product = self._create_product('grao-bio', 'Grão bio', Decimal('4.25'))
		cart = Cart.objects.create(session_key='aggregate-session')
		CartItem.objects.create(cart=cart, product=self.product, quantity=2)
		CartItem.objects.create(cart=cart, product=second_product, quantity=3)

		self.assertEqual(cart.item_count, 5)
		self.assertEqual(cart.total, Decimal('31.75'))

	def test_cart_summary_and_totals_ignore_inactive_products(self):
		inactive_product = self._create_product('sumo-inativo', 'Sumo inativo', Decimal('3.50'))
		inactive_product.is_active = False
		inactive_product.save(update_fields=['is_active'])

		cart = Cart.objects.create(session_key='inactive-summary-session')
		CartItem.objects.create(cart=cart, product=self.product, quantity=2)
		CartItem.objects.create(cart=cart, product=inactive_product, quantity=4)

		summary = get_cart_summary(cart)

		self.assertEqual(summary['cart_item_count'], 2)
		self.assertEqual(summary['cart_total'], Decimal('19.00'))
		self.assertEqual(cart.item_count, 2)
		self.assertEqual(cart.total, Decimal('19.00'))

	def test_cart_queryset_excludes_inactive_products(self):
		inactive_product = self._create_product('feijao-inativo', 'Feijão inativo', Decimal('2.00'))
		cart = Cart.objects.create(session_key='inactive-queryset-session')
		CartItem.objects.create(cart=cart, product=self.product, quantity=1)
		CartItem.objects.create(cart=cart, product=inactive_product, quantity=1)

		inactive_product.is_active = False
		inactive_product.save(update_fields=['is_active'])

		items = list(get_cart_items_queryset(cart))

		self.assertEqual(len(items), 1)
		self.assertEqual(items[0].product_id, self.product.pk)

	def test_merge_anonymous_cart_rolls_back_if_delete_fails(self):
		user_model = get_user_model()
		user = cast(Any, user_model._default_manager).create_user(
			email='cliente@biobrassica.pt',
			username='cliente',
			password='S3guraPass123',
		)
		user_cart = Cart.objects.create(user=user)
		anon_cart = Cart.objects.create(session_key='merge-session')
		CartItem.objects.create(cart=user_cart, product=self.product, quantity=1)
		CartItem.objects.create(cart=anon_cart, product=self.product, quantity=2)

		request = SimpleNamespace(session=SimpleNamespace(session_key='merge-session'))

		with patch('apps.cart.services.Cart.delete', side_effect=RuntimeError('boom')):
			with self.assertRaises(RuntimeError):
				merge_anonymous_cart_into_user_cart(request, user)

		self.assertTrue(Cart.objects.filter(pk=anon_cart.pk).exists())
		self.assertEqual(CartItem.objects.get(cart=user_cart, product=self.product).quantity, 1)
		self.assertEqual(CartItem.objects.get(cart=anon_cart, product=self.product).quantity, 2)

	def test_merge_anonymous_cart_caps_combined_quantities_at_stock(self):
		user_model = get_user_model()
		user = cast(Any, user_model._default_manager).create_user(
			email='cliente2@biobrassica.pt',
			username='cliente2',
			password='S3guraPass123',
		)
		user_cart = Cart.objects.create(user=user)
		anon_cart = Cart.objects.create(session_key='merge-session-2')
		CartItem.objects.create(cart=user_cart, product=self.product, quantity=2)
		CartItem.objects.create(cart=anon_cart, product=self.product, quantity=4)
		self.product.stock = 3
		self.product.save(update_fields=['stock'])

		request = SimpleNamespace(session=SimpleNamespace(session_key='merge-session-2'))
		merge_anonymous_cart_into_user_cart(request, user)

		self.assertFalse(Cart.objects.filter(pk=anon_cart.pk).exists())
		self.assertEqual(CartItem.objects.get(cart=user_cart, product=self.product).quantity, 3)


class CartConstraintTests(TestCase):
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
			quantity='1 un',
			stock=25,
			is_active=True,
			allow_shipping=True,
			bio_code='PT-BIO-03',
		)
		ProductTranslation.objects.create(
			product=self.product,
			language='pt',
			name='Azeite bio',
			description='Azeite bio descrição',
			allergens='Sem alergénios declarados.',
			ingredients='Azeite bio ingredientes',
		)

	def test_duplicate_non_empty_session_key_is_rejected(self):
		Cart.objects.create(session_key='session-123')

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				Cart.objects.create(session_key='session-123')

	def test_blank_or_null_session_key_can_repeat(self):
		Cart.objects.create(session_key='')
		Cart.objects.create(session_key='')
		Cart.objects.create(session_key=None)
		Cart.objects.create(session_key=None)

		self.assertEqual(Cart.objects.filter(session_key='').count(), 2)
		self.assertEqual(Cart.objects.filter(session_key__isnull=True).count(), 2)

	def test_duplicate_product_in_same_cart_is_rejected(self):
		cart = Cart.objects.create(session_key='session-abc')
		CartItem.objects.create(cart=cart, product=self.product, quantity=1)

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				CartItem.objects.create(cart=cart, product=self.product, quantity=2)


class CartSummaryTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(slug='mercearia')
		CategoryTranslation.objects.create(
			category=self.category,
			language='pt',
			name='Mercearia',
			description='Categoria de mercearia',
		)
		self.first_product = Product.objects.create(
			category=self.category,
			slug='azeite-bio',
			brand='Biobrassica',
			price=Decimal('9.50'),
			quantity='1 un',
			stock=25,
			is_active=True,
			allow_shipping=True,
			bio_code='PT-BIO-03',
		)
		ProductTranslation.objects.create(
			product=self.first_product,
			language='pt',
			name='Azeite bio',
			description='Azeite bio descrição',
			allergens='Sem alergénios declarados.',
			ingredients='Azeite bio ingredientes',
		)
		self.second_product = Product.objects.create(
			category=self.category,
			slug='grao-bio',
			brand='Biobrassica',
			price=Decimal('4.25'),
			quantity='1 un',
			stock=25,
			is_active=True,
			allow_shipping=True,
			bio_code='PT-BIO-04',
		)
		ProductTranslation.objects.create(
			product=self.second_product,
			language='pt',
			name='Grão bio',
			description='Grão bio descrição',
			allergens='Sem alergénios declarados.',
			ingredients='Grão bio ingredientes',
		)

	def test_get_cart_summary_returns_total_count_and_limited_preview(self):
		cart = Cart.objects.create(session_key='summary-session')
		CartItem.objects.create(cart=cart, product=self.first_product, quantity=2)
		CartItem.objects.create(cart=cart, product=self.second_product, quantity=3)

		summary = get_cart_summary(cart, preview_limit=1)

		self.assertEqual(summary['cart_item_count'], 5)
		self.assertEqual(summary['cart_total'], Decimal('31.75'))
		self.assertEqual(len(summary['cart_preview_items']), 1)

	def test_get_cart_summary_handles_missing_cart(self):
		summary = get_cart_summary(None)

		self.assertEqual(summary['cart_item_count'], 0)
		self.assertEqual(summary['cart_preview_items'], [])
		self.assertEqual(summary['cart_total'], Decimal('0'))
