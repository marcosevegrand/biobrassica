from django import forms
from django.http import QueryDict
from typing import cast

from apps.core.limits import MAX_PURCHASE_QUANTITY


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=MAX_PURCHASE_QUANTITY)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound:
            data = cast(QueryDict, self.data).copy()
            if data.get('quantity') in (None, ''):
                data['quantity'] = '1'
            self.data = data


class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, max_value=MAX_PURCHASE_QUANTITY)