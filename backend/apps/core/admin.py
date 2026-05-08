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
    fields = (
        'is_shop_active',
        'min_order_total',
        'payment_timeout_minutes',
        'checkout_reservation_minutes',
        'mbway_enabled',
        'mbway_number',
        'bank_transfer_enabled',
        'bank_beneficiary',
        'bank_iban',
        'bank_bic',
        'locations_link',
        'delivery_methods_link',
        'updated_at',
    )
    readonly_fields = ('updated_at', 'locations_link', 'delivery_methods_link')
    compressed_fields = True

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

