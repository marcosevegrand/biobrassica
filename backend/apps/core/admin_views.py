"""Custom admin views (Calendário kanban, etc.)."""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.orders.models import Order


# Status columns to display on the Calendário kanban (excludes terminal states by default)
CALENDARIO_COLUMNS = (
    Order.Status.PENDING,
    Order.Status.PAYMENT_PENDING,
    Order.Status.PAID,
    Order.Status.PREPARING,
    Order.Status.READY,
    Order.Status.IN_TRANSIT,
)


@staff_member_required
def calendario_view(request):
    """Kanban-style overview of in-flight orders, grouped by status."""
    qs = (
        Order.objects.exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
        .select_related()
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

    context = {
        'title': _('Calendário'),
        'columns': columns,
        'changelist_url': reverse('admin:orders_order_changelist'),
        'has_permission': True,
        'site_header': 'Biobrassica',
        'site_title': 'Biobrassica',
        'site_url': '/',
        'is_popup': False,
        'is_nav_sidebar_enabled': True,
        'available_apps': [],
    }
    return render(request, 'admin/core/calendario.html', context)
