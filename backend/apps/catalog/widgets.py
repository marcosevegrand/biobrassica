import json

from django import forms
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from apps.catalog.models import PICKUP_HOURS_WEEKDAY_KEYS, PICKUP_HOURS_WEEKDAY_LABELS, PICKUP_TIME_SLOTS


class PickupScheduleWidget(forms.Widget):
    template_name = 'admin/widgets/pickup_schedule.html'

    class Media:
        js = ('js/admin/pickup_schedule.js',)

    def format_value(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = {}
        return value or {}

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        formatted = self.format_value(value)
        context['widget'].update(
            {
                'value_json': json.dumps(formatted),
                'days': [
                    {
                        'key': key,
                        'label': str(PICKUP_HOURS_WEEKDAY_LABELS[key]),
                        'selected': set(formatted.get(key, [])),
                    }
                    for key in PICKUP_HOURS_WEEKDAY_KEYS
                ],
                'slots': PICKUP_TIME_SLOTS,
            }
        )
        return context

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        return mark_safe(render_to_string(self.template_name, context))


class PickupLocationSelectWidget(forms.CheckboxSelectMultiple):
    template_name = 'admin/widgets/pickup_locations.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        choices = []
        for group_name, group_options, group_index in context['widget']['optgroups']:
            for option in group_options:
                choices.append(option)
        context['widget']['flat_choices'] = choices
        return context

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        return mark_safe(render_to_string(self.template_name, context))
