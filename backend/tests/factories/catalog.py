from decimal import Decimal

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

        data = extracted or {}
        CategoryTranslation.objects.create(
            category=self,
            language=data.get('language', 'pt'),
            name=data.get('name', self.slug.replace('-', ' ').title()),
            description=data.get('description', f'Descrição de {self.slug}'),
        )
        if hasattr(self, '_translation_fallback_cache'):
            delattr(self, '_translation_fallback_cache')


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
    is_highlight = False
    allow_shipping = True
    bio_code = factory.Sequence(lambda n: f'PT-BIO-{n + 3:02d}')

    @factory.post_generation
    def translation(self, create, extracted, **kwargs):
        if not create:
            return

        data = extracted or {}
        ProductTranslation.objects.create(
            product=self,
            language=data.get('language', 'pt'),
            name=data.get('name', self.slug.replace('-', ' ').title()),
            description=data.get('description', f'Descrição de {self.slug}'),
            allergens=data.get('allergens', 'Sem alergénios declarados.'),
            ingredients=data.get('ingredients', f'Ingredientes de {self.slug}'),
        )
        if hasattr(self, '_translation_fallback_cache'):
            delattr(self, '_translation_fallback_cache')