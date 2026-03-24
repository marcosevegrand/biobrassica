from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.translations import get_translated_attr


class Location(models.Model):
    """CRUD-managed pickup / availability locations."""
    name = models.CharField('nome', max_length=100, help_text='Ex: Loja Braga, Loja Guimarães')
    address = models.TextField('morada', blank=True)
    image = models.ImageField('imagem', upload_to='locations/', blank=True)
    phone = models.CharField('telefone', max_length=20, blank=True)
    email = models.EmailField('email', blank=True)
    opening_hours = models.CharField('horário', max_length=120, blank=True)
    map_embed_url = models.URLField('mapa embutido', blank=True)
    is_active = models.BooleanField('ativo', default=True)
    order = models.PositiveIntegerField('ordem', default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'localização'
        verbose_name_plural = 'localizações'

    def __str__(self):
        return self.name


class DeliveryMethod(models.Model):
    """CRUD-managed delivery / fulfillment methods."""
    name = models.CharField('nome', max_length=100, help_text='Ex: Levantamento na loja, Entrega ao domicílio')
    description = models.TextField('descrição', blank=True)
    is_active = models.BooleanField('ativo', default=True)
    order = models.PositiveIntegerField('ordem', default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'método de entrega'
        verbose_name_plural = 'métodos de entrega'

    def __str__(self):
        return self.name


class Category(models.Model):
    slug = models.SlugField('slug', unique=True)
    image = models.ImageField('imagem', upload_to='categories/', blank=True)
    order = models.PositiveIntegerField('ordem', default=0)
    is_active = models.BooleanField('ativo', default=True)
    is_featured = models.BooleanField(
        default=False,
        verbose_name='categoria especial',
        help_text='Ocupa uma linha completa na secção de categorias da loja.',
    )
    featured_message = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='mensagem de destaque',
        help_text='Mensagem opcional exibida em banner no cartão desta categoria especial.',
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'

    def __str__(self):
        return get_translated_attr(self, 'name', default=self.slug, lang='pt')


class CategoryTranslation(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='translations', verbose_name='categoria')
    language = models.CharField('idioma', max_length=2, choices=[('pt', 'Português'), ('en', 'Inglês'), ('fr', 'Francês')])
    name = models.CharField('nome', max_length=255)
    description = models.TextField('descrição', blank=True)

    class Meta:
        verbose_name = 'tradução de categoria'
        verbose_name_plural = 'traduções de categoria'
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'language'],
                name='catalog_unique_category_translation_language',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.language})'


class Product(models.Model):
    if TYPE_CHECKING:
        translations: models.Manager[ProductTranslation]
        images: models.Manager[ProductImage]

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='categoria')
    slug = models.SlugField('slug', unique=True)
    brand = models.CharField('marca', max_length=120, help_text='Marca do produto.')
    price = models.DecimalField('preço', max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantity = models.CharField(
        'quantidade',
        max_length=80,
        help_text='Ex: 500 g, 1 un, 6 x 330 ml',
    )
    stock = models.PositiveIntegerField('stock', default=0)
    is_active = models.BooleanField('ativo', default=True)
    is_highlight = models.BooleanField('em destaque', default=False)
    allow_shipping = models.BooleanField(
        'permite envio',
        default=False,
        help_text='Quando ativo, o produto pode ser enviado. Caso contrário, fica disponível apenas para levantamento em loja.',
    )
    available_locations = models.ManyToManyField(
        Location,
        blank=True,
        related_name='products',
        verbose_name='localizações',
    )
    bio_code = models.CharField(
        max_length=50,
        verbose_name='código bio (EU)',
        help_text='Ex: PT-BIO-03',
    )
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['-is_highlight', '-created_at']
        verbose_name = 'produto'
        verbose_name_plural = 'produtos'

    def __str__(self):
        return get_translated_attr(self, 'name', default=self.slug, lang='pt')

    def clean(self):
        super().clean()

        errors = {}

        for field_name, value in {
            'brand': self.brand,
            'quantity': self.quantity,
            'bio_code': self.bio_code,
        }.items():
            if not value or not str(value).strip():
                errors[field_name] = 'Este campo é obrigatório.'

        if self.pk:
            if not self.translations.exists():
                errors['__all__'] = ['O produto deve ter pelo menos uma designação, descrição, alergénicos e ingredientes.']
            if not self.images.exists():
                errors.setdefault('__all__', []).append('O produto deve ter pelo menos uma foto.')

        if errors:
            raise ValidationError(errors)

    def get_name(self, lang=None):
        return get_translated_attr(self, 'name', default=self.slug, lang=lang)

    def get_description(self, lang=None):
        return get_translated_attr(self, 'description', default='', lang=lang)

    def get_allergens(self, lang=None):
        return get_translated_attr(self, 'allergens', default='', lang=lang, fallback_on_empty=True)

    def get_ingredients(self, lang=None):
        return get_translated_attr(self, 'ingredients', default='', lang=lang, fallback_on_empty=True)

    @property
    def primary_image(self):
        images = list(self.images.all())
        return next((image for image in images if image.is_primary), None) or (images[0] if images else None)

    @property
    def price_display(self):
        return f'{self.price:.2f}€'

    @property
    def in_stock(self):
        return self.stock > 0


class ProductTranslation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='translations', verbose_name='produto')
    language = models.CharField('idioma', max_length=2, choices=[('pt', 'Português'), ('en', 'Inglês'), ('fr', 'Francês')])
    name = models.CharField('nome', max_length=255)
    description = models.TextField('descrição')
    allergens = models.CharField(
        'alergénicos',
        max_length=255,
        help_text='Ex: Contém glúten, soja, frutos secos',
    )
    ingredients = models.TextField('ingredientes', help_text='Lista completa de ingredientes do produto.')

    class Meta:
        verbose_name = 'tradução de produto'
        verbose_name_plural = 'traduções de produto'
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'language'],
                name='catalog_unique_product_translation_language',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.language})'

    def clean(self):
        super().clean()
        errors = {}
        for field_name, value in {
            'description': self.description,
            'allergens': self.allergens,
            'ingredients': self.ingredients,
        }.items():
            if not value or not value.strip():
                errors[field_name] = 'Este campo é obrigatório.'

        if errors:
            raise ValidationError(errors)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='produto')
    image = models.ImageField('imagem', upload_to='products/')
    alt_text = models.CharField('texto alternativo', max_length=255, blank=True)
    order = models.PositiveIntegerField('ordem', default=0)
    is_primary = models.BooleanField('imagem principal', default=False)

    class Meta:
        ordering = ['order']
        verbose_name = 'imagem de produto'
        verbose_name_plural = 'imagens de produto'

    def __str__(self):
        return f'Imagem {self.order} - {self.product}'
