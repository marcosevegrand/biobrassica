from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import admin
from typing import Any, cast
from django.utils import translation

from apps.catalog.models import Category, CategoryTranslation, DeliveryMethod, Location, Product, ProductImage, ProductTranslation


GIF_BYTES = (
	b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
	b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


class ProductModelTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(slug='mercearia')
		CategoryTranslation.objects.create(
			category=self.category,
			language='pt',
			name='Mercearia',
			description='Categoria mercearia',
		)

	def test_product_requires_required_attributes(self):
		product = Product(
			category=self.category,
			slug='produto-incompleto',
			price='3.50',
			stock=10,
		)

		with self.assertRaises(ValidationError) as ctx:
			product.full_clean()

		self.assertIn('quantity', ctx.exception.message_dict)
		self.assertIn('bio_code', ctx.exception.message_dict)
		self.assertIn('brand', ctx.exception.message_dict)

	def test_translation_requires_description(self):
		product = Product.objects.create(
			category=self.category,
			slug='produto-completo',
			brand='Casa do Tahini',
			price='5.90',
			quantity='250 g',
			stock=5,
			bio_code='PT-BIO-03',
		)

		translation = ProductTranslation(
			product=product,
			language='pt',
			name='Tahini',
			description='',
			allergens='',
			ingredients='',
		)

		with self.assertRaises(ValidationError) as ctx:
			translation.full_clean()

		self.assertIn('description', ctx.exception.message_dict)
		self.assertIn('allergens', ctx.exception.message_dict)
		self.assertIn('ingredients', ctx.exception.message_dict)

	def test_active_product_requires_stock_primary_image_and_location(self):
		product = Product.objects.create(
			category=self.category,
			slug='produto-ativo-invalido',
			brand='Casa do Tahini',
			price='5.90',
			quantity='250 g',
			stock=1,
			bio_code='PT-BIO-03',
			is_active=False,
		)
		ProductTranslation.objects.create(
			product=product,
			language='pt',
			name='Tahini',
			description='Descrição',
			allergens='Sésamo',
			ingredients='Sementes de sésamo',
		)
		ProductImage.objects.create(
			product=product,
			image=SimpleUploadedFile('produto.gif', GIF_BYTES, content_type='image/gif'),
			alt_text='Tahini',
			is_primary=True,
		)

		product.stock = 0
		product.is_active = True

		with self.assertRaises(ValidationError) as ctx:
			product.full_clean()

		self.assertIn('O produto precisa de stock para estar ativo.', ctx.exception.messages)
		self.assertIn('O produto precisa de pelo menos uma localização para levantamento.', ctx.exception.messages)


@override_settings(ROOT_URLCONF='config.urls_shop')
class ProductDetailViewTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(slug='despensa')
		CategoryTranslation.objects.create(
			category=self.category,
			language='pt',
			name='Despensa',
			description='Produtos de despensa',
		)
		self.product = Product.objects.create(
			category=self.category,
			slug='massa-integral-bio',
			brand='Biobrassica',
			price='2.49',
			quantity='500 g',
			stock=12,
			bio_code='PT-BIO-03',
		)
		ProductTranslation.objects.create(
			product=self.product,
			language='pt',
			name='Massa integral bio',
			description='Massa de trigo duro integral com textura firme.',
			allergens='Contém glúten',
			ingredients='Farinha integral de trigo duro bio.',
		)
		ProductImage.objects.create(
			product=self.product,
			image=SimpleUploadedFile('produto.gif', GIF_BYTES, content_type='image/gif'),
			alt_text='Massa integral bio',
			is_primary=True,
		)

	def test_product_detail_shows_required_product_attributes(self):
		response = self.client.get(
			reverse('catalog:product_detail', kwargs={'slug': self.product.slug}),
			HTTP_HOST='loja.lvh.me',
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Massa integral bio')
		self.assertContains(response, 'Biobrassica')
		self.assertContains(response, 'Contém glúten')
		self.assertContains(response, 'Farinha integral de trigo duro bio.')
		self.assertContains(response, '500 g')
		self.assertContains(response, 'PT-BIO-03')

	def test_product_detail_stays_within_expected_query_budget(self):
		with CaptureQueriesContext(connection) as queries:
			response = self.client.get(
				reverse('catalog:product_detail', kwargs={'slug': self.product.slug}),
				HTTP_HOST='loja.lvh.me',
			)
			self.assertEqual(response.status_code, 200)

		self.assertLessEqual(len(queries), 10)


class CatalogConstraintTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(slug='mercearia')
		CategoryTranslation.objects.create(
			category=self.category,
			language='pt',
			name='Mercearia',
			description='Categoria mercearia',
		)
		self.product = Product.objects.create(
			category=self.category,
			slug='produto-bio',
			brand='Biobrassica',
			price='5.90',
			quantity='250 g',
			stock=5,
			bio_code='PT-BIO-03',
		)

	def test_duplicate_category_translation_language_is_rejected(self):
		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				CategoryTranslation.objects.create(
					category=self.category,
					language='pt',
					name='Mercearia duplicada',
					description='Duplicada',
				)

	def test_duplicate_product_translation_language_is_rejected(self):
		ProductTranslation.objects.create(
			product=self.product,
			language='pt',
			name='Tahini',
			description='Descrição',
			allergens='Sésamo',
			ingredients='Sementes de sésamo',
		)

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				ProductTranslation.objects.create(
					product=self.product,
					language='pt',
					name='Tahini duplicado',
					description='Descrição duplicada',
					allergens='Sésamo',
					ingredients='Sementes de sésamo',
				)

	def test_duplicate_primary_product_image_is_rejected(self):
		ProductImage.objects.create(
			product=self.product,
			image=SimpleUploadedFile('primary-1.gif', GIF_BYTES, content_type='image/gif'),
			alt_text='Primeira',
			is_primary=True,
		)

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				ProductImage.objects.create(
					product=self.product,
					image=SimpleUploadedFile('primary-2.gif', GIF_BYTES, content_type='image/gif'),
					alt_text='Segunda',
					is_primary=True,
				)


@override_settings(ROOT_URLCONF='config.urls_shop')
class CatalogListViewTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(slug='mercearia')
		CategoryTranslation.objects.create(
			category=self.category,
			language='pt',
			name='Mercearia',
			description='Categoria mercearia',
		)
		for index in range(13):
			product = Product.objects.create(
				category=self.category,
				slug=f'produto-{index}',
				brand='Biobrassica',
				price='3.50',
				quantity='250 g',
				stock=10,
				bio_code=f'PT-BIO-{index + 3:02d}',
			)
			ProductTranslation.objects.create(
				product=product,
				language='pt',
				name=f'Produto {index}',
				description='Descrição do produto',
				allergens='Sem alergénios',
				ingredients='Ingredientes do produto',
			)

	def test_product_list_paginates_and_preserves_filters(self):
		response = self.client.get(
			reverse('catalog:product_list'),
			{'categoria': self.category.slug, 'q': 'Produto', 'page': 2},
			HTTP_HOST='loja.lvh.me',
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context['is_paginated'])
		self.assertEqual(response.context['page_obj'].number, 2)
		self.assertEqual(response.context['pagination_query'], f'categoria={self.category.slug}&q=Produto')
		self.assertEqual(len(response.context['products']), 1)

	def test_product_list_stays_within_expected_query_budget(self):
		with CaptureQueriesContext(connection) as queries:
			response = self.client.get(
				reverse('catalog:product_list'),
				HTTP_HOST='loja.lvh.me',
				)
			self.assertEqual(response.status_code, 200)

		self.assertLessEqual(len(queries), 10)

	def test_product_list_uses_pt_fallback_when_requested_language_is_missing(self):
		with translation.override('en'):
			response = self.client.get(
				reverse('catalog:product_list'),
				HTTP_HOST='loja.lvh.me',
			)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Produto 12')

	def test_product_list_search_uses_pt_fallback_when_requested_language_is_missing(self):
		product = Product.objects.create(
			category=self.category,
			slug='produto-so-pt',
			brand='Biobrassica',
			price='4.20',
			quantity='200 g',
			stock=10,
			bio_code='PT-BIO-99',
		)
		ProductTranslation.objects.create(
			product=product,
			language='pt',
			name='Pesquisa PT',
			description='Encontrado via fallback',
			allergens='Sem alergénios',
			ingredients='Ingredientes PT',
		)

		with translation.override('en'):
			response = self.client.get(
				reverse('catalog:product_list'),
				{'q': 'Pesquisa'},
				HTTP_HOST='loja.lvh.me',
			)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Pesquisa PT')


@override_settings(ROOT_URLCONF='config.urls_admin')
class ProductAdminWorkflowTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.admin_user = cast(Any, user_model._default_manager).create_superuser(
			email='admin@example.com',
			username='admin',
			password='testpass123',
		)
		self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
		self.client.force_login(self.admin_user)
		self.category = Category.objects.create(slug='mercearia')
		CategoryTranslation.objects.create(
			category=self.category,
			language='pt',
			name='Mercearia',
			description='Categoria mercearia',
		)
		self.product = Product.objects.create(
			category=self.category,
			slug='produto-admin',
			brand='Biobrassica',
			price='5.90',
			quantity='250 g',
			stock=2,
			bio_code='PT-BIO-03',
		)
		ProductTranslation.objects.create(
			product=self.product,
			language='pt',
			name='Produto admin',
			description='Descrição',
			allergens='Sem alergénios',
			ingredients='Ingredientes',
		)

	def test_product_admin_changelist_shows_workflow_cards(self):
		response = self.client.get(reverse('admin:catalog_product_changelist'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Sem stock')
		self.assertContains(response, 'Baixo stock')
		self.assertContains(response, 'Sem imagem principal')
		self.assertContains(response, 'Prontos a reativar')

	def test_product_change_form_shows_publication_checklist(self):
		response = self.client.get(reverse('admin:catalog_product_change', args=[self.product.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Checklist de publicação')
		self.assertContains(response, 'Plano de reposição')
		self.assertContains(response, 'Imagens do produto')
		self.assertContains(response, 'Fila de reposição')
		self.assertContains(response, 'A galeria começa vazia')

	def test_product_add_form_starts_without_prefilled_inline_entries(self):
		response = self.client.get(reverse('admin:catalog_product_add'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Adicione apenas as traduções necessárias')
		self.assertContains(response, 'A galeria começa vazia')
		self.assertContains(response, 'Nenhuma tradução adicionada')
		self.assertContains(response, 'Galeria vazia')
		self.assertContains(response, 'Adicionar tradução')
		self.assertContains(response, 'Adicionar imagem')
		self.assertNotContains(response, 'name="translations-0-language"', html=False)
		self.assertNotContains(response, 'name="images-0-image"', html=False)
		self.assertContains(response, 'class="add-row', html=False)
		self.assertContains(response, 'class="formset"', html=False)
		self.assertContains(response, 'class="form-group', html=False)

	def test_out_of_stock_product_can_be_deactivated_from_change_form(self):
		self.product.stock = 0
		self.product.save(update_fields=['stock'])

		response = self.client.post(
			reverse('admin:catalog_product_change', args=[self.product.pk]),
			{'_deactivate_until_restock': '1'},
			follow=True,
		)

		self.product.refresh_from_db()

		self.assertEqual(response.status_code, 200)
		self.assertFalse(self.product.is_active)
		self.assertContains(response, 'Produto desativado até reposição.')

	def test_product_admin_does_not_allow_is_active_inline_edit(self):
		product_admin = admin.site._registry[Product]
		self.assertNotIn('is_active', product_admin.list_editable)


@override_settings(ROOT_URLCONF='config.urls_admin')
class CatalogSupportAdminWorkflowTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.admin_user = cast(Any, user_model._default_manager).create_superuser(
			email='admin@example.com',
			username='admin',
			password='testpass123',
		)
		self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
		self.client.force_login(self.admin_user)
		self.location = Location.objects.create(name='Loja Braga', address='Rua A', phone='253 271 187')
		self.delivery = DeliveryMethod.objects.create(name='Levantamento', description='Entrega em loja')
		self.category = Category.objects.create(slug='mercearia')
		CategoryTranslation.objects.create(
			category=self.category,
			language='pt',
			name='Mercearia',
			description='Categoria base',
		)

	def test_category_admin_shows_workflow_cards(self):
		response = self.client.get(reverse('admin:catalog_category_changelist'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Em destaque')
		self.assertContains(response, 'Sem produtos ativos')

	def test_location_admin_shows_workflow_cards(self):
		response = self.client.get(reverse('admin:catalog_location_changelist'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Lojas ativas')
		self.assertContains(response, 'Sem mapa')

	def test_delivery_admin_shows_workflow_cards(self):
		response = self.client.get(reverse('admin:catalog_deliverymethod_changelist'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Ativos')
		self.assertContains(response, 'Sem descrição')
