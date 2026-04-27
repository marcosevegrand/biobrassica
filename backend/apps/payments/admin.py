import json

from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from apps.orders.services import OrderWorkflowError, cancel_unpaid_order
from apps.payments.models import Payment, PaymentCallback
from apps.payments.services import (
    PaymentTransitionError,
    finalize_successful_payment,
    mark_payment_failed,
    schedule_manual_payment_rejection_notification,
)
from apps.core.admin_helpers import EditLinkAdminMixin, WorkflowAdminMixin, render_status_badge, render_summary_panel


class PaymentCallbackInline(TabularInline):
    model = PaymentCallback
    extra = 0
    can_delete = False
    max_num = 5
    readonly_fields = ('created_at', 'validation_badge', 'validation_message', 'anonymized_ip_display', 'sanitized_payload_display')
    fields = ('created_at', 'validation_badge', 'validation_message', 'anonymized_ip_display', 'sanitized_payload_display')
    show_change_link = True

    @admin.display(description=_('Validação'))
    def validation_badge(self, obj):
        tone = 'success' if obj.is_valid else 'danger'
        label = _('Válido') if obj.is_valid else _('Inválido')
        return render_status_badge(label, tone)

    @admin.display(description=_('IP'))
    def anonymized_ip_display(self, obj):
        return obj.ip_address

    @admin.display(description=_('Payload'))
    def sanitized_payload_display(self, obj):
        return format_html('<pre style="white-space:pre-wrap;max-width:48rem;">{}</pre>', json.dumps(obj.raw_payload, ensure_ascii=False, indent=2))


@admin.register(Payment)
class PaymentAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/payments/payment/workflow_overview.html'
    list_display = ('__str__', 'order', 'customer_display', 'method_display', 'status_badge', 'callback_health_display', 'provider_identifier_display', 'amount', 'expires_at', 'paid_at', 'created_at', 'edit_link')
    list_filter = ('method', 'status', 'created_at')
    actions = ('approve_manual_mbway_payments', 'reject_manual_mbway_payments')
    search_fields = ('=order__pk', 'provider_reference', 'provider_payment_id')
    search_help_text = _('Pesquise por encomenda ou identificadores do provedor.')
    readonly_fields = (
        'order', 'customer_display', 'status_badge', 'order_summary', 'callback_health_summary', 'method_display', 'amount',
        'provider_reference_display', 'provider_payment_id_display', 'provider_data_display', 'checkout_url', 'last_error', 'expires_at', 'paid_at', 'created_at',
    )
    list_filter_submit = True
    compressed_fields = True
    inlines = [PaymentCallbackInline]
    fieldsets = (
        (_('Operação'), {
            'fields': ('order', 'customer_display', 'status_badge', 'order_summary', 'callback_health_summary'),
        }),
        (_('Dados do pagamento'), {
            'fields': ('method_display', 'amount', 'provider_reference_display', 'provider_payment_id_display', 'provider_data_display', 'checkout_url'),
        }),
        (_('Auditoria'), {
            'fields': ('expires_at', 'paid_at', 'created_at', 'last_error'),
        }),
    )

    def _is_manual_mbway_pending(self, payment):
        return payment.method == Payment.Method.MBWAY_MANUAL and payment.status == Payment.Status.PENDING

    def _process_manual_mbway_action(self, request, queryset, *, approve: bool):
        success_count = 0
        skipped_count = 0
        error_count = 0
        rejection_reason = 'Pagamento MB WAY manual rejeitado no backoffice.'

        for payment in queryset.select_related('order'):
            try:
                with transaction.atomic():
                    locked_payment = Payment.objects.select_for_update().select_related('order').get(pk=payment.pk)
                    if not self._is_manual_mbway_pending(locked_payment):
                        skipped_count += 1
                        continue

                    if approve:
                        if finalize_successful_payment(locked_payment, source='admin_manual_mbway_approval'):
                            success_count += 1
                        else:
                            skipped_count += 1
                        continue

                    if not mark_payment_failed(locked_payment, reason=rejection_reason):
                        skipped_count += 1
                        continue

                    cancel_unpaid_order(locked_payment.order)
                    schedule_manual_payment_rejection_notification(locked_payment, reason=rejection_reason)
                    success_count += 1
            except (OrderWorkflowError, PaymentTransitionError):
                error_count += 1

        if success_count:
            message = (
                _('{} pagamento(s) MB WAY manual aprovado(s).').format(success_count)
                if approve
                else _('{} pagamento(s) MB WAY manual rejeitado(s).').format(success_count)
            )
            self.message_user(request, message, level=messages.SUCCESS)
        if skipped_count:
            self.message_user(
                request,
                _('{} pagamento(s) ignorado(s) por não estarem pendentes em MB WAY manual.').format(skipped_count),
                level=messages.WARNING,
            )
        if error_count:
            self.message_user(
                request,
                _('{} pagamento(s) não puderam ser atualizados.').format(error_count),
                level=messages.WARNING,
            )

    def get_changeform_submit_actions(self, request, obj):
        if obj is None or not self._is_manual_mbway_pending(obj):
            return []
        return [
            {'action_name': '_approve_manual_mbway', 'description': _('Aprovar pagamento MB WAY manual')},
            {'action_name': '_reject_manual_mbway', 'description': _('Rejeitar pagamento MB WAY manual')},
        ]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if obj is None:
            return None

        if action_name == '_approve_manual_mbway':
            self._process_manual_mbway_action(request, Payment.objects.filter(pk=obj.pk), approve=True)
            return HttpResponseRedirect(request.path)

        if action_name == '_reject_manual_mbway':
            self._process_manual_mbway_action(request, Payment.objects.filter(pk=obj.pk), approve=False)
            return HttpResponseRedirect(request.path)

        return None

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:payments_payment_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': _('Pendentes'), 'value': queryset.filter(status=Payment.Status.PENDING).count(), 'context': _('Acompanhar cobranças'), 'link': f'{base_url}?status__exact={Payment.Status.PENDING}'},
                {'label': _('Expirados'), 'value': queryset.filter(status=Payment.Status.EXPIRED).count(), 'context': _('Verificar recuperação'), 'link': f'{base_url}?status__exact={Payment.Status.EXPIRED}'},
                {'label': _('Falhados'), 'value': queryset.filter(status=Payment.Status.FAILED).count(), 'context': _('Rever erros'), 'link': f'{base_url}?status__exact={Payment.Status.FAILED}'},
                {'label': _('Callbacks inválidos'), 'value': queryset.filter(invalid_callback_count__gt=0).count(), 'context': _('Requer investigação'), 'link': reverse('admin:payments_paymentcallback_changelist') + '?is_valid__exact=0'},
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
        return super().get_queryset(request).select_related('order', 'order__user').annotate(
            callback_count=Count('callbacks', distinct=True),
            invalid_callback_count=Count('callbacks', filter=Q(callbacks__is_valid=False), distinct=True),
        )

    def get_changeform_custom_tools(self, request, obj):
        tools = [
            {
                'title': _('Abrir encomenda'),
                'link': reverse('admin:orders_order_change', args=[obj.order_id]),
                'icon': 'shopping_bag',
                'blank': False,
            },
            {
                'title': _('Ver callbacks'),
                'link': reverse('admin:payments_paymentcallback_changelist') + f'?payment__id__exact={obj.pk}',
                'icon': 'receipt_long',
                'blank': False,
            },
        ]
        if obj.checkout_url:
            tools.append({
                'title': _('Abrir checkout'),
                'link': obj.checkout_url,
                'icon': 'open_in_new',
                'blank': True,
            })
        return tools

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_('Cliente'))
    def customer_display(self, obj):
        return format_html('<strong>{}</strong><br><span style="color:#64748b;">{}</span>', obj.order.name, obj.order.masked_contact)

    @admin.display(ordering='method', description=_('Método'))
    def method_display(self, obj):
        return obj.method_label

    @admin.display(description=_('Referência do provedor'))
    def provider_reference_display(self, obj):
        return obj.masked_provider_reference or '—'

    @admin.display(description=_('ID do pagamento no provedor'))
    def provider_payment_id_display(self, obj):
        return obj.masked_provider_payment_id or '—'

    @admin.display(description=_('Dados do provedor'))
    def provider_data_display(self, obj):
        provider_data = obj.provider_data if isinstance(obj.provider_data, dict) else {}
        if not provider_data:
            return '—'

        if obj.method == Payment.Method.MBWAY_MANUAL:
            return render_summary_panel(
                _('Snapshot MB WAY manual'),
                [
                    (_('Número MB WAY'), provider_data.get('mbway_number') or '—'),
                    (_('Referência'), provider_data.get('order_reference') or '—'),
                ],
                footer=_('O número MB WAY fica guardado no pagamento para preservar as instruções vistas pelo cliente no checkout.'),
            )

        return format_html('<pre style="white-space:pre-wrap;max-width:48rem;">{}</pre>', json.dumps(provider_data, ensure_ascii=False, indent=2))

    @admin.display(ordering='provider_reference', description=_('ID do provedor'))
    def provider_identifier_display(self, obj):
        return obj.masked_provider_identifier or '—'

    @admin.display(ordering='invalid_callback_count', description=_('Callbacks'))
    def callback_health_display(self, obj):
        invalid_count = getattr(obj, 'invalid_callback_count', 0)
        if invalid_count:
            return render_status_badge(_('{} inválido(s)').format(invalid_count), 'danger')
        count = getattr(obj, 'callback_count', 0)
        if count:
            return render_status_badge(_('{} recebido(s)').format(count), 'info')
        return render_status_badge(_('Sem callbacks'), 'neutral')

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

    @admin.display(description=_('Saúde de callback'))
    def callback_health_summary(self, obj):
        invalid_count = getattr(obj, 'invalid_callback_count', obj.callbacks.filter(is_valid=False).count())
        total_count = getattr(obj, 'callback_count', obj.callbacks.count())
        latest_callback = obj.callbacks.order_by('-created_at').first()
        return render_summary_panel(
            _('Callbacks do provedor'),
            [
                (_('Recebidos'), total_count),
                (_('Inválidos'), invalid_count),
                (_('Último callback'), latest_callback.created_at.strftime('%d/%m/%Y %H:%M') if latest_callback else '—'),
                (_('Último motivo'), latest_callback.validation_message or '—' if latest_callback else '—'),
            ],
            footer=_('Use o atalho superior para abrir a lista filtrada de callbacks desta cobrança.'),
        )

    @admin.action(description=_('Aprovar pagamentos MB WAY manual'))
    def approve_manual_mbway_payments(self, request, queryset):
        self._process_manual_mbway_action(request, queryset, approve=True)

    @admin.action(description=_('Rejeitar pagamentos MB WAY manual'))
    def reject_manual_mbway_payments(self, request, queryset):
        self._process_manual_mbway_action(request, queryset, approve=False)


@admin.register(PaymentCallback)
class PaymentCallbackAdmin(EditLinkAdminMixin, ModelAdmin):
    list_display = ('pk', 'payment', 'validation_badge', 'validation_message', 'anonymized_ip_display', 'created_at', 'edit_link')
    list_filter = ('is_valid', 'created_at')
    readonly_fields = ('payment', 'sanitized_payload_display', 'anonymized_ip_display', 'is_valid', 'validation_message', 'created_at')
    search_fields = ('=payment__order__pk', 'payment__provider_reference', 'payment__provider_payment_id', 'provider_event_id', 'validation_message')
    list_filter_submit = True
    compressed_fields = True

    @admin.display(description=_('Validação'))
    def validation_badge(self, obj):
        tone = 'success' if obj.is_valid else 'danger'
        label = _('Válido') if obj.is_valid else _('Inválido')
        return render_status_badge(label, tone)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment', 'payment__order')

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_('IP'))
    def anonymized_ip_display(self, obj):
        return obj.ip_address

    @admin.display(description=_('Payload sanitizado'))
    def sanitized_payload_display(self, obj):
        return format_html('<pre style="white-space:pre-wrap;max-width:48rem;">{}</pre>', json.dumps(obj.raw_payload, ensure_ascii=False, indent=2))
