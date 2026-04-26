# pyright: reportPrivateImportUsage=false, reportIncompatibleVariableOverride=false

from decimal import Decimal
from typing import Any, cast

import factory

from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation


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
    brand = 'Biobrassica'
    price = Decimal('9.50')
    quantity = '1 un'
    stock = 10
    is_active = True
    is_preview_only = False
    is_highlight = False
    allow_shipping = True
    bio_code = factory.Sequence(lambda n: f'PT-BIO-{n + 3:02d}')

    @factory.post_generation
    def translation(self, create, extracted, **kwargs):
        if not create:
            return

        product = cast(Any, self)
        data = extracted or {}
        ProductTranslation.objects.create(
            product=product,
            language=data.get('language', 'pt'),
            name=data.get('name', str(product.slug).replace('-', ' ').title()),
            description=data.get('description', f'Descrição de {product.slug}'),
            allergens=data.get('allergens', 'Sem alergénios declarados.'),
            ingredients=data.get('ingredients', f'Ingredientes de {product.slug}'),
        )
        if hasattr(product, '_translation_fallback_cache'):
            delattr(product, '_translation_fallback_cache')