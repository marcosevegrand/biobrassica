from __future__ import annotations

from typing import Any, cast

from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _


def move_orderable(model, pk, direction, order_field='order'):
    objects = list(model.objects.order_by(order_field, 'pk'))
    index = next((idx for idx, current in enumerate(objects) if current.pk == pk), None)
    if index is None:
        return

    swap_index = index - 1 if direction == 'up' else index + 1
    if swap_index < 0 or swap_index >= len(objects):
        return

    current = objects[index]
    sibling = objects[swap_index]

    current_order = getattr(current, order_field)
    sibling_order = getattr(sibling, order_field)

    if current_order == sibling_order:
        current_order = swap_index
        sibling_order = index

    with transaction.atomic():
        setattr(current, order_field, sibling_order)
        setattr(sibling, order_field, current_order)
        current.save(update_fields=[order_field])
        sibling.save(update_fields=[order_field])


def render_edit_link(opts, obj, title=None):
    title = title or _('Abrir')
    url = reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[obj.pk])
    return format_html(
        '<a href="{}" title="{}" aria-label="{}" '
        'style="display:inline-flex;align-items:center;justify-content:center;width:2rem;height:2rem;'
        'border:1px solid rgba(15,23,42,0.12);border-radius:9999px;text-decoration:none;line-height:1;">'
        '<span class="material-symbols-outlined" style="font-size:18px;line-height:1;">edit</span>'
        '</a>',
        url,
        title,
        title,
    )


def render_order_controls(opts, obj, title_up=None, title_down=None):
    title_up = title_up or _('Mover para cima')
    title_down = title_down or _('Mover para baixo')
    up_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_move_up', args=[obj.pk])
    down_url = reverse(f'admin:{opts.app_label}_{opts.model_name}_move_down', args=[obj.pk])
    return format_html(
        '<span style="display:inline-flex;gap:0.25rem;align-items:center;">'
        '<a href="{}" title="{}" aria-label="{}" '
        'style="display:inline-flex;align-items:center;justify-content:center;width:1.75rem;height:1.75rem;'
        'border:1px solid rgba(15,23,42,0.12);border-radius:9999px;text-decoration:none;line-height:1;">'
        '<span class="material-symbols-outlined" style="font-size:16px;line-height:1;">keyboard_arrow_up</span></a>'
        '<a href="{}" title="{}" aria-label="{}" '
        'style="display:inline-flex;align-items:center;justify-content:center;width:1.75rem;height:1.75rem;'
        'border:1px solid rgba(15,23,42,0.12);border-radius:9999px;text-decoration:none;line-height:1;">'
        '<span class="material-symbols-outlined" style="font-size:16px;line-height:1;">keyboard_arrow_down</span></a>'
        '</span>',
        up_url,
        title_up,
        title_up,
        down_url,
        title_down,
        title_down,
    )


def render_image_preview(image_field, width=56, height=56):
    if not image_field:
        return '—'

    return format_html(
        '<img src="{}" alt="{}" '
        'style="width:{}px;height:{}px;object-fit:cover;border-radius:0.5rem;border:1px solid rgba(15,23,42,0.08);" />',
        image_field.url,
        _('Pré-visualização'),
        width,
        height,
    )


def render_status_badge(label, tone='neutral'):
    palette = {
        'neutral': ('#f1f5f9', '#334155'),
        'info': ('#e0f2fe', '#075985'),
        'success': ('#dcfce7', '#166534'),
        'warning': ('#fef3c7', '#92400e'),
        'danger': ('#ffe4e6', '#be123c'),
    }
    background, foreground = palette.get(tone, palette['neutral'])
    return format_html(
        '<span style="display:inline-flex;align-items:center;padding:0.2rem 0.6rem;border-radius:9999px;'
        'font-size:0.75rem;font-weight:600;background:{};color:{};white-space:nowrap;">{}</span>',
        background,
        foreground,
        label,
    )


def render_summary_panel(title, rows, *, footer=None):
    rendered_rows = format_html_join(
        '',
        (
            '<div style="display:grid;grid-template-columns:minmax(0,11rem) minmax(0,1fr);gap:0.5rem 1rem;padding:0.35rem 0;border-bottom:1px solid rgba(15,23,42,0.06);">'
            '<dt style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">{}</dt>'
            '<dd style="margin:0;color:#0f172a;">{}</dd>'
            '</div>'
        ),
        ((label, value) for label, value in rows),
    )
    footer_html = '' if not footer else format_html(
        '<div style="padding-top:0.75rem;font-size:0.8rem;color:#475569;">{}</div>',
        footer,
    )
    return format_html(
        '<section style="border:1px solid rgba(15,23,42,0.08);border-radius:0.9rem;background:#fff;padding:1rem 1rem 0.75rem;max-width:64rem;">'
        '<h3 style="margin:0 0 0.85rem;font-size:0.95rem;font-weight:700;color:#0f172a;">{}</h3>'
        '<dl style="margin:0;">{}</dl>{}'
        '</section>',
        title,
        rendered_rows,
        footer_html,
    )


class DefaultLanguageInlineMixin:
    default_language = 'pt'

    def get_formset(self, request, obj=None, **kwargs):
        formset = cast(Any, super()).get_formset(request, obj, **kwargs)
        if obj is None or not obj.pk:
            language_field = formset.form.base_fields.get('language')
            if language_field is not None:
                language_field.initial = self.default_language
        return formset


class EditLinkAdminMixin:
    opts: Any

    def get_list_display(self, request):
        list_display = list(cast(Any, super()).get_list_display(request))
        if 'edit_link' not in list_display:
            return list_display

        list_display = [field for field in list_display if field != 'edit_link']
        insert_at = 1 if list_display and list_display[0] == 'order_controls' else 0
        list_display.insert(insert_at, 'edit_link')
        return list_display

    @admin.display(description='')
    def edit_link(self, obj):
        return render_edit_link(self.opts, obj)


class WorkflowAdminMixin:
    change_form_show_cancel_button = False

    def get_changeform_custom_tools(self, request, obj):
        return []

    def get_changeform_submit_actions(self, request, obj):
        return []

    def _normalize_submit_action(self, action):
        attrs = dict(action.get('attrs') or {})
        return {
            **action,
            'attrs': attrs,
            'button_name': attrs.get('name') or action.get('action_name', ''),
        }

    def _get_normalized_submit_actions(self, request, obj):
        return [
            self._normalize_submit_action(action)
            for action in self.get_changeform_submit_actions(request, obj)
        ]

    def handle_changeform_submit_action(self, request, obj, action_name) -> Any:
        return None

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        obj = None
        if object_id is not None:
            obj = self.get_object(request, unquote(object_id))

        if request.method == 'POST' and obj is not None:
            action_names = {
                action.get('action_name')
                for action in self._get_normalized_submit_actions(request, obj)
                if action.get('action_name')
            }
            for action_name in action_names:
                if action_name in request.POST:
                    response = self.handle_changeform_submit_action(request, obj, action_name)
                    if response is not None:
                        return response
                    break

        return super().changeform_view(request, object_id=object_id, form_url=form_url, extra_context=extra_context)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        custom_tools = list(context.get('custom_object_tools') or [])
        submit_actions = list(context.get('actions_submit_line') or [])

        if obj is not None:
            custom_tools.extend(self.get_changeform_custom_tools(request, obj))
            submit_actions.extend(self._get_normalized_submit_actions(request, obj))

        context['custom_object_tools'] = custom_tools
        context['actions_submit_line'] = submit_actions
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)


class OrderableAdminMixin:
    order_field = 'order'
    admin_site: Any
    model: Any
    opts: Any

    def get_urls(self):
        extra_urls = [
            path(
                '<int:pk>/move-up/',
                self.admin_site.admin_view(self._move_up),
                name=f'{self.opts.app_label}_{self.opts.model_name}_move_up',
            ),
            path(
                '<int:pk>/move-down/',
                self.admin_site.admin_view(self._move_down),
                name=f'{self.opts.app_label}_{self.opts.model_name}_move_down',
            ),
        ]
        return extra_urls + cast(Any, super()).get_urls()

    def _redirect_to_changelist(self):
        return HttpResponseRedirect(reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_changelist'))

    def _move_up(self, request, pk):
        move_orderable(self.model, pk, 'up', order_field=self.order_field)
        return self._redirect_to_changelist()

    def _move_down(self, request, pk):
        move_orderable(self.model, pk, 'down', order_field=self.order_field)
        return self._redirect_to_changelist()

    @admin.display(description='Ordem')
    def order_controls(self, obj):
        return render_order_controls(self.opts, obj)
