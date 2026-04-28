from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from typing import Any, cast

from apps.accounts.validators import normalize_portuguese_mobile_phone, normalize_portuguese_phone
from apps.catalog.models import Location
from apps.orders.models import Order, PT_POSTAL_CODE_RE
from apps.payments.models import Payment
from apps.payments.services import available_payment_services


class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    fulfillment_method = forms.ChoiceField(
        choices=Order.FulfillmentMethod.choices,
        required=False,
        error_messages={'invalid_choice': _('Selecione um método de entrega válido.')},
    )
    pickup_location = forms.ChoiceField(choices=Order.PickupLocation.choices, required=False)
    shipping_address_line1 = forms.CharField(max_length=255, required=False)
    shipping_address_line2 = forms.CharField(max_length=255, required=False)
    shipping_city = forms.CharField(max_length=100, required=False)
    shipping_postal_code = forms.CharField(max_length=10, required=False)
    notes = forms.CharField(required=False)

    def __init__(self, *args, cart_can_ship, cart_items=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cart_can_ship = cart_can_ship
        self.cart_items = list(cart_items or [])
        phone_field = cast(forms.CharField, self.fields['phone'])
        # MB WAY (manual) requires a Portuguese mobile number to identify the request.
        services = {service.method: service for service in available_payment_services()}
        phone_field.required = Payment.Method.MBWAY_MANUAL in services
        self.allowed_pickup_locations = self._allowed_pickup_locations()
        self.pickup_choices = self._build_pickup_choices()
        cast(forms.ChoiceField, self.fields['pickup_location']).choices = self.pickup_choices

    def _build_pickup_choices(self):
        queryset = Location.objects.filter(is_active=True).exclude(pickup_location_code='').order_by('order', 'name')
        if self.allowed_pickup_locations is not None:
            if not self.allowed_pickup_locations:
                return []
            queryset = queryset.filter(pickup_location_code__in=self.allowed_pickup_locations)

        return [
            (location.pickup_location_code, location.name)
            for location in queryset
        ]

    def _allowed_pickup_locations(self):
        if not self.cart_items:
            return None

        allowed_sets = []
        for cart_item in self.cart_items:
            location_values = {
                location.pickup_location_code
                for location in cart_item.product.available_locations.all()
                if location.pickup_location_code
            }
            allowed_sets.append(location_values)

        if not allowed_sets:
            return None

        allowed_values = set.intersection(*allowed_sets) if allowed_sets else set()
        return allowed_values

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    def clean_email(self):
        return self.cleaned_data['email'].strip()

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        try:
            if cast(forms.CharField, self.fields['phone']).required:
                return normalize_portuguese_mobile_phone(phone)
            return normalize_portuguese_phone(phone)
        except DjangoValidationError as error:
            raise forms.ValidationError(error.messages) from error

    def clean_shipping_address_line1(self):
        return self.cleaned_data['shipping_address_line1'].strip()

    def clean_shipping_address_line2(self):
        return self.cleaned_data['shipping_address_line2'].strip()

    def clean_shipping_city(self):
        return self.cleaned_data['shipping_city'].strip()

    def clean_shipping_postal_code(self):
        return self.cleaned_data['shipping_postal_code'].strip()

    def clean(self):
        cleaned_data: dict[str, Any] = super().clean() or {}
        fulfillment_method = cleaned_data.get('fulfillment_method') or Order.FulfillmentMethod.PICKUP
        cleaned_data['fulfillment_method'] = fulfillment_method
        raw_pickup_location = str(self.data.get(self.add_prefix('pickup_location'), '') or '')

        if fulfillment_method == Order.FulfillmentMethod.SHIPPING:
            if not self.cart_can_ship:
                raise forms.ValidationError(
                    _('Este carrinho contém produtos disponíveis apenas para levantamento em loja.')
                )

            required_shipping_fields = (
                'shipping_address_line1',
                'shipping_city',
                'shipping_postal_code',
            )
            if any(not cleaned_data.get(field_name) for field_name in required_shipping_fields):
                raise forms.ValidationError(_('Preencha a morada de envio completa.'))

            postal_code = cleaned_data.get('shipping_postal_code', '')
            if postal_code and not PT_POSTAL_CODE_RE.match(postal_code):
                self.add_error('shipping_postal_code', _('Use o formato 1234-123.'))

            cleaned_data['pickup_location'] = ''
        elif self.allowed_pickup_locations == set():
            self.errors.pop('pickup_location', None)
            self.add_error('pickup_location', _('Os produtos deste carrinho não estão disponíveis para levantamento nas lojas configuradas.'))
        elif not self.pickup_choices:
            raise forms.ValidationError(_('Não existem locais de levantamento configurados neste momento.'))
        elif not cleaned_data.get('pickup_location') and not raw_pickup_location:
            raise forms.ValidationError(_('Selecione um local de levantamento.'))
        elif self.allowed_pickup_locations is not None:
            pickup_location = str(cleaned_data.get('pickup_location') or raw_pickup_location)
            if pickup_location not in self.allowed_pickup_locations:
                self.errors.pop('pickup_location', None)
                self.add_error('pickup_location', _('Este local não está disponível para todos os produtos do carrinho.'))

        if cast(forms.CharField, self.fields['phone']).required and not cleaned_data.get('phone'):
            self.add_error('phone', _('Indique um telemóvel para receber o pedido MB WAY.'))

        return cleaned_data


class PaymentSelectionForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=(),
        error_messages={'invalid_choice': _('Selecione um método de pagamento válido.')},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        services = available_payment_services()
        method_labels = dict(Payment.Method.choices)
        choices = [(service.method, method_labels.get(service.method, service.method)) for service in services]
        cast(forms.ChoiceField, self.fields['payment_method']).choices = choices
        self.available_methods = {service.method for service in services}

    def clean(self):
        cleaned_data: dict[str, Any] = super().clean() or {}
        payment_method = cleaned_data.get('payment_method')
        if not self.available_methods:
            raise forms.ValidationError(_('Não existem métodos de pagamento disponíveis neste momento.'))
        if payment_method and payment_method not in self.available_methods:
            raise forms.ValidationError(_('Selecione um método de pagamento válido.'))
        return cleaned_data