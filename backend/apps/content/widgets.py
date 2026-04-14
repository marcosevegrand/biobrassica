"""
Custom admin widgets for JSON list fields.

- TagListWidget        → renders a list of strings as individual tag inputs
- IngredientListWidget → renders a list of ingredient name strings as individual inputs
- StepListWidget       → renders a list of step strings as numbered textarea rows

All widgets keep a hidden <input type="hidden"> in sync with the visible inputs.
The JS lives in static/admin/js/list_widgets.js.
"""
import html
import json
import uuid

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

_INPUT_BASE = 'padding:5px 8px;border:1px solid #d1d5db;border-radius:4px;background:#fff;'
_BTN_ADD    = (
    'margin-top:6px;padding:5px 14px;background:#ecfdf5;color:#059669;'
    'border:1px solid #a7f3d0;border-radius:4px;cursor:pointer;font-size:13px;font-weight:500;'
)
_BTN_REMOVE = (
    'padding:3px 10px;background:#fee2e2;color:#dc2626;'
    'border:none;border-radius:4px;cursor:pointer;font-size:15px;line-height:1;'
)
_WRAP = 'border:1px solid #e5e7eb;border-radius:6px;padding:14px 14px 10px;background:#fafafa;'


def _parse_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        try:
            result = json.loads(value)
            return result if isinstance(result, list) else []
        except (ValueError, TypeError):
            pass
    return []


class TagListWidget(forms.Widget):
    """Renders a JSON list of strings as labelled tag inputs with ＋ / × controls."""

    class Media:
        js = ('admin/js/list_widgets.js',)

    def render(self, name, value, attrs=None, renderer=None):
        items = _parse_list(value)
        cid = f'bb_tags_{uuid.uuid4().hex[:10]}'

        rows = ''
        for item in items:
            v = html.escape(str(item), quote=True)
            rows += (
                f'<div class="bb-tag-row" style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">'
                f'<input type="text" class="bb-tag-input" value="{v}"'
                f' style="flex:1;{_INPUT_BASE}font-size:14px;" />'
                f'<button type="button" onclick="bbRemoveItem(this)" style="{_BTN_REMOVE}">×</button>'
                f'</div>'
            )

        json_attr = html.escape(json.dumps(items), quote=True)
        out = (
            f'<div id="{cid}" class="bb-widget-container" data-type="tags" style="{_WRAP}">'
            f'<div class="bb-tags-container">{rows}</div>'
            f'<button type="button" onclick="bbAddTag(\'{cid}\')" style="{_BTN_ADD}">+ Adicionar tag</button>'
            f'<input type="hidden" name="{name}" class="bb-json-value" value="{json_attr}" />'
            f'</div>'
        )
        return mark_safe(out)

    def value_from_datadict(self, data, files, name):
        raw = data.get(name, '[]')
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except (ValueError, TypeError):
            pass
        return []


class IngredientListWidget(forms.Widget):
    """Renders a JSON list of ingredient name strings as individual text inputs."""

    class Media:
        js = ('admin/js/list_widgets.js',)

    def render(self, name, value, attrs=None, renderer=None):
        items = _parse_list(value)
        cid = f'bb_ingr_{uuid.uuid4().hex[:10]}'

        rows = ''
        for item in items:
            # Support both plain strings and legacy {name, amount, unit} dicts
            if isinstance(item, dict):
                label = str(item.get('name', ''))
                if item.get('amount'):
                    label = f"{item['amount']}{' ' + item['unit'] if item.get('unit') else ''} {label}".strip()
            else:
                label = str(item)
            v = html.escape(label, quote=True)
            rows += (
                f'<div class="bb-ingredient-row" style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">'
                f'<input type="text" class="bb-ingredient-input" value="{v}" placeholder="{html.escape(str(_("ex: 200g farinha espelta")), quote=True)}"'
                f' style="flex:1;{_INPUT_BASE}font-size:14px;" />'
                f'<button type="button" onclick="bbRemoveItem(this)" style="{_BTN_REMOVE}">×</button>'
                f'</div>'
            )

        json_attr = html.escape(json.dumps(items), quote=True)
        out = (
            f'<div id="{cid}" class="bb-widget-container" data-type="ingredients" style="{_WRAP}">'
            f'<div class="bb-ingredients-container">{rows}</div>'
            f'<button type="button" onclick="bbAddIngredient(\'{cid}\')" style="{_BTN_ADD}">+ {_("Adicionar ingrediente")}</button>'
            f'<input type="hidden" name="{name}" class="bb-json-value" value="{json_attr}" />'
            f'</div>'
        )
        return mark_safe(out)

    def value_from_datadict(self, data, files, name):
        raw = data.get(name, '[]')
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except (ValueError, TypeError):
            pass
        return []


class StepListWidget(forms.Widget):
    """Renders a JSON list of step strings as numbered textarea rows."""

    class Media:
        js = ('admin/js/list_widgets.js',)

    def render(self, name, value, attrs=None, renderer=None):
        items = _parse_list(value)
        cid = f'bb_steps_{uuid.uuid4().hex[:10]}'

        rows = ''
        for i, item in enumerate(items, start=1):
            v = html.escape(str(item), quote=True)
            rows += (
                f'<div class="bb-step-row" style="display:flex;align-items:flex-start;gap:8px;margin-bottom:10px;">'
                f'<span class="bb-step-num" style="min-width:24px;padding-top:7px;font-weight:700;font-size:13px;'
                f'color:#6b7280;text-align:right;">{i}.</span>'
                f'<textarea class="bb-step-input" rows="2" placeholder="{html.escape(str(_("Descreva este passo…")), quote=True)}"'
                f' style="flex:1;{_INPUT_BASE}font-size:14px;resize:vertical;">{v}</textarea>'
                f'<button type="button" onclick="bbRemoveItem(this)" style="{_BTN_REMOVE};margin-top:4px;">×</button>'
                f'</div>'
            )

        json_attr = html.escape(json.dumps(items), quote=True)
        out = (
            f'<div id="{cid}" class="bb-widget-container" data-type="steps" style="{_WRAP}">'
            f'<div class="bb-steps-container">{rows}</div>'
            f'<button type="button" onclick="bbAddStep(\'{cid}\')" style="{_BTN_ADD}">+ {_("Adicionar passo")}</button>'
            f'<input type="hidden" name="{name}" class="bb-json-value" value="{json_attr}" />'
            f'</div>'
        )
        return mark_safe(out)

    def value_from_datadict(self, data, files, name):
        raw = data.get(name, '[]')
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except (ValueError, TypeError):
            pass
        return []
