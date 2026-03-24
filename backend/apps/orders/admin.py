from django.contrib import admin, messages
from django.db.models import Count
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline

from apps.orders.models import Order, OrderItem
from apps.core.admin_helpers import EditLinkAdminMixin, WorkflowAdminMixin, render_status_badge, render_summary_panel
from apps.orders.services import OrderWorkflowError, cancel_unpaid_order, transition_order_status


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity')
    can_delete = False


@admin.register(Order)
class OrderAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/orders/order/workflow_overview.html'
    list_display = (
        '__str__',
        'customer_display',
        'status_badge',
        'payment_status_badge',
        'payment_method_display',
        'workflow_next_step',
        'items_count_display',
        'fulfillment_method',
        'pickup_location',
        'total',
        'created_since',
        'created_at',
        'edit_link',
    )
    list_filter = ('status', 'payment__status', 'fulfillment_method', 'pickup_location', 'created_at')
    search_fields = ('=pk', 'email', 'name', 'phone')
    search_help_text = 'Pesquise por número de encomenda, email, nome ou telefone.'
    readonly_fields = (
        'status',
        'workflow_summary',
        'customer_snapshot',
        'payment_summary',
        'fulfillment_snapshot',
        'subtotal',
        'total',
        'created_at',
        'updated_at',
    )
    inlines = [OrderItemInline]
    list_filter_submit = True
    compressed_fields = True
    actions = ('mark_preparing', 'mark_ready', 'mark_delivered', 'cancel_unpaid_orders')

    fieldsets = (
        ('Operação', {
            'fields': ('status', 'workflow_summary', 'payment_summary'),
        }),
        ('Cliente', {
            'fields': ('user', 'customer_snapshot', 'name', 'email', 'phone'),
        }),
        ('Encomenda', {
            'fields': ('fulfillment_method', 'pickup_location', 'fulfillment_snapshot', 'language', 'notes'),
        }),
        ('Envio', {
            'fields': ('shipping_address_line1', 'shipping_address_line2', 'shipping_postal_code', 'shipping_city'),
        }),
        ('Valores', {
            'fields': ('subtotal', 'total'),
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    transition_submit_actions = {
        '_mark_preparing': (Order.Status.PREPARING, 'Encomenda marcada como em preparação.'),
        '_mark_ready': (Order.Status.READY, 'Encomenda marcada como pronta para levantamento.'),
        '_mark_delivered': (Order.Status.DELIVERED, 'Encomenda marcada como entregue.'),
    }

    def get_urls(self):
        custom_urls = [
            path(
                '<int:object_id>/cancel-unpaid/',
                self.admin_site.admin_view(self.cancel_unpaid_view),
                name='orders_order_cancel_unpaid',
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:orders_order_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': 'A aguardar pagamento', 'value': queryset.filter(status=Order.Status.PAYMENT_PENDING).count(), 'context': 'Prioridade comercial', 'link': f'{base_url}?status__exact={Order.Status.PAYMENT_PENDING}'},
                {'label': 'Pagas por preparar', 'value': queryset.filter(status=Order.Status.PAID).count(), 'context': 'Próximo passo: preparação', 'link': f'{base_url}?status__exact={Order.Status.PAID}'},
                {'label': 'Em preparação', 'value': queryset.filter(status=Order.Status.PREPARING).count(), 'context': 'Acompanhar equipa', 'link': f'{base_url}?status__exact={Order.Status.PREPARING}'},
                {'label': 'Prontas para entrega', 'value': queryset.filter(status=Order.Status.READY).count(), 'context': 'Operação de saída', 'link': f'{base_url}?status__exact={Order.Status.READY}'},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description='Estado')
    def status_badge(self, obj):
        tones = {
            Order.Status.PENDING: 'neutral',
            Order.Status.PAYMENT_PENDING: 'warning',
            Order.Status.PAID: 'success',
            Order.Status.PREPARING: 'info',
            Order.Status.READY: 'info',
            Order.Status.DELIVERED: 'success',
            Order.Status.CANCELLED: 'danger',
        }
        return render_status_badge(obj.get_status_display(), tones.get(obj.status, 'neutral'))

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment', 'user').annotate(items_count=Count('items', distinct=True))

    def handle_changeform_submit_action(self, request, obj, action_name):
        transition = self.transition_submit_actions.get(action_name)
        if transition is None:
            return None

        target_status, success_message = transition
        try:
            with transaction.atomic():
                locked_order = Order.objects.select_for_update().get(pk=obj.pk)
                changed = transition_order_status(locked_order, target_status)
        except OrderWorkflowError as error:
            self.message_user(request, str(error), level=messages.WARNING)
        else:
            if changed:
                self.message_user(request, success_message, level=messages.SUCCESS)
        return HttpResponseRedirect(request.path)

    def get_changeform_submit_actions(self, request, obj):
        actions = []
        transition_buttons = {
            Order.Status.PREPARING: ('_mark_preparing', 'Marcar em preparação'),
            Order.Status.READY: ('_mark_ready', 'Marcar pronta'),
            Order.Status.DELIVERED: ('_mark_delivered', 'Marcar entregue'),
        }
        for status, (action_name, description) in transition_buttons.items():
            if obj.can_transition_to(status):
                actions.append({'action_name': action_name, 'description': description})
        return actions

    def get_changeform_custom_tools(self, request, obj):
        tools = []
        payment = getattr(obj, 'payment', None)
        if payment is not None:
            tools.append({
                'title': 'Abrir pagamento',
                'link': reverse('admin:payments_payment_change', args=[payment.pk]),
                'icon': 'payments',
                'blank': False,
            })
        if obj.user_id:
            tools.append({
                'title': 'Abrir cliente',
                'link': reverse('admin:accounts_user_change', args=[obj.user_id]),
                'icon': 'person',
                'blank': False,
            })
        if self._can_cancel_from_change_form(obj):
            tools.append({
                'title': 'Cancelar não paga',
                'link': reverse('admin:orders_order_cancel_unpaid', args=[obj.pk]),
                'icon': 'cancel',
                'blank': False,
            })
        return tools

    def cancel_unpaid_view(self, request, object_id):
        order = self.get_object(request, object_id)
        if order is None:
            self.message_user(request, 'Encomenda não encontrada.', level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:orders_order_changelist'))

        try:
            changed = cancel_unpaid_order(order)
        except OrderWorkflowError as error:
            self.message_user(request, str(error), level=messages.WARNING)
        else:
            if changed:
                self.message_user(request, 'Encomenda cancelada e stock reposto.', level=messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:orders_order_change', args=[order.pk]))

    def _can_cancel_from_change_form(self, obj):
        payment = getattr(obj, 'payment', None)
        if payment is not None and payment.status == payment.Status.PAID:
            return False
        return obj.status not in {Order.Status.CANCELLED, Order.Status.PREPARING, Order.Status.READY, Order.Status.DELIVERED}

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.display(ordering='items_count', description='Itens')
    def items_count_display(self, obj):
        return getattr(obj, 'items_count', obj.items.count())

    @admin.display(description='Próxima ação')
    def workflow_next_step(self, obj):
        if obj.status == Order.Status.PAID:
            return 'Iniciar preparação'
        if obj.status == Order.Status.PREPARING:
            return 'Marcar pronta'
        if obj.status == Order.Status.READY:
            return 'Entregar'
        if obj.status == Order.Status.PAYMENT_PENDING:
            return 'Confirmar pagamento'
        if obj.status in {Order.Status.DELIVERED, Order.Status.CANCELLED}:
            return 'Fluxo concluído'
        return 'Validar dados'

    @admin.display(description='Há')
    def created_since(self, obj):
        delta = timezone.now() - obj.created_at
        hours = int(delta.total_seconds() // 3600)
        if hours < 24:
            return f'{max(hours, 0)}h'
        return f'{delta.days}d'

    @admin.display(description='Cliente')
    def customer_display(self, obj):
        contact = obj.masked_contact
        phone = obj.phone[:3] + '***' + obj.phone[-2:] if obj.phone and len(obj.phone) > 5 else obj.phone
        details = ' · '.join(part for part in [contact, phone] if part)
        return format_html('<strong>{}</strong><br><span style="color:#64748b;">{}</span>', obj.name, details or '—')

    @admin.display(ordering='payment__status', description='Pagamento')
    def payment_status_badge(self, obj):
        payment = getattr(obj, 'payment', None)
        if payment is None:
            return '—'

        tones = {
            payment.Status.PENDING: 'warning',
            payment.Status.PAID: 'success',
            payment.Status.FAILED: 'danger',
            payment.Status.EXPIRED: 'neutral',
            payment.Status.REFUNDED: 'info',
        }
        return render_status_badge(payment.get_status_display(), tones.get(payment.status, 'neutral'))

    @admin.display(ordering='payment__method', description='Método pag.')
    def payment_method_display(self, obj):
        payment = getattr(obj, 'payment', None)
        return payment.get_method_display() if payment else '—'

    @admin.display(description='Resumo do pagamento')
    def payment_summary(self, obj):
        payment = getattr(obj, 'payment', None)
        if payment is None:
            return 'Sem pagamento associado.'
        return render_summary_panel(
            'Pagamento',
            [
                ('Estado', payment.get_status_display()),
                ('Método', payment.get_method_display()),
                ('Pedido', payment.masked_request_id or '—'),
                ('Referência', payment.masked_reference or '—'),
                ('Valor', f'{payment.amount:.2f}€'),
            ],
            footer='Os pagamentos confirmados libertam automaticamente as próximas ações do fluxo.',
        )

    @admin.display(description='Resumo operacional')
    def workflow_summary(self, obj):
        next_steps = ', '.join(
            Order.Status(step).label for step in obj.valid_next_statuses()
        ) or 'Sem transições disponíveis'
        return render_summary_panel(
            'Fluxo da encomenda',
            [
                ('Estado atual', obj.get_status_display()),
                ('Próximas transições', next_steps),
                ('Itens', getattr(obj, 'items_count', obj.items.count())),
                ('Atualizada', obj.updated_at.strftime('%d/%m/%Y %H:%M')),
            ],
            footer='Use os botões inferiores para avançar o fluxo quando a operação estiver concluída.',
        )

    @admin.display(description='Ficha do cliente')
    def customer_snapshot(self, obj):
        return render_summary_panel(
            'Cliente',
            [
                ('Nome', obj.name),
                ('Contacto', obj.masked_contact or '—'),
                ('Telefone', obj.phone or '—'),
                ('Conta', 'Associada' if obj.user_id else 'Convidado'),
            ],
        )

    @admin.display(description='Entrega / levantamento')
    def fulfillment_snapshot(self, obj):
        return render_summary_panel(
            'Cumprimento',
            [
                ('Método', obj.get_fulfillment_method_display()),
                ('Levantamento', obj.get_pickup_location_display() if obj.pickup_location else '—'),
                ('Morada', obj.shipping_address_display or '—'),
                ('Idioma', obj.language.upper()),
            ],
        )

    def _process_transition_action(self, request, queryset, target_status):
        success_count = 0
        error_count = 0

        for order in queryset:
            try:
                with transaction.atomic():
                    locked_order = Order.objects.select_for_update().get(pk=order.pk)
                    if transition_order_status(locked_order, target_status):
                        success_count += 1
            except OrderWorkflowError:
                error_count += 1

        if success_count:
            self.message_user(request, f'{success_count} encomenda(s) atualizada(s).', level=messages.SUCCESS)
        if error_count:
            self.message_user(request, f'{error_count} encomenda(s) rejeitada(s) por transição inválida.', level=messages.WARNING)

    @admin.action(description='Marcar como em preparação')
    def mark_preparing(self, request, queryset):
        self._process_transition_action(request, queryset, Order.Status.PREPARING)

    @admin.action(description='Marcar como pronta')
    def mark_ready(self, request, queryset):
        self._process_transition_action(request, queryset, Order.Status.READY)

    @admin.action(description='Marcar como entregue')
    def mark_delivered(self, request, queryset):
        self._process_transition_action(request, queryset, Order.Status.DELIVERED)

    @admin.action(description='Cancelar encomendas não pagas')
    def cancel_unpaid_orders(self, request, queryset):
        success_count = 0
        error_count = 0

        for order in queryset:
            try:
                if cancel_unpaid_order(order):
                    success_count += 1
            except OrderWorkflowError:
                error_count += 1

        if success_count:
            self.message_user(request, f'{success_count} encomenda(s) cancelada(s).', level=messages.SUCCESS)
        if error_count:
            self.message_user(request, f'{error_count} encomenda(s) não puderam ser cancelada(s).', level=messages.WARNING)
