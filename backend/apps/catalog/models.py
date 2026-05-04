from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max, Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.accounts.validators import normalize_portuguese_phone
from apps.core.translations import DEFAULT_LANGUAGE, get_translated_attr, normalized_language


PICKUP_LOCATION_CODE_CHOICES = [
    ('braga', 'Braga'),
    ('guimaraes', 'Guimarães'),
]

TRANSLATION_LANGUAGE_CHOICES = [
    ('en', 'Inglês'),
    ('fr', 'Francês'),
]

PICKUP_HOURS_WEEKDAY_KEYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
PICKUP_HOURS_WEEKDAY_LABELS = {
    'mon': _('Segunda'),
    'tue': _('Terça'),
    'wed': _('Quarta'),
    'thu': _('Quinta'),
    'fri': _('Sexta'),
    'sat': _('Sábado'),
    'sun': _('Domingo'),
}


class OrderedEntityPosition(models.Model):
    position = models.PositiveIntegerField(_('posição'), default=0)

    class Meta:
        abstract = True
        ordering = ['position', 'pk']

    @classmethod
    def next_position(cls):
        return (cls.objects.aggregate(max_position=Max('position'))['max_position'] or 0) + 1


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
    pickup_hours = models.JSONField(
        'horário de levantamento',
        default=dict,
        blank=True,
        help_text='Horário de levantamento por dia da semana. Ex: {"mon": "09:00-18:00"}.',
    )
    map_embed_url = models.URLField('mapa embutido', blank=True)
    is_active = models.BooleanField('ativo', default=True)

    def __init__(self, *args, **kwargs):
        self._pending_order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

    class Meta:
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

        if self.pickup_hours:
            if not isinstance(self.pickup_hours, dict):
                errors['pickup_hours'] = [_('Horário de levantamento deve ser um objeto JSON.')]
            else:
                cleaned = {}
                for key, value in self.pickup_hours.items():
                    key_norm = str(key).strip().lower()[:3]
                    if key_norm not in PICKUP_HOURS_WEEKDAY_KEYS:
                        errors['pickup_hours'] = [_('Use chaves de dia válidas para o horário de levantamento.')]
                        break
                    cleaned[key_norm] = str(value or '').strip()
                else:
                    self.pickup_hours = cleaned

        if errors:
            raise ValidationError(errors)

    @property
    def pickup_hours_rows(self):
        data = self.pickup_hours or {}
        rows = []
        for key in PICKUP_HOURS_WEEKDAY_KEYS:
            value = data.get(key)
            if value:
                rows.append((PICKUP_HOURS_WEEKDAY_LABELS[key], value))
        return rows

    @property
    def position(self):
        return getattr(getattr(self, 'sort_order', None), 'position', 0)

    @property
    def order(self):
        return self.position

    @order.setter
    def order(self, value):
        self._pending_order = value

    def save(self, *args, **kwargs):
        self.full_clean()
        result = super().save(*args, **kwargs)
        position_value = self._pending_order if self._pending_order is not None else LocationPosition.next_position()
        sort_order, created = LocationPosition.objects.get_or_create(location=self, defaults={'position': position_value})
        if not created and self._pending_order is not None and sort_order.position != self._pending_order:
            sort_order.position = self._pending_order
            sort_order.save(update_fields=['position'])
        self._pending_order = None
        return result

    def __str__(self):
        return self.name


class LocationPosition(OrderedEntityPosition):
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name='sort_order', verbose_name='localização')

    class Meta(OrderedEntityPosition.Meta):
        verbose_name = 'ordem de localização'
        verbose_name_plural = 'ordens de localização'

    def __str__(self):
        return f'{self.location} ({self.position})'


class DeliveryMethod(models.Model):
    """CRUD-managed delivery / fulfillment methods."""

    name = models.CharField('nome', max_length=100, help_text='Ex: Levantamento na loja, Entrega ao domicílio')
    description = models.TextField('descrição', blank=True)
    is_active = models.BooleanField('ativo', default=True)

    def __init__(self, *args, **kwargs):
        self._pending_order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

    class Meta:
        verbose_name = 'método de entrega'
        verbose_name_plural = 'métodos de entrega'

    @property
    def position(self):
        return getattr(getattr(self, 'sort_order', None), 'position', 0)

    @property
    def order(self):
        return self.position

    @order.setter
    def order(self, value):
        self._pending_order = value

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        position_value = self._pending_order if self._pending_order is not None else DeliveryMethodPosition.next_position()
        sort_order, created = DeliveryMethodPosition.objects.get_or_create(
            delivery_method=self,
            defaults={'position': position_value},
        )
        if not created and self._pending_order is not None and sort_order.position != self._pending_order:
            sort_order.position = self._pending_order
            sort_order.save(update_fields=['position'])
        self._pending_order = None
        return result

    def __str__(self):
        return self.name


class DeliveryMethodPosition(OrderedEntityPosition):
    delivery_method = models.OneToOneField(
        DeliveryMethod,
        on_delete=models.CASCADE,
        related_name='sort_order',
        verbose_name='método de entrega',
    )

    class Meta(OrderedEntityPosition.Meta):
        verbose_name = 'ordem de método de entrega'
        verbose_name_plural = 'ordens de métodos de entrega'

    def __str__(self):
        return f'{self.delivery_method} ({self.position})'


class Category(models.Model):
    slug = models.SlugField('slug', unique=True, blank=True)
    name = models.CharField('nome', max_length=255)
    image = models.ImageField('imagem', upload_to='categories/', blank=True)
    is_active = models.BooleanField('ativo', default=True)
    is_special = models.BooleanField('especial', default=False)
    featured_message = models.CharField('mensagem de destaque', max_length=200, blank=True)

    def __init__(self, *args, **kwargs):
        self._pending_order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

    class Meta:
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'

    def clean_fields(self, exclude=None):
        if not self.name and self.slug:
            self.name = str(self.slug).replace('-', ' ').strip()
        self.name = str(self.name or '').strip()
        self.slug = str(self.slug or '').strip()
        self.featured_message = str(self.featured_message or '').strip()
        return super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        if not self.slug and self.name:
            self.slug = slugify(self.name)

    @property
    def position(self):
        return getattr(getattr(self, 'sort_order', None), 'position', 0)

    @property
    def order(self):
        return self.position

    @order.setter
    def order(self, value):
        self._pending_order = value

    def save(self, *args, **kwargs):
        self.full_clean()
        result = super().save(*args, **kwargs)
        position_value = self._pending_order if self._pending_order is not None else CategoryPosition.next_position()
        sort_order, created = CategoryPosition.objects.get_or_create(category=self, defaults={'position': position_value})
        if not created and self._pending_order is not None and sort_order.position != self._pending_order:
            sort_order.position = self._pending_order
            sort_order.save(update_fields=['position'])
        self._pending_order = None
        return result

    def get_name(self, lang=None):
        language = normalized_language(lang)
        if language == DEFAULT_LANGUAGE:
            return self.name
        return get_translated_attr(self, 'name', default=self.name, lang=language, fallback_on_empty=True)

    def get_featured_message(self, lang=None):
        language = normalized_language(lang)
        if language == DEFAULT_LANGUAGE:
            return self.featured_message
        return get_translated_attr(
            self,
            'featured_message',
            default=self.featured_message,
            lang=language,
            fallback_on_empty=True,
        )

    def __str__(self):
        return self.name or self.slug

    @property
    def is_featured(self):
        return self.is_special

    @is_featured.setter
    def is_featured(self, value):
        self.is_special = value


class CategoryPosition(OrderedEntityPosition):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name='sort_order', verbose_name='categoria')

    class Meta(OrderedEntityPosition.Meta):
        verbose_name = 'ordem de categoria'
        verbose_name_plural = 'ordens de categoria'

    def __str__(self):
        return f'{self.category} ({self.position})'


class CategoryTranslation(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='translations', verbose_name='categoria')
    language = models.CharField('idioma', max_length=2, choices=TRANSLATION_LANGUAGE_CHOICES)
    name = models.CharField('nome', max_length=255)
    featured_message = models.CharField('mensagem de destaque', max_length=200, blank=True)

    def __init__(self, *args, **kwargs):
        kwargs.pop('description', None)
        super().__init__(*args, **kwargs)

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
        return f'{self.name} ({self.get_language_display()})'


class Product(models.Model):
    if TYPE_CHECKING:
        translations: models.Manager[ProductTranslation]

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='categoria')
    slug = models.SlugField('slug', unique=True, blank=True)
    name = models.CharField('nome', max_length=255)
    brand = models.CharField('marca', max_length=120)
    bio_code = models.CharField('código bio', max_length=50)
    description = models.TextField('descrição comercial + ingredientes')
    allergens = models.CharField('alergénicos', max_length=255)
    price = models.DecimalField('preço', max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantity = models.CharField('quantidade', max_length=80)
    stock = models.PositiveIntegerField('stock', default=0)
    is_active = models.BooleanField('ativo', default=True)
    is_highlight = models.BooleanField('em destaque', default=False)
    is_preview = models.BooleanField('pré-visualização', default=False)
    allow_shipping = models.BooleanField('envio', default=False)
    allow_pickup = models.BooleanField('recolha', default=False)
    pickup_locations = models.ManyToManyField(
        Location,
        blank=True,
        related_name='products',
        verbose_name='localizações de recolha',
    )
    image = models.ImageField('imagem', upload_to='products/', blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        ordering = ['-is_highlight', 'name', 'pk']
        verbose_name = 'produto'
        verbose_name_plural = 'produtos'

    def clean_fields(self, exclude=None):
        if not self.name and self.slug:
            self.name = str(self.slug).replace('-', ' ').strip()
        if not self.description and self.name:
            self.description = self.name
        if not self.allergens:
            self.allergens = _('Sem indicação de alergénicos')
        self.slug = str(self.slug or '').strip()
        self.name = str(self.name or '').strip()
        self.brand = str(self.brand or '').strip()
        self.bio_code = str(self.bio_code or '').strip()
        self.description = str(self.description or '').strip()
        self.allergens = str(self.allergens or '').strip()
        self.quantity = str(self.quantity or '').strip()
        return super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        errors = {}

        if not self.slug and self.name:
            self.slug = slugify(self.name)

        if self.is_active and not self.allow_shipping and not self.allow_pickup:
            errors['__all__'] = [_('O produto tem de permitir envio, recolha, ou ambos.')]

        if self.pk and self.allow_pickup and not self.pickup_locations.exists():
            errors['pickup_locations'] = [_('Selecione pelo menos uma localização de recolha.')]

        if self.is_active:
            activation_blockers = self.get_activation_blockers()
            if activation_blockers:
                errors.setdefault('__all__', []).extend(activation_blockers)

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_activation_blockers(self):
        blockers = []

        if not self.image:
            blockers.append(_('O produto precisa de uma imagem.'))
        if self.stock <= 0 and not self.is_preview:
            blockers.append(_('O produto precisa de stock para estar ativo.'))
        if not self.allow_shipping and not self.allow_pickup:
            blockers.append(_('O produto precisa de um modo de disponibilização ativo.'))
        if self.pk and self.allow_pickup and self.pickup_locations.count() == 0:
            blockers.append(_('O produto precisa de pelo menos uma localização de recolha.'))

        return blockers

    def get_name(self, lang=None):
        language = normalized_language(lang)
        if language == DEFAULT_LANGUAGE:
            return self.name
        translation = next((item for item in self.translations.all() if item.language == language), None)
        return translation.name if translation and translation.name else self.name

    def get_description(self, lang=None):
        language = normalized_language(lang)
        if language == DEFAULT_LANGUAGE:
            return self.description
        translation = next((item for item in self.translations.all() if item.language == language), None)
        return translation.description if translation and translation.description else self.description

    def get_allergens(self, lang=None):
        language = normalized_language(lang)
        if language == DEFAULT_LANGUAGE:
            return self.allergens
        translation = next((item for item in self.translations.all() if item.language == language), None)
        return translation.allergens if translation and translation.allergens else self.allergens

    def get_ingredients(self, lang=None):
        return self.get_description(lang=lang)

    @property
    def primary_image(self):
        if not self.image:
            return None
        return SimpleNamespace(image=self.image, alt_text=self.get_name(lang='pt'))

    @property
    def available_locations(self):
        return self.pickup_locations

    @property
    def is_preview_only(self):
        return self.is_preview

    @is_preview_only.setter
    def is_preview_only(self, value):
        self.is_preview = value

    @property
    def price_display(self):
        return f'{self.price:.2f}€'

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_purchasable(self):
        return self.is_active and not self.is_preview

    @property
    def can_add_to_cart(self):
        return self.is_purchasable and self.in_stock


class ProductTranslation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='translations', verbose_name='produto')
    language = models.CharField('idioma', max_length=2, choices=TRANSLATION_LANGUAGE_CHOICES)
    name = models.CharField('nome', max_length=255)
    description = models.TextField('descrição comercial + ingredientes')
    allergens = models.CharField('alergénicos', max_length=255)

    def __init__(self, *args, **kwargs):
        legacy_ingredients = str(kwargs.pop('ingredients', '') or '').strip()
        super().__init__(*args, **kwargs)
        if legacy_ingredients:
            current_description = str(getattr(self, 'description', '') or '').strip()
            self.description = '\n\n'.join(part for part in [current_description, legacy_ingredients] if part)

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
        return f'{self.name} ({self.get_language_display()})'

    def clean(self):
        super().clean()
        errors = {}
        for field_name, value in {
            'name': self.name,
            'description': self.description,
            'allergens': self.allergens,
        }.items():
            if not value or not str(value).strip():
                errors[field_name] = _('Este campo é obrigatório.')

        if errors:
            raise ValidationError(errors)
