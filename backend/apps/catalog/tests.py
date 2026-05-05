from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django import forms

from apps.accounts.models import User
from apps.catalog.forms import ProductAdminForm
from apps.catalog.models import Category, CategoryPosition, CategoryTranslation, Location, Product, ProductTranslation
from apps.catalog.querysets import display_product_queryset


GIF_BYTES = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


def make_image(name='imagem.gif'):
    return SimpleUploadedFile(name, GIF_BYTES, content_type='image/gif')


class CatalogModelTests(TestCase):
    def test_category_uses_name_as_primary_pt_field(self):
        category = Category.objects.create(name='Mercearia Fresca')

        self.assertEqual(category.slug, 'mercearia-fresca')
        self.assertEqual(category.get_name('pt'), 'Mercearia Fresca')

    def test_category_accepts_legacy_order_input_but_stores_position_externally(self):
        category = Category.objects.create(name='Cabazes', order=3)

        self.assertEqual(category.order, 3)
        self.assertTrue(CategoryPosition.objects.filter(category=category, position=3).exists())

    def test_product_queryset_hides_products_without_translation_in_requested_language(self):
        category = Category.objects.create(name='Mercearia')
        product = Product.objects.create(
            category=category,
            name='Azeite Bio',
            brand='Biobrassica',
            bio_code='PT-BIO-03',
            description='Azeite virgem extra biológico.',
            allergens='Sem alergénios declarados.',
            price=Decimal('9.50'),
            quantity='750 ml',
            stock=5,
            is_active=True,
            allow_shipping=True,
            image=make_image('azeite.gif'),
        )
        ProductTranslation.objects.create(
            product=product,
            language='en',
            name='Organic Olive Oil',
            description='Organic extra virgin olive oil.',
            allergens='No declared allergens.',
        )

        self.assertEqual(list(display_product_queryset(lang='en').values_list('pk', flat=True)), [product.pk])
        self.assertFalse(display_product_queryset(lang='fr').filter(pk=product.pk).exists())

    def test_active_product_requires_image(self):
        category = Category.objects.create(name='Mercearia')
        product = Product(
            category=category,
            name='Arroz Bio',
            brand='Biobrassica',
            bio_code='PT-BIO-04',
            description='Arroz biológico.',
            allergens='Sem alergénios declarados.',
            price=Decimal('4.50'),
            quantity='1 kg',
            stock=10,
            is_active=True,
            allow_shipping=True,
        )

        with self.assertRaises(ValidationError) as ctx:
            product.save()

        self.assertIn('O produto precisa de uma imagem.', ctx.exception.messages)

    def test_active_product_with_pickup_requires_locations(self):
        category = Category.objects.create(name='Mercearia')
        product = Product.objects.create(
            category=category,
            name='Massa Bio',
            brand='Biobrassica',
            bio_code='PT-BIO-05',
            description='Massa biológica.',
            allergens='Contém glúten.',
            price=Decimal('3.20'),
            quantity='500 g',
            stock=8,
            is_active=False,
            allow_pickup=True,
            image=make_image('massa.gif'),
        )
        product.is_active = True

        with self.assertRaises(ValidationError) as ctx:
            product.save()

        self.assertIn('Selecione pelo menos uma localização de recolha.', ctx.exception.message_dict['pickup_locations'])


class ProductAdminFormTests(TestCase):
    def test_product_admin_form_uses_pickup_location_checkboxes(self):
        category = Category.objects.create(name='Mercearia')
        location = Location.objects.create(name='Loja Braga', is_active=True, order=1)

        form = ProductAdminForm()

        self.assertIsInstance(form.fields['pickup_locations'].widget, forms.CheckboxSelectMultiple)
        self.assertIn(location.pk, list(form.fields['pickup_locations'].queryset.values_list('pk', flat=True)))
        self.assertIn(category.pk, list(form.fields['category'].queryset.values_list('pk', flat=True)))


@override_settings(ROOT_URLCONF='config.urls_admin')
class CatalogAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='testpass123',
        )
        self.category = Category.objects.create(name='Mercearia')
        self.location = Location.objects.create(name='Loja Braga', is_active=True, order=1)
        self.product = Product.objects.create(
            category=self.category,
            name='Azeite Bio',
            brand='Biobrassica',
            bio_code='PT-BIO-03',
            description='Azeite virgem extra biológico.',
            allergens='Sem alergénios declarados.',
            price=Decimal('9.50'),
            quantity='750 ml',
            stock=5,
            is_active=True,
            allow_shipping=True,
            allow_pickup=True,
            image=make_image('admin-azeite.gif'),
        )
        self.product.pickup_locations.add(self.location)
        self.client.defaults['HTTP_HOST'] = 'admin.lvh.me'
        self.client.force_login(self.admin_user)

    def test_category_admin_change_form_is_flat(self):
        response = self.client.get(reverse('admin:catalog_category_change', args=[self.category.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="name"', html=False)
        self.assertContains(response, 'name="featured_message"', html=False)
        self.assertNotContains(response, 'Checklist da categoria')
        self.assertNotContains(response, 'Publicação')

    def test_product_admin_change_form_uses_base_pt_fields_and_no_gallery_inline(self):
        response = self.client.get(reverse('admin:catalog_product_change', args=[self.product.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="name"', html=False)
        self.assertContains(response, 'name="description"', html=False)
        self.assertContains(response, 'name="allergens"', html=False)
        self.assertContains(response, self.location.name)
        self.assertContains(response, 'Adicionar tradução EN/FR')
        self.assertNotContains(response, 'name="quantity_value"', html=False)
        self.assertNotContains(response, 'Imagens do produto')
        self.assertNotContains(response, 'Checklist de publicação')

    def test_product_changelist_uses_portuguese_add_and_search_text(self):
        response = self.client.get(reverse('admin:catalog_product_changelist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adicionar produto')
        self.assertContains(response, 'Pesquisar')
        self.assertNotContains(response, 'Add produto')
        self.assertNotContains(response, 'Search apps and models...')


@override_settings(ROOT_URLCONF='config.urls_shop')
class CatalogAnonymousCartTests(TestCase):
    def test_htmx_add_to_cart_redirects_anonymous_user_to_login(self):
        category = Category.objects.create(name='Mercearia')
        product = Product.objects.create(
            category=category,
            name='Azeite Bio',
            brand='Biobrassica',
            bio_code='PT-BIO-03',
            description='Azeite virgem extra biológico.',
            allergens='Sem alergénios declarados.',
            price=Decimal('9.50'),
            quantity='750 ml',
            stock=5,
            is_active=True,
            allow_shipping=True,
            image=make_image('anonymous-azeite.gif'),
        )
        response = self.client.post(
            reverse('cart:add', args=[product.pk]),
            {'quantity': '1'},
            HTTP_HOST='loja.lvh.me',
            HTTP_HX_REQUEST='true',
            HTTP_HX_CURRENT_URL='http://loja.lvh.me/pt/produtos/',
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response['HX-Redirect'], f"{reverse('accounts:login')}?next=/pt/produtos/")
