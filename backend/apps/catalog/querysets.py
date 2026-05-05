from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation
from apps.core.translations import translation_prefetch


def active_category_queryset(*, lang=None):
    return Category.objects.filter(is_active=True).select_related('sort_order').prefetch_related(
        translation_prefetch(CategoryTranslation, lang=lang),
    )


def display_category_queryset(*, lang=None):
    return active_category_queryset(lang=lang).order_by('-is_special', 'sort_order__position', 'name', 'pk')


def active_product_queryset(*, lang=None):
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
        translation_prefetch(ProductTranslation, lang=lang),
        translation_prefetch(CategoryTranslation, related_name='category__translations', lang=lang),
        'pickup_locations',
    )
    if lang and lang != 'pt':
        queryset = queryset.filter(translations__language=lang)
    return queryset


def display_product_queryset(*, lang=None):
    return active_product_queryset(lang=lang).order_by('-is_highlight', 'name', 'pk')


def highlighted_product_queryset(*, lang=None):
    return display_product_queryset(lang=lang).filter(is_highlight=True)


def latest_product_queryset(*, lang=None):
    return active_product_queryset(lang=lang).order_by('-created_at')


def product_detail_queryset(*, lang=None):
    return active_product_queryset(lang=lang)
