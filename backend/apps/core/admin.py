"""Core admin configuration."""

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.core.models import ShopSettings


@admin.register(ShopSettings)
class ShopSettingsAdmin(ModelAdmin):
    fieldsets = (
        (_('Loja'), {
            'fields': ('is_shop_active', 'min_order_total'),
            'description': _(
                'Desative a loja para impedir o avanço do checkout. A configuração é '
                'persistida em base de dados e mantém-se entre deployments.'
            ),
        }),
        (_('MB WAY'), {
            'fields': ('mbway_enabled', 'mbway_number'),
        }),
        (_('Transferência bancária'), {
            'fields': ('bank_transfer_enabled', 'bank_beneficiary', 'bank_iban', 'bank_bic'),
        }),
        (_('Locais de levantamento e métodos de entrega'), {
            'fields': ('locations_link', 'delivery_methods_link'),
            'description': _(
                'Configure os locais de levantamento (com horário) e os métodos de entrega '
                'disponíveis na loja.'
            ),
        }),
        (_('Auditoria'), {
            'fields': ('updated_at',),
        }),
    )
    readonly_fields = ('updated_at', 'locations_link', 'delivery_methods_link')

    def has_add_permission(self, request):
        return not ShopSettings.objects.filter(pk=1).exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):  # type: ignore[override]
        ShopSettings.load()
        return HttpResponseRedirect(reverse('admin:core_shopsettings_change', args=[1]))

    @admin.display(description=_('Locais de levantamento'))
    def locations_link(self, obj):
        url = reverse('admin:catalog_location_changelist')
        add_url = reverse('admin:catalog_location_add')
        return format_html(
            '<a class="button" href="{}">{}</a> &nbsp; '
            '<a class="button" href="{}">{}</a>',
            url, _('Gerir locais'),
            add_url, _('+ Novo local'),
        )

    @admin.display(description=_('Métodos de entrega'))
    def delivery_methods_link(self, obj):
        url = reverse('admin:catalog_deliverymethod_changelist')
        add_url = reverse('admin:catalog_deliverymethod_add')
        return format_html(
            '<a class="button" href="{}">{}</a> &nbsp; '
            '<a class="button" href="{}">{}</a>',
            url, _('Gerir métodos'),
            add_url, _('+ Novo método'),
        )


