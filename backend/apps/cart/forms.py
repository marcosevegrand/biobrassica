from django import forms


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound:
            data = self.data.copy()
            if data.get('quantity') in (None, ''):
                data['quantity'] = '1'
            self.data = data


class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(min_value=0)