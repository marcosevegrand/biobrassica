from django import forms
from django.utils.translation import gettext_lazy as _

from apps.orders.models import Order, PT_POSTAL_CODE_RE
from apps.payments.models import Payment


class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=255)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    fulfillment_method = forms.ChoiceField(choices=Order.FulfillmentMethod.choices, required=False)
    pickup_location = forms.ChoiceField(choices=Order.PickupLocation.choices, required=False)
    shipping_address_line1 = forms.CharField(max_length=255, required=False)
    shipping_address_line2 = forms.CharField(max_length=255, required=False)
    shipping_city = forms.CharField(max_length=100, required=False)
    shipping_postal_code = forms.CharField(max_length=10, required=False)
    notes = forms.CharField(required=False)

    def __init__(self, *args, cart_can_ship, **kwargs):
        super().__init__(*args, **kwargs)
        self.cart_can_ship = cart_can_ship

    def clean_name(self):
        return self.cleaned_data['name'].strip()

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
        elif not cleaned_data.get('pickup_location'):
            raise forms.ValidationError(_('Selecione um local de levantamento.'))

        return cleaned_data


class PaymentSelectionForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=[(Payment.Method.MBWAY, 'MB WAY')],
        error_messages={'invalid_choice': _('Selecione um método de pagamento válido.')},
    )
    mbway_phone = forms.CharField(max_length=20, required=False)

    def clean_mbway_phone(self):
        return self.cleaned_data['mbway_phone'].strip()

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        mbway_phone = cleaned_data.get('mbway_phone', '')

        if payment_method == Payment.Method.MBWAY and not mbway_phone:
            raise forms.ValidationError(_('Indique o número de telemóvel para MB WAY.'))

        return cleaned_data