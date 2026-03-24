from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

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

    payment_pending_orders = Order.objects.filter(status=Order.Status.PAYMENT_PENDING)
    paid_orders = Order.objects.filter(
        status__in=[Order.Status.PAID, Order.Status.PREPARING, Order.Status.READY, Order.Status.DELIVERED],
    )
    today = timezone.localdate()
    todays_pickups = Order.objects.filter(
        fulfillment_method=Order.FulfillmentMethod.PICKUP,
        status__in=[Order.Status.PAID, Order.Status.PREPARING, Order.Status.READY],
        created_at__date=today,
    )
    payments_requiring_attention = Payment.objects.filter(status__in=[Payment.Status.PENDING, Payment.Status.FAILED])
    failed_payment_recovery = Payment.objects.filter(status__in=[Payment.Status.FAILED, Payment.Status.EXPIRED])
    draft_blog_posts = BlogPost.objects.filter(is_published=False)
    draft_recipes = Recipe.objects.filter(is_published=False)
    active_accounts = User.objects.filter(is_active=True)
    paid_payments = Payment.objects.filter(status=Payment.Status.PAID)

    paid_orders_total = paid_orders.aggregate(gross_total=Sum('total'), average=Avg('total'))
    paid_payments_total = paid_payments.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0')),
    )
    average_paid_order_total = paid_orders_total['average'] or Decimal('0')

    context['dashboard_generated_at'] = timezone.localtime()
    context['dashboard_metric_cards'] = [
        {
            'label': 'Contas ativas',
            'value': active_accounts.count(),
            'context': 'Clientes e equipa com acesso ativo',
            'icon': 'group',
            'link': reverse('admin:accounts_user_changelist') + '?is_active__exact=1',
        },
        {
            'label': 'Encomendas pagas',
            'value': paid_orders.count(),
            'context': 'Pedidos já convertidos em receita',
            'icon': 'receipt_long',
            'link': reverse('admin:orders_order_changelist') + f'?status__exact={Order.Status.PAID}',
        },
        {
            'label': 'Volume transacionado',
            'value': f"{paid_payments_total['total']:.2f}€",
            'context': 'Total confirmado em pagamentos pagos',
            'icon': 'payments',
            'link': reverse('admin:payments_payment_changelist') + f'?status__exact={Payment.Status.PAID}',
        },
        {
            'label': 'Ticket médio',
            'value': f"{average_paid_order_total:.2f}€",
            'context': 'Valor médio por encomenda paga',
            'icon': 'monitoring',
            'link': reverse('admin:orders_order_changelist'),
        },
        {
            'label': 'A cobrar',
            'value': payment_pending_orders.count(),
            'context': 'Encomendas à espera de pagamento confirmado',
            'icon': 'shopping_bag',
            'link': reverse('admin:orders_order_changelist') + f'?status__exact={Order.Status.PAYMENT_PENDING}',
        },
        {
            'label': 'Conteúdo em rascunho',
            'value': draft_blog_posts.count() + draft_recipes.count(),
            'context': 'Blog e receitas por publicar',
            'icon': 'edit_note',
            'link': reverse('admin:content_blogpost_changelist') + '?is_published__exact=0',
        },
        {
            'label': 'Reposição urgente',
            'value': out_of_stock_products.count(),
            'context': 'Produtos ativos em rutura',
            'icon': 'inventory_2',
            'link': reverse('admin:catalog_product_changelist') + '?ops_queue=out-of-stock',
        },
        {
            'label': 'Stock baixo',
            'value': low_stock_products.count(),
            'context': 'Cobertura curta para a semana',
            'icon': 'warning',
            'link': reverse('admin:catalog_product_changelist') + '?ops_queue=low-stock',
        },
        {
            'label': 'Produtos com lacunas',
            'value': products_with_gaps.count(),
            'context': 'Sem tradução PT ou sem imagem principal',
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
                    customer.get_full_name() or 'Sem nome definido',
                    'Sem telefone' if not customer.phone else 'Telefone OK',
                    'Sem morada predefinida' if not getattr(customer, 'default_address_count', 0) else 'Morada pronta',
                ]
                if part
            ),
            'badge': 'Acompanhar',
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
            'badge': 'Recuperar',
            'link': reverse('admin:payments_payment_change', args=[payment.pk]),
        }
        for payment in failed_payment_recovery.select_related('order').order_by('-created_at')[:5]
    ]

    todays_pickup_items = [
        {
            'title': f'Encomenda #{order.pk}',
            'meta': f'{order.name} · {order.get_pickup_location_display()} · {Order.Status(order.status).label}',
            'badge': 'Hoje',
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
                    f'{getattr(product, "location_count", 0)} localizações',
                ]
                if part
            ),
            'badge': 'Rutura' if product.stock == 0 else 'Baixo stock',
            'link': reverse('admin:catalog_product_change', args=[product.pk]),
        }
        for product in product_queryset.filter(Q(is_active=True, stock=0) | Q(is_active=True, stock__gt=0, stock__lt=5)).order_by('stock', 'updated_at')[:6]
    ]

    draft_content_items = [
        {
            'title': str(post),
            'meta': f'Blog · {timezone.localtime(post.created_at).strftime("%d/%m %H:%M")}',
            'badge': 'Rascunho',
            'link': reverse('admin:content_blogpost_change', args=[post.pk]),
        }
        for post in draft_blog_posts.order_by('-created_at')[:3]
    ] + [
        {
            'title': str(recipe),
            'meta': f'Receita · {timezone.localtime(recipe.created_at).strftime("%d/%m %H:%M")}',
            'badge': 'Rascunho',
            'link': reverse('admin:content_recipe_change', args=[recipe.pk]),
        }
        for recipe in draft_recipes.order_by('-created_at')[:3]
    ]

    context['dashboard_panels'] = [
        {
            'title': 'Fila operacional',
            'description': 'Pedidos que exigem decisão nas próximas horas.',
            'items': recent_order_items,
            'empty': 'Sem encomendas recentes.',
            'link': reverse('admin:orders_order_changelist'),
        },
        {
            'title': 'Levantamentos de hoje',
            'description': 'Pedidos pickup com atividade prevista para hoje.',
            'items': todays_pickup_items,
            'empty': 'Sem levantamentos planeados para hoje.',
            'link': reverse('admin:orders_order_changelist') + f'?fulfillment_method__exact={Order.FulfillmentMethod.PICKUP}',
        },
        {
            'title': 'Reposição urgente',
            'description': 'Produtos com rutura ou cobertura curta para a semana.',
            'items': replenishment_items,
            'empty': 'Sem alertas de reposição neste momento.',
            'link': reverse('admin:catalog_product_changelist') + '?ops_queue=low-stock',
        },
        {
            'title': 'Clientes a acompanhar',
            'description': 'Perfis ativos com dados incompletos para suporte ou checkout.',
            'items': customer_follow_up_items,
            'empty': 'Todos os clientes ativos têm a base de dados completa.',
            'link': reverse('admin:accounts_user_changelist'),
        },
        {
            'title': 'Pagamentos recentes',
            'description': 'Estado dos últimos pagamentos gerados.',
            'items': payment_items,
            'empty': 'Sem pagamentos registados.',
            'link': reverse('admin:payments_payment_changelist'),
        },
        {
            'title': 'Recuperação de pagamentos',
            'description': 'Cobranças expiradas ou falhadas a recuperar pelo suporte.',
            'items': failed_payment_items,
            'empty': 'Sem pagamentos falhados para recuperar.',
            'link': reverse('admin:payments_payment_changelist') + f'?status__exact={Payment.Status.FAILED}',
        },
        {
            'title': 'Conteúdo por publicar',
            'description': 'Rascunhos mais recentes à espera de revisão.',
            'items': draft_content_items[:5],
            'empty': 'Não há rascunhos urgentes neste momento.',
            'link': reverse('admin:content_blogpost_changelist') + '?is_published__exact=0',
        },
    ]

    return context