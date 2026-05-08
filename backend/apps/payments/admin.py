import json

from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from unfold.admin import ModelAdmin

from apps.core.admin_helpers import (
    EditLinkAdminMixin,
    WorkflowAdminMixin,
    render_action_group,
    render_action_link,
    render_status_badge,
    render_summary_panel,
)
from apps.orders.models import Order
from apps.orders.services import OrderWorkflowError
from apps.payments.models import Payment
from apps.payments.services import (
    cancel_payment,
    PaymentTransitionError,
    finalize_successful_payment,
    transition_payment_status,
)


class PaymentAdminForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['provider_data'].required = False
        self.fields['last_error'].required = False
        self.fields['checkout_url'].required = False
        self.fields['provider_reference'].required = False
        self.fields['provider_payment_id'].required = False
        self.fields['expires_at'].required = False
        self.fields['paid_at'].required = False
        self.fields['last_error'].widget.attrs.setdefault('rows', 3)

        if self.instance.pk:
            allowed_statuses = {self.instance.status, *self.instance.valid_next_statuses()}
        else:
            allowed_statuses = {
                Payment.Status.PENDING,
                Payment.Status.CONFIRMED,
                Payment.Status.CANCELLED,
            }
            self.initial.setdefault('status', Payment.Status.PENDING)

        self.fields['status'].choices = [
            choice for choice in Payment.Status.choices if choice[0] in allowed_statuses
        ]

    def clean(self):
        cleaned_data = super().clean()
        order = cleaned_data.get('order')
        status = cleaned_data.get('status') or Payment.Status.PENDING
        if order is None:
            return cleaned_data

        if Payment.objects.filter(order=order).exclude(pk=self.instance.pk).exists():
            self.add_error('order', _('A encomenda selecionada já tem um pagamento associado.'))

        if order.status == Order.Status.CANCELLED and status != Payment.Status.CANCELLED:
            self.add_error('order', _('A encomenda selecionada foi cancelada e já não aceita este estado de pagamento.'))

        if status == Payment.Status.CONFIRMED and order.status == Order.Status.CANCELLED:
            self.add_error('status', _('Não pode confirmar um pagamento numa encomenda cancelada.'))

        return cleaned_data


@admin.register(Payment)
class PaymentAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    form = PaymentAdminForm
    list_display = ('__str__', 'order', 'method_display', 'status_badge', 'amount', 'paid_at', 'created_at', 'edit_link')
    list_filter = ('method', 'status', 'created_at')
    actions = ('approve_pending_payments', 'reject_pending_payments')
    search_fields = ('=order__pk',)
    search_help_text = _('Pesquise pelo número da encomenda.')
    readonly_fields = ()
    list_filter_submit = True
    compressed_fields = True
    autocomplete_fields = ('order',)

    add_fieldsets = (
        (None, {
            'fields': (
                'order',
                'method',
                'status',
                'amount',
                'provider_reference',
                'provider_payment_id',
                'checkout_url',
                'expires_at',
                'provider_data',
                'last_error',
                'paid_at',
            ),
        }),
    )

    fieldsets = (
        (None, {
            'fields': (
                'order',
                'method',
                'status',
                'amount',
                'provider_reference',
                'provider_payment_id',
                'checkout_url',
                'expires_at',
                'provider_data',
                'last_error',
                'paid_at',
            ),
        }),
    )

    def get_urls(self):
        custom_urls = [
            path(
                '<int:object_id>/status/<slug:target_status>/',
                self.admin_site.admin_view(self.status_view),
                name='payments_payment_status',
            ),
        ]
        return custom_urls + super().get_urls()

    def get_fieldsets(self, request, obj=None):
        return self.add_fieldsets if obj is None else self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        return ()

    def _is_pending_manual(self, payment):
        return payment.status == Payment.Status.PENDING and payment.method in {Payment.Method.MBWAY_MANUAL, Payment.Method.BANK_TRANSFER}

    def _sync_order_payment_state(self, payment, target_payment_state):
        if payment.order.payment_state != target_payment_state:
            from apps.orders.services import transition_payment_state

            try:
                transition_payment_state(payment.order, target_payment_state)
            except Exception:
                pass

    def _apply_payment_status(self, payment, target_status, *, reason=''):
        if payment.status == target_status:
            if target_status == Payment.Status.PENDING:
                self._sync_order_payment_state(payment, Order.PaymentState.PENDING)
            return False

        if target_status == Payment.Status.CONFIRMED:
            self._sync_order_payment_state(payment, Order.PaymentState.CONFIRMED)
            return finalize_successful_payment(payment, source='admin_manual_update')

        if target_status == Payment.Status.CANCELLED:
            self._sync_order_payment_state(payment, Order.PaymentState.CANCELLED)
            return cancel_payment(payment, reason=reason or _('Pagamento cancelado no backoffice.'), source='admin_manual_update')

        if target_status == Payment.Status.PENDING:
            changed = transition_payment_status(payment, Payment.Status.PENDING, source='admin_manual_update')
            self._sync_order_payment_state(payment, Order.PaymentState.PENDING)
            return changed

        if target_status == Payment.Status.REFUNDED:
            self._sync_order_payment_state(payment, Order.PaymentState.REFUNDED)
            return transition_payment_status(payment, Payment.Status.REFUNDED, source='admin_manual_update')

        raise PaymentTransitionError(_('Estado de pagamento inválido.'))

    def _process_manual_action(self, request, queryset, *, approve: bool):
        success_count = 0
        skipped_count = 0
        error_count = 0
        rejection_reason = 'Pagamento cancelado no backoffice.'

        for payment in queryset.select_related('order'):
            try:
                with transaction.atomic():
                    locked = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
                    if not self._is_pending_manual(locked):
                        skipped_count += 1
                        continue

                    if approve:
                        if finalize_successful_payment(locked, source='admin_manual_approval'):
                            success_count += 1
                        else:
                            skipped_count += 1
                        continue

                    if not cancel_payment(locked, reason=rejection_reason, source='admin_manual_rejection'):
                        skipped_count += 1
                        continue

                    success_count += 1
            except (OrderWorkflowError, PaymentTransitionError):
                error_count += 1

        if success_count:
            message = (
                _('{} pagamento(s) aprovado(s).').format(success_count)
                if approve
                else _('{} pagamento(s) rejeitado(s).').format(success_count)
            )
            self.message_user(request, message, level=messages.SUCCESS)
        if skipped_count:
            self.message_user(
                request,
                _('{} pagamento(s) ignorado(s) por não estarem pendentes.').format(skipped_count),
                level=messages.WARNING,
            )
        if error_count:
            self.message_user(
                request,
                _('{} pagamento(s) não puderam ser atualizados.').format(error_count),
                level=messages.WARNING,
            )

    def get_changeform_submit_actions(self, request, obj):
        if obj is None or not self._is_pending_manual(obj):
            return []
        return [
            {'action_name': '_approve_payment', 'description': _('Aprovar pagamento')},
            {'action_name': '_reject_payment', 'description': _('Rejeitar pagamento')},
        ]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if obj is None:
            return None
        if action_name == '_approve_payment':
            self._process_manual_action(request, Payment.objects.filter(pk=obj.pk), approve=True)
            return HttpResponseRedirect(request.path)
        if action_name == '_reject_payment':
            self._process_manual_action(request, Payment.objects.filter(pk=obj.pk), approve=False)
            return HttpResponseRedirect(request.path)
        return None

    def save_model(self, request, obj, form, change):
        desired_status = form.cleaned_data['status']
        desired_paid_at = form.cleaned_data.get('paid_at')

        if change:
            original_status = getattr(obj, '_original_status', obj.status)
            if desired_status != original_status:
                obj.status = original_status
                if original_status == Payment.Status.CONFIRMED and obj.paid_at is None:
                    obj.paid_at = Payment.objects.only('paid_at').get(pk=obj.pk).paid_at
                elif original_status != Payment.Status.CONFIRMED:
                    obj.paid_at = None
            super().save_model(request, obj, form, change)
            if desired_status != original_status:
                self._apply_payment_status(obj, desired_status, reason=form.cleaned_data.get('last_error', ''))
                if desired_status == Payment.Status.CONFIRMED and desired_paid_at is not None and obj.paid_at != desired_paid_at:
                    obj.paid_at = desired_paid_at
                    obj.save(update_fields=['paid_at'])
            elif desired_status == Payment.Status.PENDING:
                self._sync_order_payment_state(obj, Order.PaymentState.PENDING)
            return

        if desired_status != Payment.Status.PENDING:
            obj.status = Payment.Status.PENDING
            obj.paid_at = None
        super().save_model(request, obj, form, change)

        if desired_status != Payment.Status.PENDING:
            self._apply_payment_status(obj, desired_status, reason=form.cleaned_data.get('last_error', ''))
            if desired_status == Payment.Status.CONFIRMED and desired_paid_at is not None and obj.paid_at != desired_paid_at:
                obj.paid_at = desired_paid_at
                obj.save(update_fields=['paid_at'])
        else:
            self._sync_order_payment_state(obj, Order.PaymentState.PENDING)

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description=_('Estado'))
    def status_badge(self, obj):
        tones = {
            Payment.Status.PENDING: 'warning',
            Payment.Status.CONFIRMED: 'success',
            Payment.Status.CANCELLED: 'danger',
            Payment.Status.REFUNDED: 'info',
        }
        return render_status_badge(obj.get_status_display(), tones.get(obj.status, 'neutral'))

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__user')

    def get_changeform_custom_tools(self, request, obj):
        return []

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_superuser)

    @require_http_methods(['POST'])
    def status_view(self, request, object_id, target_status):
        payment = self.get_object(request, object_id)
        if payment is None:
            self.message_user(request, _('Pagamento não encontrado.'), level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:payments_payment_changelist'))

        try:
            target_label = Payment.Status(target_status).label
        except ValueError:
            self.message_user(request, _('Estado de pagamento inválido.'), level=messages.ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('admin:payments_payment_changelist'))

        try:
            with transaction.atomic():
                locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
                changed = self._apply_payment_status(locked_payment, target_status)
        except (OrderWorkflowError, PaymentTransitionError, ValidationError) as error:
            self.message_user(request, str(error), level=messages.WARNING)
        else:
            if changed:
                self.message_user(
                    request,
                    _('Pagamento atualizado para %(status)s.') % {'status': target_label},
                    level=messages.SUCCESS,
                )
        return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('admin:payments_payment_changelist'))

    @admin.display(description=_('Cliente'))
    def customer_display(self, obj):
        return format_html('<strong>{}</strong><br><span style="color:#64748b;">{}</span>', obj.order.name, obj.order.masked_contact)

    @admin.display(ordering='method', description=_('Método'))
    def method_display(self, obj):
        return obj.method_label

    @admin.display(description=_('Ações rápidas'))
    def quick_actions(self, obj):
        actions = []
        if obj.status == Payment.Status.PENDING:
            actions.extend([
                render_action_link(reverse('admin:payments_payment_status', args=[obj.pk, Payment.Status.CONFIRMED]), _('Confirmar'), tone='success'),
                render_action_link(reverse('admin:payments_payment_status', args=[obj.pk, Payment.Status.CANCELLED]), _('Cancelar'), tone='danger'),
            ])
        elif obj.status == Payment.Status.CANCELLED:
            actions.append(
                render_action_link(
                    reverse('admin:payments_payment_status', args=[obj.pk, Payment.Status.PENDING]),
                    _('Reabrir'),
                    tone='info',
                )
            )
        elif obj.status == Payment.Status.CONFIRMED:
            actions.append(
                render_action_link(
                    reverse('admin:payments_payment_status', args=[obj.pk, Payment.Status.REFUNDED]),
                    _('Reembolsar'),
                    tone='warning',
                )
            )
        return render_action_group(actions)

    @admin.display(description=_('Dados do provedor'))
    def provider_data_display(self, obj):
        provider_data = obj.provider_data if isinstance(obj.provider_data, dict) else {}
        if not provider_data:
            return '—'

        if obj.method == Payment.Method.MBWAY_MANUAL:
            return render_summary_panel(
                _('Resumo MB WAY'),
                [
                    (_('Número MB WAY'), provider_data.get('mbway_number') or '—'),
                    (_('Referência'), provider_data.get('order_reference') or '—'),
                ],
            )
        if obj.method == Payment.Method.BANK_TRANSFER:
            return render_summary_panel(
                _('Resumo da transferência'),
                [
                    (_('Beneficiário'), provider_data.get('beneficiary') or '—'),
                    (_('IBAN'), provider_data.get('iban') or '—'),
                    (_('BIC'), provider_data.get('bic') or '—'),
                    (_('Referência'), provider_data.get('order_reference') or '—'),
                ],
            )

        return format_html('<pre style="white-space:pre-wrap;max-width:48rem;">{}</pre>', json.dumps(provider_data, ensure_ascii=False, indent=2))

    @admin.display(description=_('Resumo da encomenda'))
    def order_summary(self, obj):
        order = obj.order
        return render_summary_panel(
            _('Encomenda associada'),
            [
                (_('Encomenda'), f'#{order.pk}'),
                (_('Cliente'), order.name),
                (_('Estado'), order.get_status_display()),
                (_('Entrega'), order.get_fulfillment_method_display()),
                (_('Total'), f'{order.total:.2f}€'),
            ],
        )

    @admin.action(description=_('Aprovar pagamentos pendentes'))
    def approve_pending_payments(self, request, queryset):
        self._process_manual_action(request, queryset, approve=True)

    @admin.action(description=_('Rejeitar pagamentos pendentes'))
    def reject_pending_payments(self, request, queryset):
        self._process_manual_action(request, queryset, approve=False)
