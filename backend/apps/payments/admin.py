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
from apps.orders.services import OrderWorkflowError, cancel_unpaid_order
from apps.payments.models import Payment
from apps.payments.services import (
    PaymentTransitionError,
    finalize_successful_payment,
    mark_payment_failed,
    schedule_manual_payment_rejection_notification,
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
                Payment.Status.PAID,
                Payment.Status.FAILED,
                Payment.Status.EXPIRED,
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

        if status == Payment.Status.PAID and order.status == Order.Status.CANCELLED:
            self.add_error('status', _('Não pode registar um pagamento pago numa encomenda cancelada.'))

        if status in {Payment.Status.PENDING, Payment.Status.FAILED, Payment.Status.EXPIRED} and order.status in {
            Order.Status.CANCELLED,
            Order.Status.PAID,
            Order.Status.PREPARING,
            Order.Status.READY,
            Order.Status.IN_TRANSIT,
            Order.Status.DELIVERED,
        }:
            self.add_error('order', _('Escolha uma encomenda ainda não fechada para este estado de pagamento.'))

        return cleaned_data


@admin.register(Payment)
class PaymentAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    form = PaymentAdminForm
    list_display = ('__str__', 'order', 'customer_display', 'method_display', 'status_badge', 'amount', 'paid_at', 'created_at', 'quick_actions', 'edit_link')
    list_filter = ('method', 'status', 'created_at')
    actions = ('approve_pending_payments', 'reject_pending_payments')
    search_fields = ('=order__pk',)
    search_help_text = _('Pesquise pelo número da encomenda.')
    readonly_fields = ('customer_display', 'order_summary', 'created_at')
    list_filter_submit = True
    compressed_fields = True
    autocomplete_fields = ('order',)

    add_fieldsets = (
        (_('Pagamento'), {
            'fields': ('order', 'method', 'status', 'amount'),
        }),
        (_('Referências e prazos'), {
            'fields': ('provider_reference', 'provider_payment_id', 'checkout_url', 'expires_at'),
        }),
        (_('Dados adicionais'), {
            'fields': ('provider_data', 'last_error', 'paid_at'),
        }),
    )

    fieldsets = (
        (_('Operação'), {
            'fields': ('order', 'customer_display', 'status', 'order_summary'),
        }),
        (_('Dados do pagamento'), {
            'fields': ('method', 'amount', 'provider_reference', 'provider_payment_id', 'checkout_url', 'expires_at', 'provider_data'),
        }),
        (_('Auditoria'), {
            'fields': ('paid_at', 'created_at', 'last_error'),
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
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return super().get_readonly_fields(request, obj)

    def _is_pending_manual(self, payment):
        return payment.status == Payment.Status.PENDING and payment.method in {Payment.Method.MBWAY_MANUAL, Payment.Method.BANK_TRANSFER}

    def _ensure_order_ready_for_paid_payment(self, payment):
        order = payment.order
        if order.status == Order.Status.PENDING:
            transition_payment_status(payment, Payment.Status.PENDING, source='admin_prepare_payment')
            from apps.orders.services import transition_order_status

            transition_order_status(order, Order.Status.PAYMENT_PENDING)

    def _sync_order_for_pending_payment(self, payment):
        if payment.order.status == Order.Status.PENDING:
            from apps.orders.services import transition_order_status

            transition_order_status(payment.order, Order.Status.PAYMENT_PENDING)

    def _apply_payment_status(self, payment, target_status, *, reason=''):
        if payment.status == target_status:
            if target_status == Payment.Status.PENDING:
                self._sync_order_for_pending_payment(payment)
            return False

        if target_status == Payment.Status.PAID:
            self._ensure_order_ready_for_paid_payment(payment)
            return finalize_successful_payment(payment, source='admin_manual_update')

        if target_status == Payment.Status.FAILED:
            return mark_payment_failed(payment, reason=reason or _('Pagamento marcado como falhado no backoffice.'))

        if target_status == Payment.Status.EXPIRED:
            changed = transition_payment_status(
                payment,
                Payment.Status.EXPIRED,
                reason=reason or _('Pagamento marcado como expirado no backoffice.'),
                source='admin_manual_update',
            )
            if payment.order.status == Order.Status.PAYMENT_PENDING:
                from apps.orders.services import transition_order_status

                transition_order_status(payment.order, Order.Status.PENDING)
            return changed

        if target_status == Payment.Status.PENDING:
            changed = transition_payment_status(payment, Payment.Status.PENDING, source='admin_manual_update')
            self._sync_order_for_pending_payment(payment)
            return changed

        if target_status == Payment.Status.REFUNDED:
            return transition_payment_status(payment, Payment.Status.REFUNDED, source='admin_manual_update')

        raise PaymentTransitionError(_('Estado de pagamento inválido.'))

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

    def save_model(self, request, obj, form, change):
        desired_status = form.cleaned_data['status']
        desired_paid_at = form.cleaned_data.get('paid_at')

        if change:
            original_status = getattr(obj, '_original_status', obj.status)
            if desired_status != original_status:
                obj.status = original_status
                if original_status == Payment.Status.PAID and obj.paid_at is None:
                    obj.paid_at = Payment.objects.only('paid_at').get(pk=obj.pk).paid_at
                elif original_status != Payment.Status.PAID:
                    obj.paid_at = None
            super().save_model(request, obj, form, change)
            if desired_status != original_status:
                self._apply_payment_status(obj, desired_status, reason=form.cleaned_data.get('last_error', ''))
                if desired_status == Payment.Status.PAID and desired_paid_at is not None and obj.paid_at != desired_paid_at:
                    obj.paid_at = desired_paid_at
                    obj.save(update_fields=['paid_at'])
            elif desired_status == Payment.Status.PENDING:
                self._sync_order_for_pending_payment(obj)
            return

        if desired_status != Payment.Status.PENDING:
            obj.status = Payment.Status.PENDING
            obj.paid_at = None
        super().save_model(request, obj, form, change)

        if desired_status != Payment.Status.PENDING:
            self._apply_payment_status(obj, desired_status, reason=form.cleaned_data.get('last_error', ''))
            if desired_status == Payment.Status.PAID and desired_paid_at is not None and obj.paid_at != desired_paid_at:
                obj.paid_at = desired_paid_at
                obj.save(update_fields=['paid_at'])
        else:
            self._sync_order_for_pending_payment(obj)

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
        return bool(request.user.is_superuser)

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
                render_action_link(reverse('admin:payments_payment_status', args=[obj.pk, Payment.Status.PAID]), _('Pago'), tone='success'),
                render_action_link(reverse('admin:payments_payment_status', args=[obj.pk, Payment.Status.FAILED]), _('Falhar'), tone='danger'),
                render_action_link(reverse('admin:payments_payment_status', args=[obj.pk, Payment.Status.EXPIRED]), _('Expirar'), tone='warning'),
            ])
        elif obj.status in {Payment.Status.FAILED, Payment.Status.EXPIRED}:
            actions.append(
                render_action_link(
                    reverse('admin:payments_payment_status', args=[obj.pk, Payment.Status.PENDING]),
                    _('Reabrir'),
                    tone='info',
                )
            )
        elif obj.status == Payment.Status.PAID:
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
