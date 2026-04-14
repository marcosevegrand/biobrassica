"""
Custom ModelForms for content admin that replace raw JSON textarea inputs
with user-friendly dynamic list widgets.
"""
import json

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.content.models import BlogPost, Recipe, RecipeTranslation
from apps.content.widgets import IngredientListWidget, StepListWidget, TagListWidget


# ── Custom form fields ──────────────────────────────────────────────────────

class TagListField(forms.Field):
    """
    A form field backed by TagListWidget.
    Stores/returns a Python list of strings.
    """
    widget = TagListWidget

    def to_python(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str) and value:
            try:
                result = json.loads(value)
                if isinstance(result, list):
                    return [str(v).strip() for v in result if str(v).strip()]
            except (ValueError, TypeError):
                pass
        return []

    def prepare_value(self, value):
        """Pass list directly to widget so it can render existing items."""
        if isinstance(value, str):
            try:
                return json.loads(value) if value else []
            except (ValueError, TypeError):
                return []
        return value if isinstance(value, list) else []

    def has_changed(self, initial, data):
        return self.to_python(initial) != self.to_python(data)


class IngredientListField(forms.Field):
    """
    A form field backed by IngredientListWidget.
    Stores/returns a Python list of plain ingredient strings (e.g. "200g farinha").
    """
    widget = IngredientListWidget

    def to_python(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            clean = []
            for item in value:
                if isinstance(item, dict):
                    # Legacy dict format: combine amount/unit/name into one string
                    parts = []
                    if item.get('amount'):
                        parts.append(str(item['amount']))
                        if item.get('unit'):
                            parts[-1] += str(item['unit'])
                    if item.get('name'):
                        parts.append(str(item['name']))
                    combined = ' '.join(parts).strip()
                    if combined:
                        clean.append(combined)
                elif isinstance(item, str) and item.strip():
                    clean.append(item.strip())
            return clean
        if isinstance(value, str) and value:
            try:
                result = json.loads(value)
                if isinstance(result, list):
                    return self.to_python(result)
            except (ValueError, TypeError):
                pass
        return []

    def prepare_value(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value) if value else []
            except (ValueError, TypeError):
                return []
        return value if isinstance(value, list) else []

    def has_changed(self, initial, data):
        return self.to_python(initial) != self.to_python(data)


class StepListField(forms.Field):
    """
    A form field backed by StepListWidget.
    Stores/returns a Python list of preparation step strings.
    """
    widget = StepListWidget

    def to_python(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str) and value:
            try:
                result = json.loads(value)
                if isinstance(result, list):
                    return [str(v).strip() for v in result if str(v).strip()]
            except (ValueError, TypeError):
                pass
        return []

    def prepare_value(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value) if value else []
            except (ValueError, TypeError):
                return []
        return value if isinstance(value, list) else []

    def has_changed(self, initial, data):
        return self.to_python(initial) != self.to_python(data)


# ── ModelForms ──────────────────────────────────────────────────────────────

class BlogPostAdminForm(forms.ModelForm):
    tags = TagListField(
        required=False,
        label=_('Tags'),
        help_text=_('Adicione tags para categorizar este artigo.'),
    )

    class Meta:
        model = BlogPost
        fields = '__all__'


class RecipeAdminForm(forms.ModelForm):
    tags = TagListField(
        required=False,
        label=_('Tags'),
        help_text=_('Adicione tags para categorizar esta receita.'),
    )

    class Meta:
        model = Recipe
        fields = '__all__'


class RecipeTranslationAdminForm(forms.ModelForm):
    ingredients = IngredientListField(
        required=False,
        label=_('Ingredientes'),
        help_text=_('Adicione os ingredientes necessários para esta receita (ex: "200g farinha espelta").'),
    )
    instructions = StepListField(
        required=False,
        label=_('Preparação'),
        help_text=_('Adicione cada passo de preparação. O sistema numera automaticamente.'),
    )

    class Meta:
        model = RecipeTranslation
        fields = '__all__'
