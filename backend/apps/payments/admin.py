import json

from django.contrib import admin, messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.orders.services import OrderWorkflowError, cancel_unpaid_order
from apps.payments.models import Payment
from apps.payments.services import (
    PaymentTransitionError,
    finalize_successful_payment,
    mark_payment_failed,
    schedule_manual_payment_rejection_notification,
)
from apps.core.admin_helpers import EditLinkAdminMixin, WorkflowAdminMixin, render_status_badge, render_summary_panel


@admin.register(Payment)
class PaymentAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_display = ('__str__', 'order', 'customer_display', 'method_display', 'status_badge', 'amount', 'paid_at', 'created_at', 'edit_link')
    list_filter = ('method', 'status', 'created_at')
    actions = ('approve_pending_payments', 'reject_pending_payments')
    search_fields = ('=order__pk',)
    search_help_text = _('Pesquise pelo número da encomenda.')
    readonly_fields = (
        'order', 'customer_display', 'status_badge', 'order_summary', 'method_display', 'amount',
        'provider_data_display', 'last_error', 'paid_at', 'created_at',
    )
    list_filter_submit = True
    compressed_fields = True
    fieldsets = (
        (_('Operação'), {
            'fields': ('order', 'customer_display', 'status_badge', 'order_summary'),
        }),
        (_('Dados do pagamento'), {
            'fields': ('method_display', 'amount', 'provider_data_display'),
        }),
        (_('Auditoria'), {
            'fields': ('paid_at', 'created_at', 'last_error'),
        }),
    )

    def _is_pending_manual(self, payment):
        return payment.status == Payment.Status.PENDING and payment.method in {Payment.Method.MBWAY_MANUAL, Payment.Method.BANK_TRANSFER}

    def _process_manual_action(self, request, queryset, *, approve: bool):
        success_count = 0
        skipped_count = 0
        error_count = 0
        rejection_reason = 'Pagamento rejeitado no backoffice.'

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

                    if not mark_payment_failed(locked, reason=rejection_reason):
                        skipped_count += 1
                        continue

                    cancel_unpaid_order(locked.order)
                    schedule_manual_payment_rejection_notification(locked, reason=rejection_reason)
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

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:payments_payment_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': _('Pendentes'), 'value': queryset.filter(status=Payment.Status.PENDING).count(), 'context': _('A aguardar validação manual'), 'link': f'{base_url}?status__exact={Payment.Status.PENDING}'},
                {'label': _('Pagos'), 'value': queryset.filter(status=Payment.Status.PAID).count(), 'context': _('Confirmados'), 'link': f'{base_url}?status__exact={Payment.Status.PAID}'},
                {'label': _('Falhados'), 'value': queryset.filter(status=Payment.Status.FAILED).count(), 'context': _('Rever motivos'), 'link': f'{base_url}?status__exact={Payment.Status.FAILED}'},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description=_('Estado'))
    def status_badge(self, obj):
        tones = {
            Payment.Status.PENDING: 'warning',
            Payment.Status.PAID: 'success',
            Payment.Status.FAILED: 'danger',
            Payment.Status.EXPIRED: 'neutral',
            Payment.Status.REFUNDED: 'info',
        }
        return render_status_badge(obj.get_status_display(), tones.get(obj.status, 'neutral'))

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__user')

    def get_changeform_custom_tools(self, request, obj):
        return [
            {
                'title': _('Abrir encomenda'),
                'link': reverse('admin:orders_order_change', args=[obj.order_id]),
                'icon': 'shopping_bag',
                'blank': False,
            },
        ]

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_('Cliente'))
    def customer_display(self, obj):
        return format_html('<strong>{}</strong><br><span style="color:#64748b;">{}</span>', obj.order.name, obj.order.masked_contact)

    @admin.display(ordering='method', description=_('Método'))
    def method_display(self, obj):
        return obj.method_label

    @admin.display(description=_('Dados do provedor'))
    def provider_data_display(self, obj):
        provider_data = obj.provider_data if isinstance(obj.provider_data, dict) else {}
        if not provider_data:
            return '—'

        if obj.method == Payment.Method.MBWAY_MANUAL:
            return render_summary_panel(
                _('Snapshot MB WAY'),
                [
                    (_('Número MB WAY'), provider_data.get('mbway_number') or '—'),
                    (_('Referência'), provider_data.get('order_reference') or '—'),
                ],
            )
        if obj.method == Payment.Method.BANK_TRANSFER:
            return render_summary_panel(
                _('Snapshot transferência'),
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
