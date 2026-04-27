from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import normalize_portuguese_phone
from apps.core.translations import get_translated_attr


PICKUP_LOCATION_CODE_CHOICES = [
    ('braga', 'Braga'),
    ('guimaraes', 'Guimaraes'),
]


class Location(models.Model):
    """CRUD-managed pickup / availability locations."""
    name = models.CharField('nome', max_length=100, help_text='Ex: Loja Braga, Loja Guimarães')
    pickup_location_code = models.CharField(
        'código de levantamento',
        max_length=20,
        blank=True,
        choices=PICKUP_LOCATION_CODE_CHOICES,
        help_text='Liga a localização a uma opção fixa de levantamento usada no checkout.',
    )
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
        constraints = [
            models.UniqueConstraint(
                fields=['pickup_location_code'],
                condition=~Q(pickup_location_code=''),
                name='catalog_unique_location_pickup_location_code',
            ),
        ]

    def clean_fields(self, exclude=None):
        self.name = str(self.name or '').strip()
        self.pickup_location_code = str(self.pickup_location_code or '').strip()
        self.address = str(self.address or '').strip()
        self.phone = str(self.phone or '').strip()
        self.email = str(self.email or '').strip().lower()
        self.opening_hours = str(self.opening_hours or '').strip()
        self.map_embed_url = str(self.map_embed_url or '').strip()
        return super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()

        errors = {}

        try:
            self.phone = normalize_portuguese_phone(self.phone)
        except ValidationError as error:
            errors['phone'] = error.messages

        if self.map_embed_url and urlsplit(self.map_embed_url).scheme != 'https':
            errors['map_embed_url'] = [_('Use um URL https:// válido para o mapa.')]

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

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
    is_preview_only = models.BooleanField(
        'apenas pré-visualização',
        default=False,
        help_text='Quando ativo, o produto permanece visível no catálogo mas não pode ser comprado.',
    )
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

        if self.is_active:
            activation_blockers = self.get_activation_blockers()
            if activation_blockers:
                errors.setdefault('__all__', []).extend(activation_blockers)

        if errors:
            raise ValidationError(errors)

    def get_activation_blockers(self):
        blockers = []

        if self.stock <= 0 and not self.is_preview_only:
            blockers.append('O produto precisa de stock para estar ativo.')

        if not self.pk:
            return blockers

        pt_translation_count = getattr(self, 'pt_translation_count', self.translations.filter(language='pt').count())
        primary_image_count = getattr(self, 'primary_image_count', self.images.filter(is_primary=True).count())
        location_count = getattr(self, 'location_count', self.available_locations.count())

        if pt_translation_count == 0:
            blockers.append('O produto precisa de tradução PT para estar ativo.')
        if primary_image_count == 0:
            blockers.append('O produto precisa de uma imagem principal para estar ativo.')
        if location_count == 0:
            blockers.append('O produto precisa de pelo menos uma localização para levantamento.')

        return blockers

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

    @property
    def is_purchasable(self):
        return self.is_active and not self.is_preview_only

    @property
    def can_add_to_cart(self):
        return self.is_purchasable and self.in_stock


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
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=Q(is_primary=True),
                name='catalog_unique_primary_product_image',
            ),
        ]

    def __str__(self):
        return f'Imagem {self.order} - {self.product}'

    def clean(self):
        super().clean()
        product = getattr(self, 'product', None)

        if (
            self.is_primary
            and product is not None
            and product.pk is not None
            and ProductImage.objects.filter(product=product, is_primary=True)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError({'is_primary': 'O produto já tem uma imagem principal.'})
