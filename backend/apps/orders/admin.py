from collections import Counter
from decimal import Decimal
from typing import Any, cast

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from apps.catalog.models import Product
from apps.core.admin_helpers import (
    EditLinkAdminMixin,
    WorkflowAdminMixin,
    render_action_group,
    render_action_link,
    render_status_badge,
    render_summary_panel,
)
from apps.orders.models import Order, OrderItem
from apps.orders.services import OrderWorkflowError, cancel_order, transition_order_status
from apps.payments.models import Payment


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ('access_token', 'created_at', 'updated_at', 'payment_state')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].widget.attrs.setdefault('rows', 4)
        self.fields['name'].widget.attrs.setdefault('placeholder', _('Nome do cliente'))
        self.fields['email'].widget.attrs.setdefault('placeholder', _('cliente@exemplo.pt'))
        self.fields['phone'].widget.attrs.setdefault('placeholder', _('912 345 678'))
        self.fields['subtotal'].required = False
        self.fields['total'].required = False
        self.fields['subtotal'].widget.attrs.setdefault('step', '0.01')
        self.fields['total'].widget.attrs.setdefault('step', '0.01')

        if self.instance.pk:
            if self.instance.payment_state == Order.PaymentState.CONFIRMED or self.instance.status in {
                Order.Status.CANCELLED,
                Order.Status.DELIVERED,
            }:
                allowed_statuses = {self.instance.status, *self.instance.valid_next_statuses()}
            else:
                allowed_statuses = {self.instance.status}
        else:
            allowed_statuses = {Order.Status.PENDING}
            self.initial.setdefault('status', Order.Status.PENDING)

        self.fields['status'].choices = [
            choice for choice in Order.Status.choices if choice[0] in allowed_statuses
        ]

    def save(self, commit=True):
        instance = cast(Order, super().save(commit=False))
        if instance.subtotal is None:
            instance.subtotal = Decimal('0.00')
        if instance.total is None:
            instance.total = Decimal('0.00')
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class OrderItemInlineForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_name'].required = False
        self.fields['price'].required = False
        self.fields['product_name'].widget.attrs.setdefault('placeholder', _('Nome apresentado ao cliente'))
        self.fields['price'].widget.attrs.setdefault('step', '0.01')

    def clean(self):
        cleaned_data = cast(dict[str, Any], super().clean() or {})
        if cleaned_data.get('DELETE'):
            return cleaned_data

        product = cleaned_data.get('product')
        product_name = str(cleaned_data.get('product_name') or '').strip()
        price = cleaned_data.get('price')

        if product is not None and not product_name:
            product_name = product.get_name('pt')
            cleaned_data['product_name'] = product_name

        if product is not None and price in (None, ''):
            cleaned_data['price'] = product.price

        if not cleaned_data.get('product_name'):
            self.add_error('product_name', _('Indique o nome do item da encomenda.'))
        if cleaned_data.get('price') in (None, ''):
            self.add_error('price', _('Indique o preço unitário desta linha.'))

        self.instance.product_name = str(cleaned_data.get('product_name') or '').strip()
        self.instance.price = cleaned_data.get('price')
        return cleaned_data


class OrderItemInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        active_forms = [
            form
            for form in self.forms
            if getattr(form, 'cleaned_data', None) and not form.cleaned_data.get('DELETE', False)
        ]
        if not active_forms:
            raise ValidationError(_('Adicione pelo menos um item à encomenda.'))

        current_status = getattr(self.instance, 'status', Order.Status.PENDING)
        if current_status == Order.Status.CANCELLED:
            return

        original_reserved = Counter()
        if self.instance.pk and getattr(self.instance, '_original_status', None) != Order.Status.CANCELLED:
            for item in self.instance.items.all():
                if item.product_id:
                    original_reserved[item.product_id] += item.quantity

        new_reserved = Counter()
        for form in active_forms:
            product = form.cleaned_data.get('product')
            quantity = int(form.cleaned_data.get('quantity') or 0)
            if product is not None and quantity > 0:
                new_reserved[product.pk] += quantity

        products = {
            product.pk: product
            for product in Product.objects.filter(pk__in=new_reserved.keys())
        }
        for product_id, reserved_quantity in new_reserved.items():
            extra_needed = reserved_quantity - original_reserved.get(product_id, 0)
            if extra_needed <= 0:
                continue

            product = products.get(product_id)
            if product is None:
                continue
            if product.stock < extra_needed:
                raise ValidationError(
                    _('Sem stock suficiente para %(product)s.')
                    % {'product': product.get_name('pt')}
                )


class OrderItemInline(TabularInline):
    model = OrderItem
    form = OrderItemInlineForm
    formset = OrderItemInlineFormSet
    extra = 1
    autocomplete_fields = ('product',)
    fields = ('product', 'product_name', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    form = OrderAdminForm
    list_display = (
        '__str__',
        'status_badge',
        'fulfillment_method',
        'pickup_location',
        'total',
        'created_at',
        'edit_link',
    )
    list_filter = ('status', 'payment__status', 'fulfillment_method', 'pickup_location', 'created_at')
    search_fields = ('=pk', 'email', 'name', 'phone')
    search_help_text = _('Pesquise por número de encomenda, email, nome ou telefone.')
    readonly_fields = ('payment_state_display',)
    inlines = [OrderItemInline]
    list_filter_submit = True
    compressed_fields = True
    autocomplete_fields = ('user',)
    actions = ('mark_preparing', 'mark_ready', 'mark_in_transit', 'mark_delivered', 'cancel_orders')

    add_fieldsets = (
        (None, {
            'fields': (
                'user',
                'name',
                'email',
                'phone',
                'status',
                'fulfillment_method',
                'pickup_location',
                'shipping_address_line1',
                'shipping_address_line2',
                'shipping_postal_code',
                'shipping_city',
                'language',
                'notes',
                'subtotal',
                'total',
            ),
        }),
    )

    pickup_fieldsets = (
        (None, {
            'fields': (
                'user',
                'name',
                'email',
                'phone',
                'status',
                'payment_state_display',
                'fulfillment_method',
                'pickup_location',
                'language',
                'notes',
                'subtotal',
                'total',
            ),
        }),
    )

    shipping_fieldsets = (
        (None, {
            'fields': (
                'user',
                'name',
                'email',
                'phone',
                'status',
                'payment_state_display',
                'fulfillment_method',
                'shipping_address_line1',
                'shipping_address_line2',
                'shipping_postal_code',
                'shipping_city',
                'language',
                'notes',
                'subtotal',
                'total',
            ),
        }),
    )

    transition_submit_actions = {
        '_mark_preparing': (Order.Status.PREPARING, _('Encomenda marcada como em preparação.')),
        '_mark_ready': (Order.Status.READY, _('Encomenda marcada como pronta para levantamento.')),
        '_mark_in_transit': (Order.Status.IN_TRANSIT, _('Encomenda marcada como em trânsito.')),
        '_mark_delivered': (Order.Status.DELIVERED, _('Encomenda marcada como entregue.')),
    }

    def get_urls(self):
        custom_urls = [
            path(
                '<int:object_id>/transition/<slug:target_status>/',
                self.admin_site.admin_view(self.transition_view),
                name='orders_order_transition',
            ),
            path(
                '<int:object_id>/cancel-unpaid/',
                self.admin_site.admin_view(self.cancel_unpaid_view),
                name='orders_order_cancel_unpaid',
            ),
        ]
        return custom_urls + super().get_urls()

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        if obj.fulfillment_method == Order.FulfillmentMethod.SHIPPING:
            return self.shipping_fieldsets
        return self.pickup_fieldsets

    def get_readonly_fields(self, request, obj=None):
        return ('payment_state_display',)

    @admin.display(description=_('Estado do pagamento'))
    def payment_state_display(self, obj):
        payment = getattr(obj, 'payment', None)
        if payment is None:
            return _('Sem pagamento associado.')
        tones = {
            Order.PaymentState.PENDING: 'warning',
            Order.PaymentState.CONFIRMED: 'success',
            Order.PaymentState.CANCELLED: 'danger',
            Order.PaymentState.REFUNDED: 'info',
        }
        badge = render_status_badge(payment.status_label, tones.get(obj.payment_state, 'neutral'))
        link = format_html(
            '<a href="{}" style="margin-left:8px;font-size:13px;">{}</a>',
            reverse('admin:payments_payment_change', args=[payment.pk]),
            _('Atualizar pagamento'),
        )
        return format_html('{}{}', badge, link)

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description='Estado')
    def status_badge(self, obj):
        tones = {
            Order.Status.PENDING: 'neutral',
            Order.Status.PREPARING: 'info',
            Order.Status.READY: 'info',
            Order.Status.IN_TRANSIT: 'info',
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

    def save_model(self, request, obj, form, change):
        if change:
            obj._admin_original_status = getattr(obj, '_original_status', obj.status)
            obj._admin_original_items_snapshot = list(
                OrderItem.objects.filter(order=obj).values('product_id', 'quantity')
            )
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        self._sync_order_totals_and_stock(cast(Order, form.instance))

    def get_changeform_submit_actions(self, request, obj):
        if obj is None:
            return []
        if obj.status == Order.Status.PENDING and obj.payment_state != Order.PaymentState.CONFIRMED:
            return []

        actions = []
        transition_buttons = {
            Order.Status.PREPARING: ('_mark_preparing', _('Marcar em preparação')),
            Order.Status.READY: ('_mark_ready', _('Marcar pronta')),
            Order.Status.IN_TRANSIT: ('_mark_in_transit', _('Marcar em trânsito')),
            Order.Status.DELIVERED: ('_mark_delivered', _('Marcar entregue')),
        }
        for status, (action_name, description) in transition_buttons.items():
            if obj.can_transition_to(status):
                actions.append({'action_name': action_name, 'description': description})
        return actions

    def get_changeform_custom_tools(self, request, obj):
        return []

    def cancel_unpaid_view(self, request, object_id):
        order = self.get_object(request, object_id)
        if order is None:
            self.message_user(request, _('Encomenda não encontrada.'), level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:orders_order_changelist'))

        try:
            changed = cancel_order(order)
        except OrderWorkflowError as error:
            self.message_user(request, str(error), level=messages.WARNING)
        else:
            if changed:
                self.message_user(request, _('Encomenda cancelada.'), level=messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:orders_order_change', args=[order.pk]))

    def _can_cancel_from_change_form(self, obj):
        return obj.status not in {Order.Status.CANCELLED, Order.Status.DELIVERED}

    def _sync_order_totals_and_stock(self, order):
        original_items = getattr(order, '_admin_original_items_snapshot', [])
        original_status = getattr(order, '_admin_original_status', None)
        current_items = list(order.items.select_related('product'))

        original_reserved = Counter()
        if original_status != Order.Status.CANCELLED:
            for item in original_items:
                if item['product_id']:
                    original_reserved[item['product_id']] += item['quantity']

        current_reserved = Counter()
        if order.status != Order.Status.CANCELLED:
            for item in current_items:
                if item.product_id:
                    current_reserved[item.product_id] += item.quantity

        locked_products = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(
                pk__in=set(original_reserved.keys()) | set(current_reserved.keys())
            )
        }
        for product_id in set(original_reserved.keys()) | set(current_reserved.keys()):
            delta = current_reserved.get(product_id, 0) - original_reserved.get(product_id, 0)
            if delta == 0:
                continue

            product = locked_products.get(product_id)
            if product is None:
                continue
            product.stock -= delta
            product.save(update_fields=['stock', 'updated_at'])

        subtotal = sum((item.price * item.quantity for item in current_items), Decimal('0.00'))
        if order.subtotal != subtotal or order.total != subtotal:
            order.subtotal = subtotal
            order.total = subtotal
            order.save(update_fields=['subtotal', 'total', 'updated_at'])

        payment = Payment.objects.filter(order=order).first()
        if payment is not None and payment.status != Payment.Status.CONFIRMED and payment.amount != order.total:
            payment.amount = order.total
            payment.save(update_fields=['amount'])

    def transition_view(self, request, object_id, target_status):
        order = self.get_object(request, object_id)
        if order is None:
            self.message_user(request, _('Encomenda não encontrada.'), level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:orders_order_changelist'))

        try:
            status_label = Order.Status(target_status).label
        except ValueError:
            self.message_user(request, _('Estado de encomenda inválido.'), level=messages.ERROR)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('admin:orders_order_changelist'))

        try:
            with transaction.atomic():
                locked_order = Order.objects.select_for_update().select_related('payment').get(pk=order.pk)
                changed = transition_order_status(locked_order, target_status)
        except OrderWorkflowError as error:
            self.message_user(request, str(error), level=messages.WARNING)
        else:
            if changed:
                self.message_user(
                    request,
                    _('Encomenda atualizada para %(status)s.') % {'status': status_label},
                    level=messages.SUCCESS,
                )
        return HttpResponseRedirect(request.META.get('HTTP_REFERER') or reverse('admin:orders_order_changelist'))

    def has_delete_permission(self, request, obj=None):
        return bool(cast(Any, request.user).is_superuser)

    @admin.display(ordering='items_count', description=_('Itens'))
    def items_count_display(self, obj):
        return getattr(obj, 'items_count', obj.items.count())

    @admin.display(description=_('Ações rápidas'))
    def quick_actions(self, obj):
        actions = []
        transition_labels = {
            Order.Status.PREPARING: _('Preparar'),
            Order.Status.READY: _('Pronta'),
            Order.Status.IN_TRANSIT: _('Em transporte'),
            Order.Status.DELIVERED: _('Entregue'),
        }

        next_statuses = []
        if obj.status == Order.Status.PENDING:
            if obj.payment_state == Order.PaymentState.CONFIRMED:
                next_statuses = [Order.Status.PREPARING]
        elif obj.status == Order.Status.PREPARING:
            next_statuses = [Order.Status.IN_TRANSIT] if obj.is_shipping else [Order.Status.READY]
        elif obj.status == Order.Status.READY:
            next_statuses = [Order.Status.DELIVERED]
        elif obj.status == Order.Status.IN_TRANSIT:
            next_statuses = [Order.Status.DELIVERED]

        for target_status in next_statuses:
            actions.append(
                render_action_link(
                    reverse('admin:orders_order_transition', args=[obj.pk, target_status]),
                    transition_labels[target_status],
                    tone='info' if target_status != Order.Status.DELIVERED else 'success',
                )
            )

        if self._can_cancel_from_change_form(obj):
            actions.append(
                render_action_link(
                    reverse('admin:orders_order_cancel_unpaid', args=[obj.pk]),
                    _('Cancelar'),
                    tone='danger',
                )
            )

        return render_action_group(actions)

    @admin.display(description=_('Próxima ação'))
    def workflow_next_step(self, obj):
        if obj.payment_state == Order.PaymentState.PENDING and obj.status == Order.Status.PENDING:
            return _('Confirmar pagamento')
        if obj.status == Order.Status.PENDING and obj.payment_state == Order.PaymentState.CONFIRMED:
            return _('Iniciar preparação')
        if obj.status == Order.Status.PREPARING:
            return _('Marcar em trânsito') if obj.is_shipping else _('Marcar pronta')
        if obj.status == Order.Status.READY:
            return _('Entregar')
        if obj.status in {Order.Status.DELIVERED, Order.Status.CANCELLED}:
            return _('Fluxo concluído')
        return _('Validar dados')

    @admin.display(description=_('Há'))
    def created_since(self, obj):
        delta = timezone.now() - obj.created_at
        hours = int(delta.total_seconds() // 3600)
        if hours < 24:
            return f'{max(hours, 0)}h'
        return f'{delta.days}d'

    @admin.display(description=_('Cliente'))
    def customer_display(self, obj):
        contact = obj.masked_contact
        phone = obj.phone[:3] + '***' + obj.phone[-2:] if obj.phone and len(obj.phone) > 5 else obj.phone
        details = ' · '.join(part for part in [contact, phone] if part)
        return format_html('<strong>{}</strong><br><span style="color:#64748b;">{}</span>', obj.name, details or '—')

    @admin.display(ordering='payment__status', description=_('Pagamento'))
    def payment_status_badge(self, obj):
        payment = getattr(obj, 'payment', None)
        if payment is None:
            return '—'

        tones = {
            payment.Status.PENDING: 'warning',
            payment.Status.CONFIRMED: 'success',
            payment.Status.CANCELLED: 'danger',
            payment.Status.REFUNDED: 'info',
        }
        return render_status_badge(payment.get_status_display(), tones.get(payment.status, 'neutral'))

    @admin.display(ordering='payment__method', description=_('Método pag.'))
    def payment_method_display(self, obj):
        payment = getattr(obj, 'payment', None)
        return payment.get_method_display() if payment else '—'

    @admin.display(description=_('Resumo do pagamento'))
    def payment_summary(self, obj):
        payment = getattr(obj, 'payment', None)
        if payment is None:
            return _('Sem pagamento associado.')
        return render_summary_panel(
            _('Pagamento'),
            [
                (_('Estado'), payment.status_label),
                (_('Método'), payment.method_label),
                (_('Referência'), payment.masked_provider_reference or '—'),
                (_('ID no provedor'), payment.masked_provider_payment_id or '—'),
                (_('Valor'), f'{payment.amount:.2f}€'),
            ],
            footer=_('Atualize o pagamento no editor próprio; o estado da encomenda avança separadamente.'),
        )

    @admin.display(description=_('Resumo operacional'))
    def workflow_summary(self, obj):
        next_step_labels = [str(Order.Status(step).label) for step in obj.valid_next_statuses()]
        next_steps = ', '.join(next_step_labels) or str(_('Sem transições disponíveis'))
        return render_summary_panel(
            _('Fluxo da encomenda'),
            [
                (_('Estado atual'), obj.get_status_display()),
                (_('Próximas transições'), next_steps),
                (_('Itens'), getattr(obj, 'items_count', obj.items.count())),
                (_('Atualizada'), obj.updated_at.strftime('%d/%m/%Y %H:%M')),
            ],
            footer=_('Use os botões inferiores para avançar o fluxo quando a operação estiver concluída.'),
        )

    @admin.display(description=_('Ficha do cliente'))
    def customer_snapshot(self, obj):
        return render_summary_panel(
            _('Cliente'),
            [
                (_('Nome'), obj.name),
                (_('Contacto'), obj.masked_contact or '—'),
                (_('Telefone'), obj.phone or '—'),
                (_('Conta'), _('Associada') if obj.user_id else _('Convidado')),
            ],
        )

    @admin.display(description=_('Entrega / levantamento'))
    def fulfillment_snapshot(self, obj):
        return render_summary_panel(
            _('Cumprimento'),
            [
                (_('Método'), obj.get_fulfillment_method_display()),
                (_('Levantamento'), obj.get_pickup_location_display() if obj.pickup_location else '—'),
                (_('Morada'), obj.shipping_address_display or '—'),
                (_('Idioma'), obj.get_language_display()),
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
            self.message_user(request, _('{} encomenda(s) atualizada(s).').format(success_count), level=messages.SUCCESS)
        if error_count:
            self.message_user(request, _('{} encomenda(s) rejeitada(s) por transição inválida.').format(error_count), level=messages.WARNING)

    @admin.action(description=_('Marcar como em preparação'))
    def mark_preparing(self, request, queryset):
        self._process_transition_action(request, queryset, Order.Status.PREPARING)

    @admin.action(description=_('Marcar como pronta'))
    def mark_ready(self, request, queryset):
        self._process_transition_action(request, queryset, Order.Status.READY)

    @admin.action(description=_('Marcar como em trânsito'))
    def mark_in_transit(self, request, queryset):
        self._process_transition_action(request, queryset, Order.Status.IN_TRANSIT)

    @admin.action(description=_('Marcar como entregue'))
    def mark_delivered(self, request, queryset):
        self._process_transition_action(request, queryset, Order.Status.DELIVERED)

    @admin.action(description=_('Cancelar encomendas'))
    def cancel_orders(self, request, queryset):
        success_count = 0
        error_count = 0

        for order in queryset:
            try:
                if cancel_order(order):
                    success_count += 1
            except OrderWorkflowError:
                error_count += 1

        if success_count:
            self.message_user(request, _('{} encomenda(s) cancelada(s).').format(success_count), level=messages.SUCCESS)
        if error_count:
            self.message_user(request, _('{} encomenda(s) não puderam ser cancelada(s).').format(error_count), level=messages.WARNING)
