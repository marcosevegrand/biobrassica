from decimal import Decimal, InvalidOperation
import re
from typing import Any

from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from typing import cast

from apps.catalog.models import Product, ProductImage, ProductTranslation


class ProductAdminForm(forms.ModelForm):
    BRAND_CUSTOM_CHOICE = '__custom__'
    QUANTITY_UNIT_CHOICES = [
        ('g', _('g')),
        ('kg', _('kg')),
        ('ml', _('ml')),
        ('l', _('l')),
        ('un', _('un')),
        ('pack', _('pack')),
        ('box', _('box')),
    ]
    QUANTITY_PATTERN = re.compile(r'^\s*(?P<value>\d+(?:[\.,]\d{1,2})?)\s*(?P<unit>g|kg|ml|l|un|pack|box)\s*$')

    slug = forms.SlugField(
        required=False,
        help_text=_('Gerado automaticamente a partir do nome em Português e da quantidade, mas pode ser ajustado manualmente.'),
    )
    brand_choice = forms.ChoiceField(
        label=_('Marca existente'),
        required=False,
        help_text=_('Escolha uma marca já usada no catálogo para evitar duplicados.'),
    )
    brand_custom = forms.CharField(
        label=_('Nova marca'),
        required=False,
        help_text=_('Preencha apenas se a marca ainda não existir.'),
    )
    quantity_value = forms.DecimalField(
        label=_('Quantidade'),
        required=False,
        min_value=Decimal('0.01'),
        max_digits=8,
        decimal_places=2,
        help_text=_('Use um valor simples e normalizado para o peso, volume ou unidades.'),
    )
    quantity_unit = forms.ChoiceField(
        label=_('Unidade'),
        required=False,
        choices=QUANTITY_UNIT_CHOICES,
        help_text=_('Escolha a unidade apresentada ao cliente na ficha do produto.'),
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category_field = cast(forms.ModelChoiceField, self.fields['category'])
        locations_field = cast(forms.ModelMultipleChoiceField, self.fields['available_locations'])
        if 'brand' in self.fields:
            self.fields['brand'].required = False
            self.fields['brand'].widget = forms.HiddenInput()
        if 'quantity' in self.fields:
            self.fields['quantity'].required = False
            self.fields['quantity'].widget = forms.HiddenInput()
        category_queryset = category_field.queryset
        locations_queryset = locations_field.queryset
        if category_queryset is not None:
            category_field.queryset = category_queryset.filter(is_active=True).order_by('order', 'slug')
        if locations_queryset is not None:
            locations_field.queryset = locations_queryset.filter(is_active=True).order_by('order', 'name')

        current_brand = self._normalize_brand_name(getattr(self.instance, 'brand', ''))
        brand_choices = [
            ('', str(_('Selecione uma marca'))),
            *[(brand, brand) for brand in self._brand_suggestions(current_brand)],
            (self.BRAND_CUSTOM_CHOICE, str(_('Outra marca'))),
        ]
        cast(forms.ChoiceField, self.fields['brand_choice']).choices = brand_choices

        if current_brand:
            available_brands = {value for value, _ in brand_choices}
            if current_brand in available_brands:
                self.initial.setdefault('brand_choice', current_brand)
                self.initial.setdefault('brand_custom', '')
            else:
                self.initial.setdefault('brand_choice', self.BRAND_CUSTOM_CHOICE)
                self.initial.setdefault('brand_custom', current_brand)

        parsed_quantity = self._parse_quantity(getattr(self.instance, 'quantity', ''))
        if parsed_quantity is not None:
            quantity_value, quantity_unit = parsed_quantity
            self.initial.setdefault('quantity_value', quantity_value)
            self.initial.setdefault('quantity_unit', quantity_unit)

        placeholders = {
            'brand_custom': _('Ex: Biobrassica'),
            'quantity_value': _('Ex: 500'),
            'bio_code': _('Ex: PT-BIO-03'),
            'slug': _('Gerado automaticamente se deixar vazio'),
        }
        for field_name, placeholder in placeholders.items():
            self.fields[field_name].widget.attrs.setdefault('placeholder', placeholder)

        self.fields['available_locations'].help_text = _('Escolha os pontos de venda onde o produto está disponível para levantamento.')
        self.fields['stock'].help_text = _('Atualize o stock real para evitar encomendas impossíveis de cumprir.')
        self.fields['brand_custom'].widget.attrs.setdefault('autocomplete', 'off')
        self.fields['quantity_value'].widget.attrs.setdefault('step', '0.01')

    def _normalize_brand_name(self, value):
        return ' '.join(str(value or '').split())

    def _brand_suggestions(self, current_brand):
        brands = set(
            self._normalize_brand_name(brand)
            for brand in Product.objects.exclude(brand='').values_list('brand', flat=True)
        )
        if current_brand:
            brands.add(current_brand)
        return sorted(brand for brand in brands if brand)

    def _parse_quantity(self, value):
        quantity = str(value or '').strip()
        if not quantity:
            return None

        match = self.QUANTITY_PATTERN.match(quantity)
        if not match:
            return None

        normalized_value = match.group('value').replace(',', '.')
        try:
            quantity_value = Decimal(normalized_value)
        except InvalidOperation:
            return None

        return quantity_value, match.group('unit')

    def _format_quantity_value(self, value):
        normalized = value.quantize(Decimal('0.01')).normalize()
        text = format(normalized, 'f')
        return text.rstrip('0').rstrip('.') if '.' in text else text

    def clean(self):
        cleaned_data: dict[str, Any] = super().clean() or {}
        brand_choice = str(cleaned_data.get('brand_choice') or '').strip()
        brand_custom = self._normalize_brand_name(cleaned_data.get('brand_custom', ''))

        existing_brands = {
            brand.casefold(): brand
            for brand in self._brand_suggestions(self._normalize_brand_name(getattr(self.instance, 'brand', '')))
        }

        if brand_choice == self.BRAND_CUSTOM_CHOICE:
            if not brand_custom:
                self.add_error('brand_custom', _('Indique a nova marca para este produto.'))
            cleaned_brand = existing_brands.get(brand_custom.casefold(), brand_custom)
        elif brand_choice:
            cleaned_brand = brand_choice
        elif brand_custom:
            cleaned_brand = existing_brands.get(brand_custom.casefold(), brand_custom)
        else:
            cleaned_brand = ''
            self.add_error('brand_choice', _('Selecione uma marca existente ou indique uma nova marca.'))

        quantity_value = cleaned_data.get('quantity_value')
        quantity_unit = str(cleaned_data.get('quantity_unit') or '').strip()
        cleaned_quantity = ''
        if quantity_value in (None, '') and not quantity_unit:
            self.add_error('quantity_value', _('Indique a quantidade apresentada ao cliente.'))
            self.add_error('quantity_unit', _('Escolha a unidade apresentada ao cliente.'))
        elif quantity_value in (None, ''):
            self.add_error('quantity_value', _('Indique a quantidade apresentada ao cliente.'))
        elif not quantity_unit:
            self.add_error('quantity_unit', _('Escolha a unidade apresentada ao cliente.'))
        else:
            cleaned_quantity = f'{self._format_quantity_value(quantity_value)} {quantity_unit}'

        cleaned_data['brand'] = cleaned_brand
        cleaned_data['quantity'] = cleaned_quantity
        return cleaned_data

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip()
        return slugify(slug) if slug else ''

    def save(self, commit=True):
        self.instance.brand = str(self.cleaned_data.get('brand') or '').strip()
        self.instance.quantity = str(self.cleaned_data.get('quantity') or '').strip()
        return super().save(commit=commit)


class ProductTranslationInlineForm(forms.ModelForm):
    class Meta:
        model = ProductTranslation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['language'].help_text = _('Adicione apenas os idiomas realmente necessários. Português primeiro.')
        self.fields['name'].widget.attrs.setdefault('placeholder', _('Ex: Massa integral bio'))
        self.fields['description'].widget.attrs.setdefault('rows', 4)
        self.fields['description'].widget.attrs.setdefault('placeholder', _('Descrição comercial curta e clara do produto.'))
        self.fields['allergens'].widget.attrs.setdefault('placeholder', _('Ex: Contém glúten'))
        self.fields['ingredients'].widget.attrs.setdefault('rows', 4)
        self.fields['ingredients'].widget.attrs.setdefault('placeholder', _('Lista completa de ingredientes.'))


class ProductImageInlineForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.setdefault('accept', 'image/*')
        self.fields['alt_text'].widget.attrs.setdefault('placeholder', _('Descrição curta para acessibilidade e SEO'))
        self.fields['order'].help_text = _('Use a ordem para controlar a sequência da galeria.')
