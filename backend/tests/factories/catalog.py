# pyright: reportPrivateImportUsage=false, reportIncompatibleVariableOverride=false

from decimal import Decimal
from typing import Any, cast

import factory
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation


def make_test_image(name='produto.jpg'):
    return SimpleUploadedFile(
        name,
        (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00' + b'\x08' * 64 +
            b'\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01'
            b'\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08'
            b'\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xd2\xcf \xff\xd9'
        ),
        content_type='image/jpeg',
    )


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        skip_postgeneration_save = True

    slug = factory.Sequence(lambda n: f'categoria-{n}')
    is_active = True

    @factory.post_generation
    def translation(self, create, extracted, **kwargs):
        if not create:
            return

        category = cast(Any, self)
        data = extracted or {}
        CategoryTranslation.objects.create(
            category=category,
            language=data.get('language', 'pt'),
            name=data.get('name', str(category.slug).replace('-', ' ').title()),
            description=data.get('description', f'Descrição de {category.slug}'),
        )
        if hasattr(category, '_translation_fallback_cache'):
            delattr(category, '_translation_fallback_cache')


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product
        skip_postgeneration_save = True

    category = factory.SubFactory(CategoryFactory)
    slug = factory.Sequence(lambda n: f'produto-{n}')
    name = factory.Sequence(lambda n: f'Produto {n}')
    brand = 'Biobrassica'
    description = factory.Sequence(lambda n: f'Descrição do produto {n}')
    allergens = 'Sem alergénios declarados.'
    price = Decimal('9.50')
    quantity = '1 un'
    stock = 10
    is_active = True
    is_preview = False
    is_highlight = False
    allow_shipping = True
    allow_pickup = False
    bio_code = factory.Sequence(lambda n: f'PT-BIO-{n + 3:02d}')
    image = factory.LazyFunction(make_test_image)

    @factory.post_generation
    def translation(self, create, extracted, **kwargs):
        if not create:
            return

        product = cast(Any, self)
        data = extracted or {}
        language = data.get('language', 'pt')
        if language == 'pt':
            product.name = data.get('name', product.name)
            product.description = data.get('description', product.description)
            product.allergens = data.get('allergens', product.allergens)
            product.save(update_fields=['name', 'description', 'allergens'])

        ProductTranslation.objects.create(
            product=product,
            language=language,
            name=data.get('name', str(product.slug).replace('-', ' ').title()),
            description=data.get('description', f'Descrição de {product.slug}'),
            allergens=data.get('allergens', 'Sem alergénios declarados.'),
            ingredients=data.get('ingredients', f'Ingredientes de {product.slug}'),
        )
        if hasattr(product, '_translation_fallback_cache'):
            delattr(product, '_translation_fallback_cache')
