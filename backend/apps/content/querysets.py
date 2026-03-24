from django.db.models import Prefetch

from apps.catalog.querysets import active_product_queryset
from apps.content.models import BlogPost, BlogPostTranslation, Recipe, RecipeTranslation
from apps.core.translations import translation_prefetch


def published_blogpost_queryset(*, lang=None):
    return BlogPost.objects.filter(is_published=True).select_related('author').prefetch_related(
        translation_prefetch(BlogPostTranslation, lang=lang),
    )


def published_recipe_queryset(*, lang=None):
    return Recipe.objects.filter(is_published=True).prefetch_related(
        translation_prefetch(RecipeTranslation, lang=lang),
    )


def featured_recipe_queryset(*, lang=None, limit=3):
    return published_recipe_queryset(lang=lang).order_by('-created_at')[:limit]


def recipe_detail_queryset(*, lang=None):
    return published_recipe_queryset(lang=lang).prefetch_related(
        Prefetch('related_products', queryset=active_product_queryset(lang=lang)),
    )