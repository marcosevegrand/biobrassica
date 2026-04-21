from django import forms
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Location
from apps.orders.models import Order, PT_POSTAL_CODE_RE
from apps.payments.models import Payment


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
        self.pickup_choices = self._build_pickup_choices()
        self.fields['pickup_location'].choices = self.pickup_choices
        self.allowed_pickup_locations = self._allowed_pickup_locations()

    def _build_pickup_choices(self):
        return [
            (location.pickup_location_code, location.name)
            for location in Location.objects.filter(is_active=True).exclude(pickup_location_code='').order_by('order', 'name')
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
        return self.cleaned_data['phone'].strip()

    def clean_shipping_address_line1(self):
        return self.cleaned_data['shipping_address_line1'].strip()

    def clean_shipping_address_line2(self):
        return self.cleaned_data['shipping_address_line2'].strip()

    def clean_shipping_city(self):
        return self.cleaned_data['shipping_city'].strip()

    def clean_shipping_postal_code(self):
        return self.cleaned_data['shipping_postal_code'].strip()

    def clean(self):
        cleaned_data = super().clean()
        fulfillment_method = cleaned_data.get('fulfillment_method') or Order.FulfillmentMethod.PICKUP
        cleaned_data['fulfillment_method'] = fulfillment_method

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
        elif not self.pickup_choices:
            raise forms.ValidationError(_('Não existem locais de levantamento configurados neste momento.'))
        elif not cleaned_data.get('pickup_location'):
            raise forms.ValidationError(_('Selecione um local de levantamento.'))
        elif self.allowed_pickup_locations is not None:
            pickup_location = cleaned_data['pickup_location']
            if not self.allowed_pickup_locations:
                self.add_error('pickup_location', _('Os produtos deste carrinho não estão disponíveis para levantamento nas lojas configuradas.'))
            elif pickup_location not in self.allowed_pickup_locations:
                self.add_error('pickup_location', _('Este local não está disponível para todos os produtos do carrinho.'))

        return cleaned_data


class PaymentSelectionForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=[(Payment.Method.STRIPE, 'Stripe')],
        error_messages={'invalid_choice': _('Selecione um método de pagamento válido.')},
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        if payment_method and payment_method != Payment.Method.STRIPE:
            raise forms.ValidationError(_('Selecione um método de pagamento válido.'))
        return cleaned_data