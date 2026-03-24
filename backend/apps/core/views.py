from django.shortcuts import render
from django.utils.translation import get_language

from apps.catalog.querysets import highlighted_product_queryset


def home(request):
    lang = get_language() or 'pt'
    highlights = highlighted_product_queryset(lang=lang)[:8]
    return render(request, 'core/home.html', {
        'highlights': highlights,
        'lang': lang,
    })
