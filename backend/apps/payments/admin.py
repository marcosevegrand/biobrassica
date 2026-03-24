import json

from django.contrib import admin
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from apps.payments.models import Payment, PaymentCallback
from apps.core.admin_helpers import EditLinkAdminMixin, WorkflowAdminMixin, render_status_badge, render_summary_panel


class PaymentCallbackInline(TabularInline):
    model = PaymentCallback
    extra = 0
    can_delete = False
    max_num = 5
    readonly_fields = ('created_at', 'validation_badge', 'validation_message', 'anonymized_ip_display', 'sanitized_payload_display')
    fields = ('created_at', 'validation_badge', 'validation_message', 'anonymized_ip_display', 'sanitized_payload_display')
    show_change_link = True

    @admin.display(description='Validação')
    def validation_badge(self, obj):
        tone = 'success' if obj.is_valid else 'danger'
        label = 'Válido' if obj.is_valid else 'Inválido'
        return render_status_badge(label, tone)

    @admin.display(description='IP')
    def anonymized_ip_display(self, obj):
        return obj.ip_address

    @admin.display(description='Payload')
    def sanitized_payload_display(self, obj):
        return format_html('<pre style="white-space:pre-wrap;max-width:48rem;">{}</pre>', json.dumps(obj.raw_payload, ensure_ascii=False, indent=2))


@admin.register(Payment)
class PaymentAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/payments/payment/workflow_overview.html'
    list_display = ('__str__', 'order', 'customer_display', 'method', 'status_badge', 'callback_health_display', 'masked_reference_display', 'amount', 'expires_at', 'paid_at', 'created_at', 'edit_link')
    list_filter = ('method', 'status', 'created_at')
    search_fields = ('=order__pk', 'mb_reference', 'ifthenpay_request_id', 'mbway_transaction_id')
    search_help_text = 'Pesquise por encomenda, referência, request id ou transação MB WAY.'
    readonly_fields = (
        'order', 'customer_display', 'status_badge', 'order_summary', 'callback_health_summary', 'method', 'amount', 'ifthenpay_request_id_display',
        'mb_entity', 'mb_reference_display', 'mbway_phone_display', 'mbway_transaction_id',
        'checkout_url', 'last_error', 'expires_at', 'paid_at', 'created_at',
    )
    list_filter_submit = True
    compressed_fields = True
    inlines = [PaymentCallbackInline]
    fieldsets = (
        ('Operação', {
            'fields': ('order', 'customer_display', 'status_badge', 'order_summary', 'callback_health_summary'),
        }),
        ('Dados do pagamento', {
            'fields': ('method', 'amount', 'ifthenpay_request_id_display', 'mb_entity', 'mb_reference_display', 'mbway_phone_display', 'mbway_transaction_id', 'checkout_url'),
        }),
        ('Auditoria', {
            'fields': ('expires_at', 'paid_at', 'created_at', 'last_error'),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:payments_payment_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': 'Pendentes', 'value': queryset.filter(status=Payment.Status.PENDING).count(), 'context': 'Acompanhar cobranças', 'link': f'{base_url}?status__exact={Payment.Status.PENDING}'},
                {'label': 'Expirados', 'value': queryset.filter(status=Payment.Status.EXPIRED).count(), 'context': 'Verificar recuperação', 'link': f'{base_url}?status__exact={Payment.Status.EXPIRED}'},
                {'label': 'Falhados', 'value': queryset.filter(status=Payment.Status.FAILED).count(), 'context': 'Rever erros', 'link': f'{base_url}?status__exact={Payment.Status.FAILED}'},
                {'label': 'Callbacks inválidos', 'value': queryset.filter(invalid_callback_count__gt=0).count(), 'context': 'Requer investigação', 'link': reverse('admin:payments_paymentcallback_changelist') + '?is_valid__exact=0'},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description='Estado')
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
                'title': 'Abrir encomenda',
                'link': reverse('admin:orders_order_change', args=[obj.order_id]),
                'icon': 'shopping_bag',
                'blank': False,
            },
            {
                'title': 'Ver callbacks',
                'link': reverse('admin:payments_paymentcallback_changelist') + f'?payment__id__exact={obj.pk}',
                'icon': 'receipt_long',
                'blank': False,
            },
        ]
        if obj.checkout_url:
            tools.append({
                'title': 'Abrir checkout',
                'link': obj.checkout_url,
                'icon': 'open_in_new',
                'blank': True,
            })
        return tools

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Cliente')
    def customer_display(self, obj):
        return format_html('<strong>{}</strong><br><span style="color:#64748b;">{}</span>', obj.order.name, obj.order.masked_contact)

    @admin.display(description='Pedido')
    def ifthenpay_request_id_display(self, obj):
        return obj.masked_request_id or '—'

    @admin.display(description='Referência')
    def mb_reference_display(self, obj):
        return obj.masked_reference or '—'

    @admin.display(description='Telefone MB WAY')
    def mbway_phone_display(self, obj):
        return obj.masked_mbway_phone or '—'

    @admin.display(ordering='mb_reference', description='Ref.')
    def masked_reference_display(self, obj):
        return obj.masked_reference or obj.masked_request_id or '—'

    @admin.display(ordering='invalid_callback_count', description='Callbacks')
    def callback_health_display(self, obj):
        invalid_count = getattr(obj, 'invalid_callback_count', 0)
        if invalid_count:
            return render_status_badge(f'{invalid_count} inválido(s)', 'danger')
        count = getattr(obj, 'callback_count', 0)
        if count:
            return render_status_badge(f'{count} recebido(s)', 'info')
        return render_status_badge('Sem callbacks', 'neutral')

    @admin.display(description='Resumo da encomenda')
    def order_summary(self, obj):
        order = obj.order
        return render_summary_panel(
            'Encomenda associada',
            [
                ('Encomenda', f'#{order.pk}'),
                ('Cliente', order.name),
                ('Estado', order.get_status_display()),
                ('Entrega', order.get_fulfillment_method_display()),
                ('Total', f'{order.total:.2f}€'),
            ],
        )

    @admin.display(description='Saúde de callback')
    def callback_health_summary(self, obj):
        invalid_count = getattr(obj, 'invalid_callback_count', obj.callbacks.filter(is_valid=False).count())
        total_count = getattr(obj, 'callback_count', obj.callbacks.count())
        latest_callback = obj.callbacks.order_by('-created_at').first()
        return render_summary_panel(
            'Callbacks do provedor',
            [
                ('Recebidos', total_count),
                ('Inválidos', invalid_count),
                ('Último callback', latest_callback.created_at.strftime('%d/%m/%Y %H:%M') if latest_callback else '—'),
                ('Último motivo', latest_callback.validation_message or '—' if latest_callback else '—'),
            ],
            footer='Use o atalho superior para abrir a lista filtrada de callbacks desta cobrança.',
        )


@admin.register(PaymentCallback)
class PaymentCallbackAdmin(EditLinkAdminMixin, ModelAdmin):
    list_display = ('pk', 'payment', 'validation_badge', 'validation_message', 'anonymized_ip_display', 'created_at', 'edit_link')
    list_filter = ('is_valid', 'created_at')
    readonly_fields = ('payment', 'sanitized_payload_display', 'anonymized_ip_display', 'is_valid', 'validation_message', 'created_at')
    search_fields = ('=payment__order__pk', 'payment__ifthenpay_request_id', 'payment__mb_reference', 'validation_message')
    list_filter_submit = True
    compressed_fields = True

    @admin.display(description='Validação')
    def validation_badge(self, obj):
        tone = 'success' if obj.is_valid else 'danger'
        label = 'Válido' if obj.is_valid else 'Inválido'
        return render_status_badge(label, tone)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment', 'payment__order')

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='IP')
    def anonymized_ip_display(self, obj):
        return obj.ip_address

    @admin.display(description='Payload sanitizado')
    def sanitized_payload_display(self, obj):
        return format_html('<pre style="white-space:pre-wrap;max-width:48rem;">{}</pre>', json.dumps(obj.raw_payload, ensure_ascii=False, indent=2))
