from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils.translation import get_language

from apps.catalog.querysets import (
    display_category_queryset,
    display_product_queryset,
    highlighted_product_queryset,
    latest_product_queryset,
    product_detail_queryset,
)
from apps.core.pagination import paginate_queryset


PRODUCTS_PER_PAGE = 12


def shop_home(request):
    lang = get_language() or 'pt'
    highlights = highlighted_product_queryset(lang=lang)[:8]
    latest = latest_product_queryset(lang=lang)[:4]
    categories = display_category_queryset(lang=lang)
    return render(request, 'catalog/shop_home.html', {
        'highlights': highlights,
        'latest_products': latest,
        'categories': categories,
    })


def product_list(request):
    lang = get_language() or 'pt'
    categories = display_category_queryset(lang=lang)[:10]
    products = display_product_queryset(lang=lang)

    category_slug = request.GET.get('categoria')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    search = request.GET.get('q')
    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(brand__icontains=search)
            | Q(description__icontains=search)
            | Q(translations__name__icontains=search)
            | Q(translations__description__icontains=search)
        ).distinct()

    pagination = paginate_queryset(request, products, per_page=PRODUCTS_PER_PAGE)

    return render(request, 'catalog/product_list.html', {
        'products': pagination['page_obj'].object_list,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search or '',
        **pagination,
    })


def category_detail(request, slug):
    lang = get_language() or 'pt'
    category = get_object_or_404(display_category_queryset(lang=lang), slug=slug)
    products = display_product_queryset(lang=lang).filter(category=category)
    pagination = paginate_queryset(request, products, per_page=PRODUCTS_PER_PAGE)

    return render(request, 'catalog/category_detail.html', {
        'category': category,
        'products': pagination['page_obj'].object_list,
        **pagination,
    })


def product_detail(request, slug):
    lang = get_language() or 'pt'
    product = get_object_or_404(
        product_detail_queryset(lang=lang),
        slug=slug,
    )
    related = display_product_queryset(lang=lang).filter(category=product.category).exclude(pk=product.pk)[:4]

    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'related_products': related,
    })
