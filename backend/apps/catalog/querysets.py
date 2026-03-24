from django.db.models import Q

from apps.catalog.models import Category, CategoryTranslation, Product, ProductTranslation
from apps.core.translations import translation_prefetch, normalized_language


def active_category_queryset(*, lang=None):
    return Category.objects.filter(is_active=True).prefetch_related(
        translation_prefetch(CategoryTranslation, lang=lang),
    )


def display_category_queryset(*, lang=None):
    return active_category_queryset(lang=lang).order_by('-is_featured', 'slug')


def active_product_queryset(*, lang=None):
    # Filter to only include products that have a translation in the specified language
    normalized_lang = normalized_language(lang)
    return Product.objects.filter(
        is_active=True,
        translations__language=normalized_lang,
    ).distinct().select_related('category').prefetch_related(
        translation_prefetch(ProductTranslation, lang=lang),
        translation_prefetch(CategoryTranslation, related_name='category__translations', lang=lang),
        'images',
        'available_locations',
    )


def display_product_queryset(*, lang=None):
    return active_product_queryset(lang=lang).order_by('-is_highlight', '-created_at')


def highlighted_product_queryset(*, lang=None):
    return display_product_queryset(lang=lang).filter(is_highlight=True)


def latest_product_queryset(*, lang=None):
    return active_product_queryset(lang=lang).order_by('-created_at')


def product_detail_queryset(*, lang=None):
    return active_product_queryset(lang=lang)