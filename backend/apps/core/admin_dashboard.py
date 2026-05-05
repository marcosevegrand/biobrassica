from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.catalog.models import Product
from apps.content.models import BlogPost, Recipe
from apps.orders.models import Order
from apps.payments.models import Payment


def build_admin_dashboard(request, context):
    product_queryset = Product.objects.annotate(
        pt_translation_count=Count('translations', filter=Q(translations__language='pt'), distinct=True),
        primary_image_count=Count('images', filter=Q(images__is_primary=True), distinct=True),
        location_count=Count('available_locations', distinct=True),
    )
    products_with_gaps = product_queryset.filter(Q(pt_translation_count=0) | Q(primary_image_count=0))
    out_of_stock_products = product_queryset.filter(is_active=True, stock=0)
    low_stock_products = product_queryset.filter(is_active=True, stock__gt=0, stock__lt=5)
    customers_needing_follow_up = User.objects.annotate(
        default_address_count=Count('addresses', filter=Q(addresses__is_default=True), distinct=True),
    ).filter(is_active=True).filter(Q(phone='') | Q(default_address_count=0)).distinct()

    payment_pending_orders = Order.objects.filter(
        payment_state=Order.PaymentState.PENDING,
        status=Order.Status.PENDING,
        payment__isnull=False,
    )
    paid_orders = Order.objects.filter(payment_state=Order.PaymentState.CONFIRMED).exclude(
        status=Order.Status.CANCELLED,
    ).exclude(payment__status=Payment.Status.REFUNDED)
    today = timezone.localdate()
    todays_pickups = Order.objects.filter(
        fulfillment_method=Order.FulfillmentMethod.PICKUP,
        payment_state=Order.PaymentState.CONFIRMED,
        status__in=[Order.Status.PENDING, Order.Status.PREPARING, Order.Status.READY],
        created_at__date=today,
    ).exclude(payment__status=Payment.Status.REFUNDED)
    payments_requiring_attention = Payment.objects.filter(status=Payment.Status.PENDING)
    failed_payment_recovery = Payment.objects.filter(status=Payment.Status.CANCELLED)
    draft_blog_posts = BlogPost.objects.filter(is_published=False)
    draft_recipes = Recipe.objects.filter(is_published=False)
    active_accounts = User.objects.filter(is_active=True)
    paid_payments = Payment.objects.filter(status=Payment.Status.CONFIRMED)

    paid_orders_total = paid_orders.aggregate(gross_total=Sum('total'), average=Avg('total'))
    paid_payments_total = paid_payments.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0')),
    )
    average_paid_order_total = paid_orders_total['average'] or Decimal('0')

    context['dashboard_generated_at'] = timezone.localtime()
    context['dashboard_metric_cards'] = [
        {
            'label': _('Contas ativas'),
            'value': active_accounts.count(),
            'context': _('Clientes e equipa com acesso ativo'),
            'icon': 'group',
            'link': reverse('admin:accounts_user_changelist') + '?is_active__exact=1',
        },
        {
            'label': _('Encomendas pagas'),
            'value': paid_orders.count(),
            'context': _('Pedidos já convertidos em receita'),
            'icon': 'receipt_long',
            'link': reverse('admin:orders_order_changelist') + f'?payment_state__exact={Order.PaymentState.CONFIRMED}',
        },
        {
            'label': _('Volume transacionado'),
            'value': f"{paid_payments_total['total']:.2f}€",
            'context': _('Total confirmado em pagamentos pagos'),
            'icon': 'payments',
            'link': reverse('admin:payments_payment_changelist') + f'?status__exact={Payment.Status.CONFIRMED}',
        },
        {
            'label': _('Ticket médio'),
            'value': f"{average_paid_order_total:.2f}€",
            'context': _('Valor médio por encomenda paga'),
            'icon': 'monitoring',
            'link': reverse('admin:orders_order_changelist'),
        },
        {
            'label': _('A cobrar'),
            'value': payment_pending_orders.count(),
            'context': _('Encomendas à espera de pagamento confirmado'),
            'icon': 'shopping_bag',
            'link': reverse('admin:orders_order_changelist') + f'?payment_state__exact={Order.PaymentState.PENDING}',
        },
        {
            'label': _('Conteúdo em rascunho'),
            'value': draft_blog_posts.count() + draft_recipes.count(),
            'context': _('Blog e receitas por publicar'),
            'icon': 'edit_note',
            'link': reverse('admin:content_blogpost_changelist') + '?is_published__exact=0',
        },
        {
            'label': _('Reposição urgente'),
            'value': out_of_stock_products.count(),
            'context': _('Produtos ativos em rutura'),
            'icon': 'inventory_2',
            'link': reverse('admin:catalog_product_changelist') + '?ops_queue=out-of-stock',
        },
        {
            'label': _('Stock baixo'),
            'value': low_stock_products.count(),
            'context': _('Cobertura curta para a semana'),
            'icon': 'warning',
            'link': reverse('admin:catalog_product_changelist') + '?ops_queue=low-stock',
        },
        {
            'label': _('Produtos com lacunas'),
            'value': products_with_gaps.count(),
            'context': _('Sem tradução PT ou sem imagem principal'),
            'icon': 'broken_image',
            'link': reverse('admin:catalog_product_changelist') + '?ops_queue=missing-image',
        },
    ]

    recent_order_items = [
        {
            'title': f'Encomenda #{order.pk}',
            'meta': f'{order.name} · {Order.Status(order.status).label} · {timezone.localtime(order.created_at).strftime("%d/%m %H:%M")}',
            'badge': Order.Status(order.status).label,
            'link': reverse('admin:orders_order_change', args=[order.pk]),
        }
        for order in Order.objects.order_by('-created_at')[:5]
    ]

    customer_follow_up_items = [
        {
            'title': customer.email,
            'meta': ' · '.join(
                part
                for part in [
                    customer.get_full_name() or str(_('Sem nome definido')),
                    str(_('Sem telefone')) if not customer.phone else str(_('Telefone OK')),
                    str(_('Sem morada predefinida')) if not getattr(customer, 'default_address_count', 0) else str(_('Morada pronta')),
                ]
                if part
            ),
            'badge': _('Acompanhar'),
            'link': reverse('admin:accounts_user_change', args=[customer.pk]),
        }
        for customer in customers_needing_follow_up.order_by('-date_joined')[:5]
    ]

    payment_items = [
        {
            'title': f'Pagamento #{payment.pk}',
            'meta': f'{payment.order.name} · {Payment.Status(payment.status).label} · {Payment.Method(payment.method).label}',
            'badge': Payment.Status(payment.status).label,
            'link': reverse('admin:payments_payment_change', args=[payment.pk]),
        }
        for payment in payments_requiring_attention.select_related('order').order_by('-created_at')[:5]
    ]

    failed_payment_items = [
        {
            'title': f'Pagamento #{payment.pk}',
            'meta': f'{payment.order.name} · {Payment.Status(payment.status).label} · {timezone.localtime(payment.created_at).strftime("%d/%m %H:%M")}',
            'badge': _('Recuperar'),
            'link': reverse('admin:payments_payment_change', args=[payment.pk]),
        }
        for payment in failed_payment_recovery.select_related('order').order_by('-created_at')[:5]
    ]

    todays_pickup_items = [
        {
            'title': f'Encomenda #{order.pk}',
            'meta': f'{order.name} · {order.get_pickup_location_display() if order.pickup_location else "—"} · {Order.Status(order.status).label}',
            'badge': _('Hoje'),
            'link': reverse('admin:orders_order_change', args=[order.pk]),
        }
        for order in todays_pickups.order_by('created_at')[:6]
    ]

    replenishment_items = [
        {
            'title': str(product),
            'meta': ' · '.join(
                part
                for part in [
                    f'Stock {product.stock}',
                    product.brand,
                    _('%(count)s localizações') % {'count': getattr(product, 'location_count', 0)},
                ]
                if part
            ),
            'badge': _('Rutura') if product.stock == 0 else _('Baixo stock'),
            'link': reverse('admin:catalog_product_change', args=[product.pk]),
        }
        for product in product_queryset.filter(Q(is_active=True, stock=0) | Q(is_active=True, stock__gt=0, stock__lt=5)).order_by('stock', 'updated_at')[:6]
    ]

    draft_content_items = [
        {
            'title': str(post),
            'meta': _('Blog') + f' · {timezone.localtime(post.created_at).strftime("%d/%m %H:%M")}',
            'badge': _('Rascunho'),
            'link': reverse('admin:content_blogpost_change', args=[post.pk]),
        }
        for post in draft_blog_posts.order_by('-created_at')[:3]
    ] + [
        {
            'title': str(recipe),
            'meta': _('Receita') + f' · {timezone.localtime(recipe.created_at).strftime("%d/%m %H:%M")}',
            'badge': _('Rascunho'),
            'link': reverse('admin:content_recipe_change', args=[recipe.pk]),
        }
        for recipe in draft_recipes.order_by('-created_at')[:3]
    ]

    context['dashboard_panels'] = [
        {
            'title': _('Fila operacional'),
            'description': _('Pedidos que exigem decisão nas próximas horas.'),
            'items': recent_order_items,
            'empty': _('Sem encomendas recentes.'),
            'link': reverse('admin:orders_order_changelist'),
        },
        {
            'title': _('Levantamentos de hoje'),
            'description': _('Pedidos pickup com atividade prevista para hoje.'),
            'items': todays_pickup_items,
            'empty': _('Sem levantamentos planeados para hoje.'),
            'link': reverse('admin:orders_order_changelist') + f'?fulfillment_method__exact={Order.FulfillmentMethod.PICKUP}',
        },
        {
            'title': _('Reposição urgente'),
            'description': _('Produtos com rutura ou cobertura curta para a semana.'),
            'items': replenishment_items,
            'empty': _('Sem alertas de reposição neste momento.'),
            'link': reverse('admin:catalog_product_changelist') + '?ops_queue=low-stock',
        },
        {
            'title': _('Clientes a acompanhar'),
            'description': _('Perfis ativos com dados incompletos para suporte ou checkout.'),
            'items': customer_follow_up_items,
            'empty': _('Todos os clientes ativos têm a base de dados completa.'),
            'link': reverse('admin:accounts_user_changelist'),
        },
        {
            'title': _('Pagamentos recentes'),
            'description': _('Estado dos últimos pagamentos gerados.'),
            'items': payment_items,
            'empty': _('Sem pagamentos registados.'),
            'link': reverse('admin:payments_payment_changelist'),
        },
        {
            'title': _('Recuperação de pagamentos'),
            'description': _('Pagamentos cancelados que podem exigir acompanhamento do suporte.'),
            'items': failed_payment_items,
            'empty': _('Sem pagamentos cancelados para acompanhar.'),
            'link': reverse('admin:payments_payment_changelist') + f'?status__exact={Payment.Status.CANCELLED}',
        },
        {
            'title': _('Conteúdo por publicar'),
            'description': _('Rascunhos mais recentes à espera de revisão.'),
            'items': draft_content_items[:5],
            'empty': _('Não há rascunhos urgentes neste momento.'),
            'link': reverse('admin:content_blogpost_changelist') + '?is_published__exact=0',
        },
    ]

    return context
