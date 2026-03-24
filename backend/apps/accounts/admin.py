from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Max, Q, Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin, TabularInline

from apps.accounts.models import User, Address
from apps.core.admin_helpers import EditLinkAdminMixin, WorkflowAdminMixin, render_status_badge, render_summary_panel


class AddressInline(TabularInline):
    model = Address
    extra = 0
    fields = ('name', 'line1', 'city', 'postal_code', 'is_default')
    show_change_link = True


@admin.register(User)
class UserAdmin(WorkflowAdminMixin, EditLinkAdminMixin, BaseUserAdmin):
    list_before_template = 'admin/accounts/user/workflow_overview.html'

    list_display = (
        'email',
        'full_name_display',
        'profile_status_badge',
        'order_count_display',
        'default_address_badge',
        'preferred_language',
        'is_active',
        'is_staff',
        'edit_link',
    )
    list_filter = ('is_staff', 'is_active', 'preferred_language')
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'nif')
    search_help_text = 'Pesquise por email, nome, telefone ou NIF do cliente.'
    ordering = ('email',)
    list_filter_submit = True
    compressed_fields = True
    inlines = [AddressInline]
    readonly_fields = ('customer_snapshot_panel', 'customer_service_panel', 'last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Resumo de cliente', {'fields': ('customer_snapshot_panel', 'customer_service_panel')}),
        ('Informação Pessoal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
        ('Informação Adicional', {
            'fields': ('phone', 'nif', 'preferred_language'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Informação Adicional', {
            'fields': ('email', 'phone', 'preferred_language'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            order_count=Count('orders', distinct=True),
            address_count=Count('addresses', distinct=True),
            default_address_count=Count('addresses', filter=Q(addresses__is_default=True), distinct=True),
            last_order_at=Max('orders__created_at'),
            lifetime_revenue=Coalesce(
                Sum('orders__total', distinct=True),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:accounts_user_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': 'Clientes ativos', 'value': queryset.filter(is_active=True).count(), 'context': 'Com acesso ativo', 'link': f'{base_url}?is_active__exact=1'},
                {'label': 'Com encomendas', 'value': queryset.filter(order_count__gt=0).count(), 'context': 'Já compraram', 'link': base_url},
                {'label': 'Sem telefone', 'value': queryset.filter(phone='').count(), 'context': 'Suporte com contacto incompleto', 'link': base_url},
                {'label': 'Sem morada predefinida', 'value': queryset.filter(default_address_count=0).count(), 'context': 'Fricção no checkout', 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_changeform_submit_actions(self, request, obj):
        if obj.is_active:
            return [{'action_name': '_deactivate_customer', 'description': 'Desativar acesso'}]
        return [{'action_name': '_reactivate_customer', 'description': 'Reativar acesso'}]

    def handle_changeform_submit_action(self, request, obj, action_name):
        if action_name == '_deactivate_customer' and obj.is_active:
            obj.is_active = False
            obj.save(update_fields=['is_active'])
            self.message_user(request, 'Cliente desativado.', level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        if action_name == '_reactivate_customer' and not obj.is_active:
            obj.is_active = True
            obj.save(update_fields=['is_active'])
            self.message_user(request, 'Cliente reativado.', level=messages.SUCCESS)
            return HttpResponseRedirect(request.path)

        return None

    def get_changeform_custom_tools(self, request, obj):
        tools = [
            {
                'title': 'Ver encomendas',
                'link': reverse('admin:orders_order_changelist') + f'?q={obj.email}',
                'icon': 'shopping_bag',
                'blank': False,
            },
            {
                'title': 'Adicionar morada',
                'link': reverse('admin:accounts_address_add') + f'?user={obj.pk}',
                'icon': 'location_on',
                'blank': False,
            },
        ]
        default_address = obj.addresses.filter(is_default=True).first()
        if default_address is not None:
            tools.append({
                'title': 'Abrir morada predefinida',
                'link': reverse('admin:accounts_address_change', args=[default_address.pk]),
                'icon': 'home_pin',
                'blank': False,
            })
        return tools

    @admin.display(description='Cliente')
    def full_name_display(self, obj):
        full_name = ' '.join(part for part in [obj.first_name, obj.last_name] if part).strip()
        if not full_name:
            full_name = 'Sem nome definido'
        return full_name

    @admin.display(ordering='order_count', description='Encomendas')
    def order_count_display(self, obj):
        return getattr(obj, 'order_count', obj.orders.count())

    @admin.display(description='Perfil')
    def profile_status_badge(self, obj):
        if not obj.is_active:
            return render_status_badge('Suspenso', 'danger')

        blockers = []
        if not obj.phone:
            blockers.append('telefone')
        if not obj.nif:
            blockers.append('NIF')
        if getattr(obj, 'default_address_count', obj.addresses.filter(is_default=True).count()) == 0:
            blockers.append('morada')

        if blockers:
            return render_status_badge('Dados em falta', 'warning')
        if getattr(obj, 'order_count', obj.orders.count()) == 0:
            return render_status_badge('Novo cliente', 'info')
        return render_status_badge('Acompanhado', 'success')

    @admin.display(description='Morada')
    def default_address_badge(self, obj):
        if getattr(obj, 'default_address_count', obj.addresses.filter(is_default=True).count()):
            return render_status_badge('Predefinida', 'success')
        return render_status_badge('Por definir', 'warning')

    @admin.display(description='NIF')
    def masked_nif(self, obj):
        if not obj.nif:
            return '—'
        if len(obj.nif) <= 3:
            return '*' * len(obj.nif)
        return f'{obj.nif[:3]}***{obj.nif[-1:]}'

    @admin.display(description='Resumo do cliente')
    def customer_snapshot_panel(self, obj):
        if obj is None:
            return 'Guarde o cliente para ver o resumo operacional.'

        default_address = obj.addresses.filter(is_default=True).first()
        order_count = getattr(obj, 'order_count', obj.orders.count())
        lifetime_revenue = getattr(
            obj,
            'lifetime_revenue',
            obj.orders.aggregate(
                total=Coalesce(
                    Sum('total'),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )['total'],
        )
        footer = 'Complete telefone, NIF e uma morada predefinida para acelerar apoio ao cliente.'
        if obj.is_active and obj.phone and obj.nif and default_address is not None:
            footer = 'Perfil operacionalmente completo para suporte e encomendas.'

        return render_summary_panel(
            'Resumo do cliente',
            [
                ('Estado', 'Ativo' if obj.is_active else 'Suspenso'),
                ('Nome', self.full_name_display(obj)),
                ('Contacto', obj.phone or 'Sem telefone'),
                ('NIF', self.masked_nif(obj)),
                ('Idioma preferido', obj.get_preferred_language_display()),
                ('Encomendas', order_count),
                ('Receita acumulada', f'{lifetime_revenue} €'),
                ('Última encomenda', getattr(obj, 'last_order_at', None) or 'Sem encomendas'),
                ('Morada predefinida', default_address or 'Sem morada predefinida'),
            ],
            footer=footer,
        )

    @admin.display(description='Serviço e acesso')
    def customer_service_panel(self, obj):
        if obj is None:
            return 'Guarde o cliente para ver o estado de serviço.'

        address_count = getattr(obj, 'address_count', obj.addresses.count())
        return render_summary_panel(
            'Serviço e acesso',
            [
                ('Acesso ao site', 'Ativo' if obj.is_active else 'Desativado'),
                ('Permissão de staff', 'Sim' if obj.is_staff else 'Não'),
                ('Moradas guardadas', address_count),
                ('Último login', obj.last_login or 'Ainda não autenticou'),
                ('Criado em', obj.date_joined),
            ],
            footer='Use os atalhos acima para abrir encomendas ou tratar a morada do cliente sem sair deste contexto.',
        )


@admin.register(Address)
class AddressAdmin(WorkflowAdminMixin, EditLinkAdminMixin, ModelAdmin):
    list_before_template = 'admin/accounts/address/workflow_overview.html'

    list_display = ('name', 'user', 'city', 'postal_code', 'address_status_badge', 'is_default', 'user_order_count_display', 'edit_link')
    list_filter = ('city', 'is_default')
    search_fields = ('name', 'line1', 'city', 'postal_code', 'user__email')
    search_help_text = 'Pesquise por cliente, nome da morada, cidade ou código postal.'
    list_filter_submit = True
    compressed_fields = True
    readonly_fields = ('address_summary_panel',)
    fieldsets = (
        ('Resumo', {'fields': ('address_summary_panel',)}),
        ('Morada', {'fields': ('user', 'name', 'line1', 'line2', 'city', 'postal_code', 'country', 'is_default')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').annotate(
            user_order_count=Count('user__orders', distinct=True),
        )

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)
        base_url = reverse('admin:accounts_address_changelist')
        extra_context = {
            **(extra_context or {}),
            'workflow_metric_cards': [
                {'label': 'Moradas totais', 'value': queryset.count(), 'context': 'Livro de moradas', 'link': base_url},
                {'label': 'Predefinidas', 'value': queryset.filter(is_default=True).count(), 'context': 'Preferidas no checkout', 'link': f'{base_url}?is_default__exact=1'},
                {'label': 'Secundárias', 'value': queryset.filter(is_default=False).count(), 'context': 'Alternativas guardadas', 'link': f'{base_url}?is_default__exact=0'},
                {'label': 'Clientes sem default', 'value': User.objects.annotate(default_address_count=Count('addresses', filter=Q(addresses__is_default=True), distinct=True)).filter(addresses__isnull=False, default_address_count=0).distinct().count(), 'context': 'Rever para checkout rápido', 'link': base_url},
            ],
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_changeform_custom_tools(self, request, obj):
        return [
            {
                'title': 'Abrir cliente',
                'link': reverse('admin:accounts_user_change', args=[obj.user_id]),
                'icon': 'person',
                'blank': False,
            },
            {
                'title': 'Histórico de encomendas',
                'link': reverse('admin:orders_order_changelist') + f'?q={obj.user.email}',
                'icon': 'shopping_bag',
                'blank': False,
            },
        ]

    @admin.display(description='Estado')
    def address_status_badge(self, obj):
        if obj.is_default:
            return render_status_badge('Predefinida', 'success')
        return render_status_badge('Secundária', 'info')

    @admin.display(ordering='user_order_count', description='Encomendas cliente')
    def user_order_count_display(self, obj):
        return getattr(obj, 'user_order_count', obj.user.orders.count())

    @admin.display(description='Resumo da morada')
    def address_summary_panel(self, obj):
        if obj is None:
            return 'Guarde a morada para ver o resumo operacional.'

        return render_summary_panel(
            'Resumo da morada',
            [
                ('Cliente', obj.user),
                ('Tipo', 'Predefinida' if obj.is_default else 'Secundária'),
                ('Linha 1', obj.line1),
                ('Linha 2', obj.line2 or '—'),
                ('Cidade', obj.city),
                ('Código postal', obj.postal_code),
                ('País', obj.country),
                ('Encomendas do cliente', getattr(obj, 'user_order_count', obj.user.orders.count())),
            ],
            footer='Abra o cliente para ajustar preferências ou usar o histórico de encomendas como contexto de suporte.',
        )
