from django.shortcuts import render
from django.utils.translation import get_language

from apps.core.site_content import get_website_content
from apps.content.querysets import featured_recipe_queryset
from apps.website.models import TeamMember


def home(request):
    """Homepage — hero, values, featured recipes, shop CTA."""
    lang = get_language() or 'pt'
    featured_recipes = featured_recipe_queryset(lang=lang, limit=3)

    return render(request, 'website/home.html', {
        'featured_recipes': featured_recipes,
        'lang': lang,
        'website_content': get_website_content(lang=lang),

    })


def about(request):
    """Quem Somos — company story, values, timeline."""
    lang = get_language() or 'pt'
    return render(request, 'website/about.html', {
        'lang': lang,
        'team_members': TeamMember.objects.filter(is_active=True).select_related('sort_order').order_by('sort_order__position', 'name', 'pk'),
        'website_content': get_website_content(lang=lang),
    })


def agriculture(request):
    """Agricultura Biológica — organic farming, certifications, seasonal calendar."""
    lang = get_language() or 'pt'
    return render(request, 'website/agriculture.html', {
        'lang': lang,
        'website_content': get_website_content(lang=lang),
    })


def contacts(request):
    """Contactos — store locations, hours, maps."""
    lang = get_language() or 'pt'
    return render(request, 'website/contacts.html', {
        'lang': lang,
        'website_content': get_website_content(lang=lang),
    })


def _base_template(request):
    """Return the correct base template for the current subdomain."""
    if getattr(request, 'subdomain', None) == 'shop':
        return 'base.html'
    return 'base_website.html'


def privacy(request):
    """Política de Privacidade — RGPD compliance."""
    lang = get_language() or 'pt'
    return render(request, 'website/privacy.html', {
        'lang': lang,
        'base_template': _base_template(request),
        'website_content': get_website_content(lang=lang),
    })


def terms(request):
    """Termos e Condições — terms of service."""
    lang = get_language() or 'pt'
    return render(request, 'website/terms.html', {
        'lang': lang,
        'base_template': _base_template(request),
        'website_content': get_website_content(lang=lang),
    })
