from django.db import connection
from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language

from apps.core.pagination import paginate_queryset
from apps.content.querysets import (
    published_blogpost_queryset,
    published_recipe_queryset,
    recipe_detail_queryset,
)


BLOG_POSTS_PER_PAGE = 9
RECIPES_PER_PAGE = 9


def _filter_queryset_by_tag(queryset, *, tag):
    normalized_tag = (tag or '').strip()
    if not normalized_tag:
        return queryset

    if connection.features.supports_json_field_contains:
        return queryset.filter(tags__contains=[normalized_tag])

    matching_ids = [
        instance.pk
        for instance in queryset
        if normalized_tag in getattr(instance, 'tags_list', [])
    ]
    return queryset.filter(pk__in=matching_ids)


def blog_list(request):
    """List published blog posts."""
    lang = get_language() or 'pt'
    posts = published_blogpost_queryset(lang=lang)

    tag = request.GET.get('tag')
    if tag:
        posts = _filter_queryset_by_tag(posts, tag=tag)

    pagination = paginate_queryset(request, posts, per_page=BLOG_POSTS_PER_PAGE)

    return render(request, 'content/blog_list.html', {
        'posts': pagination['page_obj'].object_list,
        'current_tag': tag,
        'lang': lang,
        **pagination,
    })


def blog_detail(request, slug):
    """Single blog post detail."""
    lang = get_language() or 'pt'
    post = get_object_or_404(
        published_blogpost_queryset(lang=lang),
        slug=slug,
    )

    return render(request, 'content/blog_detail.html', {
        'post': post,
        'lang': lang,
    })


def recipe_list(request):
    """List published recipes."""
    lang = get_language() or 'pt'
    recipes = published_recipe_queryset(lang=lang)

    tag = request.GET.get('tag')
    if tag:
        recipes = _filter_queryset_by_tag(recipes, tag=tag)

    pagination = paginate_queryset(request, recipes, per_page=RECIPES_PER_PAGE)

    return render(request, 'content/recipe_list.html', {
        'recipes': pagination['page_obj'].object_list,
        'current_tag': tag,
        'lang': lang,
        **pagination,
    })


def recipe_detail(request, slug):
    """Single recipe detail with related products."""
    lang = get_language() or 'pt'
    recipe = get_object_or_404(
        recipe_detail_queryset(lang=lang),
        slug=slug,
    )
    related_products = list(recipe.related_products.all())

    return render(request, 'content/recipe_detail.html', {
        'recipe': recipe,
        'related_products': related_products,
        'translation': recipe.safe_translation,
        'lang': lang,
    })
