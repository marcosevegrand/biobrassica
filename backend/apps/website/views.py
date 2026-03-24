from django.shortcuts import render
from django.utils.translation import get_language

from apps.catalog.models import Location
from apps.content.querysets import featured_recipe_queryset
from apps.website.models import TeamMember, WebsiteContent


DEFAULT_LOCATION_CONTENT = {
    'braga': {
        'image': 'images/shop/loja-braga.png',
        'phone': '253 271 187',
        'email': 'geral@biobrassica.pt',
        'opening_hours': 'Segunda a Sábado\n9h00 – 19h30',
        'map_embed_url': 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Braga+Avenida+Doutor+Ant%C3%B3nio+Palha&t=&z=16&ie=UTF8&iwloc=&output=embed',
    },
    'guimaraes': {
        'image': 'images/shop/loja-guima.png',
        'phone': '253 145 388',
        'email': 'geral@biobrassica.pt',
        'opening_hours': 'Segunda a Sábado\n9h00 – 19h30',
        'map_embed_url': 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Guimar%C3%A3es+Rua+Calouste+Gulbenkian&t=&z=16&ie=UTF8&iwloc=&output=embed',
    },
}


def get_website_content(lang=None):
    content = WebsiteContent.objects.first()
    if content is None:
        return None
    return content.for_language(lang=lang)


def get_contact_locations():
    locations = []
    for location in Location.objects.filter(is_active=True).order_by('order', 'name'):
        default_key = 'guimaraes' if 'guimar' in location.name.lower() else 'braga'
        defaults = DEFAULT_LOCATION_CONTENT[default_key]
        locations.append({
            'obj': location,
            'name': location.name,
            'address_lines': [line.strip() for line in (location.address or '').splitlines() if line.strip()],
            'phone': location.phone or defaults['phone'],
            'email': location.email or defaults['email'],
            'opening_hours': [line.strip() for line in (location.opening_hours or defaults['opening_hours']).splitlines() if line.strip()],
            'map_embed_url': location.map_embed_url or defaults['map_embed_url'],
            'static_image': defaults['image'],
            'image': location.image,
        })
    return locations


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
        'team_members': TeamMember.objects.filter(is_active=True).order_by('order', 'name'),
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
        'locations': get_contact_locations(),
    })


def _base_template(request):
    """Return the correct base template for the current subdomain."""
    if getattr(request, 'subdomain', None) == 'shop':
        return 'base.html'
    return 'base_website.html'


def privacy(request):
    """Política de Privacidade — RGPD compliance."""
    return render(request, 'website/privacy.html', {
        'lang': get_language() or 'pt',
        'base_template': _base_template(request),
    })


def terms(request):
    """Termos e Condições — terms of service."""
    return render(request, 'website/terms.html', {
        'lang': get_language() or 'pt',
        'base_template': _base_template(request),
    })
