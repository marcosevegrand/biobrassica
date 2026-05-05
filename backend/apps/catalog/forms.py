from django import forms
import json
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Category, CategoryTranslation, DeliveryMethod, Location, Product, ProductTranslation
from apps.catalog.widgets import PickupLocationSelectWidget, PickupScheduleWidget


class BaseAdminStyleFormMixin:
    string_placeholders = {}
    textarea_fields = {}
    numeric_fields = ()

    def _apply_shared_admin_styles(self):
        for field_name, placeholder in self.string_placeholders.items():
            field = self.fields.get(field_name)
            if field is not None:
                field.widget.attrs.setdefault('placeholder', placeholder)

        for field_name, rows in self.textarea_fields.items():
            field = self.fields.get(field_name)
            if field is not None:
                field.widget.attrs.setdefault('rows', rows)

        for field_name in self.numeric_fields:
            field = self.fields.get(field_name)
            if field is not None:
                field.widget.attrs.setdefault('step', '0.01')


class CategoryAdminForm(BaseAdminStyleFormMixin, forms.ModelForm):
    string_placeholders = {
        'name': _('Nome da categoria'),
        'slug': _('Gerado automaticamente a partir do nome'),
        'featured_message': _('Mensagem opcional de destaque'),
    }

    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()


class CategoryTranslationInlineForm(BaseAdminStyleFormMixin, forms.ModelForm):
    string_placeholders = {
        'name': _('Nome traduzido'),
        'featured_message': _('Mensagem de destaque traduzida'),
    }

    class Meta:
        model = CategoryTranslation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()


class ProductAdminForm(BaseAdminStyleFormMixin, forms.ModelForm):
    string_placeholders = {
        'name': _('Nome do produto'),
        'slug': _('Gerado automaticamente a partir do nome'),
        'brand': _('Marca'),
        'bio_code': _('Ex: PT-BIO-03'),
        'quantity': _('Ex: 500 g, 1 un, 6 x 330 ml'),
        'allergens': _('Ex: Contém glúten'),
    }
    textarea_fields = {
        'description': 5,
    }
    numeric_fields = ('price',)

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('name', 'pk')
        self.fields['pickup_locations'].queryset = (
            Location.objects.filter(is_active=True)
            .select_related('sort_order')
            .order_by('sort_order__position', 'name', 'pk')
        )
        self.fields['pickup_locations'].widget = PickupLocationSelectWidget()
        self.fields['pickup_locations'].widget.choices = self.fields['pickup_locations'].choices
        self.fields['pickup_locations'].help_text = _('Selecione as localizações onde o produto pode ser recolhido.')
        self.fields['image'].widget.attrs.setdefault('accept', 'image/png,image/jpeg,image/webp')

    def clean(self):
        cleaned_data = super().clean()
        allow_pickup = cleaned_data.get('allow_pickup')
        pickup_locations = cleaned_data.get('pickup_locations')
        if allow_pickup and not pickup_locations:
            self.add_error('pickup_locations', _('Selecione pelo menos uma localização de recolha.'))
        return cleaned_data


class ProductTranslationInlineForm(BaseAdminStyleFormMixin, forms.ModelForm):
    string_placeholders = {
        'name': _('Nome traduzido'),
        'allergens': _('Alergénicos traduzidos'),
    }
    textarea_fields = {
        'description': 4,
    }

    class Meta:
        model = ProductTranslation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()


class LocationAdminForm(BaseAdminStyleFormMixin, forms.ModelForm):
    pickup_hours = forms.CharField(
        label=_('horário'),
        required=False,
        widget=PickupScheduleWidget(),
        help_text=_('Selecione os blocos de 30 minutos em que o levantamento está disponível.'),
    )
    string_placeholders = {
        'name': _('Nome do local'),
        'address': _('Morada do local'),
        'phone': _('Telefone de contacto'),
    }

    class Meta:
        model = Location
        fields = ('name', 'address', 'phone', 'is_active', 'pickup_hours')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()
        self.initial['pickup_hours'] = json.dumps(self.instance.pickup_hours or {}) if getattr(self.instance, 'pk', None) else '{}'

    def clean_pickup_hours(self):
        raw_value = str(self.cleaned_data.get('pickup_hours') or '{}').strip() or '{}'
        try:
            data = json.loads(raw_value)
        except json.JSONDecodeError as error:
            raise forms.ValidationError(_('Horário inválido.')) from error
        if not isinstance(data, dict):
            raise forms.ValidationError(_('Horário inválido.'))
        return data


class DeliveryMethodAdminForm(BaseAdminStyleFormMixin, forms.ModelForm):
    string_placeholders = {
        'name': _('Nome do método'),
        'estimated_delivery_time': _('Ex: 24h a 48h úteis'),
    }

    class Meta:
        model = DeliveryMethod
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()
