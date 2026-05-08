"""
Custom ModelForms for content admin that replace raw JSON textarea inputs
with user-friendly dynamic list widgets.
"""
import json

from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.content.models import BlogPost, BlogPostTranslation, Recipe, RecipeTranslation
from apps.content.widgets import IngredientListWidget, StepListWidget, TagListWidget


class BaseAdminStyleFormMixin:
    string_placeholders = {}
    textarea_fields = {}

    def _apply_shared_admin_styles(self):
        for field_name, placeholder in self.string_placeholders.items():
            field = self.fields.get(field_name)
            if field is not None:
                field.widget.attrs.setdefault('placeholder', placeholder)

        for field_name, rows in self.textarea_fields.items():
            field = self.fields.get(field_name)
            if field is not None:
                field.widget.attrs.setdefault('rows', rows)


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

class BlogPostAdminForm(BaseAdminStyleFormMixin, forms.ModelForm):
    title = forms.CharField(label=_('Título'))
    excerpt = forms.CharField(label=_('Resumo'), widget=forms.Textarea)
    content = forms.CharField(label=_('Conteúdo'), widget=forms.Textarea)
    tags = TagListField(
        required=False,
        label=_('Tags'),
        help_text=_('Adicione tags para categorizar este artigo.'),
    )
    string_placeholders = {
        'slug': _('Gerado automaticamente a partir do título'),
        'title': _('Título em Português'),
    }
    textarea_fields = {
        'excerpt': 3,
        'content': 16,
    }

    class Meta:
        model = BlogPost
        fields = (
            'slug', 'title', 'excerpt', 'content', 'author',
            'cover_image', 'tags', 'is_published', 'published_at',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()
        self.fields['slug'].required = False
        self.fields['content'].help_text = _('Escreva o conteúdo em Markdown.')
        if self.instance.pk:
            self.fields['title'].initial = self.instance.get_title('pt')
            self.fields['excerpt'].initial = self.instance.get_excerpt('pt')
            self.fields['content'].initial = self.instance.get_content('pt')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('slug') and cleaned_data.get('title'):
            cleaned_data['slug'] = slugify(cleaned_data['title'])[:200]
            self.instance.slug = cleaned_data['slug']
        self.instance._pt_translation_draft = {
            'title': cleaned_data.get('title', ''),
            'excerpt': cleaned_data.get('excerpt', ''),
            'content': cleaned_data.get('content', ''),
        }
        return cleaned_data


class BlogPostTranslationAdminForm(BaseAdminStyleFormMixin, forms.ModelForm):
    string_placeholders = {
        'title': _('Título traduzido'),
    }
    textarea_fields = {
        'excerpt': 3,
        'content': 12,
    }

    class Meta:
        model = BlogPostTranslation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()
        self.fields['content'].help_text = _('Escreva o conteúdo traduzido em Markdown.')
        self.fields['language'].choices = [('en', _('Inglês')), ('fr', _('Francês'))]


class RecipeAdminForm(BaseAdminStyleFormMixin, forms.ModelForm):
    title = forms.CharField(label=_('Título'))
    description = forms.CharField(label=_('Resumo'), widget=forms.Textarea)
    content = forms.CharField(label=_('Conteúdo'), widget=forms.Textarea)
    tags = TagListField(
        required=False,
        label=_('Tags'),
        help_text=_('Adicione tags para categorizar esta receita.'),
    )
    string_placeholders = {
        'slug': _('Gerado automaticamente a partir do título'),
        'title': _('Título em Português'),
    }
    textarea_fields = {
        'description': 3,
        'content': 16,
    }

    class Meta:
        model = Recipe
        fields = (
            'slug', 'title', 'description', 'content', 'cover_image',
            'tags', 'prep_time', 'cook_time', 'servings', 'difficulty',
            'related_products', 'is_published',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()
        self.fields['slug'].required = False
        self.fields['content'].help_text = _('Escreva o conteúdo da receita em Markdown.')
        if self.instance.pk:
            self.fields['title'].initial = self.instance.get_title('pt')
            self.fields['description'].initial = self.instance.get_description('pt')
            self.fields['content'].initial = self.instance.get_content('pt')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('slug') and cleaned_data.get('title'):
            cleaned_data['slug'] = slugify(cleaned_data['title'])[:200]
            self.instance.slug = cleaned_data['slug']
        self.instance._pt_translation_draft = {
            'title': cleaned_data.get('title', ''),
            'description': cleaned_data.get('description', ''),
            'content': cleaned_data.get('content', ''),
        }
        return cleaned_data


class RecipeTranslationAdminForm(BaseAdminStyleFormMixin, forms.ModelForm):
    string_placeholders = {
        'title': _('Título traduzido'),
    }
    textarea_fields = {
        'description': 3,
        'content': 12,
    }

    class Meta:
        model = RecipeTranslation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_shared_admin_styles()
        self.fields['content'].help_text = _('Escreva o conteúdo traduzido em Markdown.')
        self.fields['language'].choices = [('en', _('Inglês')), ('fr', _('Francês'))]
