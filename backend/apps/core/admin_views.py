"""Custom admin views (Painel operacional, etc.)."""

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.orders.models import Order


# Status columns to display on the Painel operacional.
CALENDARIO_COLUMNS = (
    Order.Status.PENDING,
    Order.Status.PAYMENT_PENDING,
    Order.Status.PAID,
    Order.Status.PREPARING,
    Order.Status.READY,
    Order.Status.IN_TRANSIT,
)


def calendario_view(request):
    """Painel operacional das encomendas em curso."""
    order_admin = admin.site._registry[Order]
    if not order_admin.has_view_or_change_permission(request):
        raise PermissionDenied

    qs = (
        Order.objects.exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
        .select_related('payment', 'user')
        .order_by('-created_at')
    )

    by_status = {status: [] for status in CALENDARIO_COLUMNS}
    for order in qs:
        if order.status in by_status:
            by_status[order.status].append(order)

    columns = []
    for status in CALENDARIO_COLUMNS:
        orders = by_status[status]
        columns.append({
            'status': status,
            'label': Order.Status(status).label,
            'count': len(orders),
            'orders': orders,
        })

    request.current_app = admin.site.name
    context = {
        **admin.site.each_context(request),
        'title': _('Painel'),
        'subtitle': None,
        'opts': Order._meta,
        'app_label': Order._meta.app_label,
        'columns': columns,
        'changelist_url': reverse('admin:orders_order_changelist'),
    }
    return TemplateResponse(request, 'admin/core/calendario.html', context)
