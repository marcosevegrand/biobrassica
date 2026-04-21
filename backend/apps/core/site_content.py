from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import override

from apps.catalog.models import Location
from apps.core.translations import normalized_language
from apps.website.models import WebsiteContent


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

DEFAULT_COMPANY_LEGAL_NAME = 'Biobrassica, Lda.'
DEFAULT_COMPANY_ADDRESS = 'R. dos Capelistas 121, 4700-215 Braga'
DEFAULT_SUPPORT_EMAIL = 'geral@biobrassica.pt'
DEFAULT_WHATSAPP_NUMBER = '+351938722638'
CONTACT_LOCATIONS_CACHE_KEY = 'core:contact_locations:v1'
CONTACT_LOCATIONS_CACHE_TIMEOUT = 300


def _normalize_whatsapp_number(number):
    return ''.join(character for character in str(number or '') if character.isdigit())


def _display_location_name(name):
    return str(name or '').removeprefix('Loja ').strip()


def get_pickup_locations_label(*, lang=None, contact_locations=None):
    with override(normalized_language(lang)):
        if contact_locations is None:
            names = [
                _display_location_name(location.name)
                for location in Location.objects.filter(is_active=True).order_by('order', 'name')
                if _display_location_name(location.name)
            ]
        else:
            names = [
                _display_location_name(location.get('name'))
                for location in contact_locations
                if _display_location_name(location.get('name'))
            ]
        if not names:
            return gettext('Braga ou Guimarães')
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return gettext('%(first)s ou %(second)s') % {
                'first': names[0],
                'second': names[1],
            }
        return gettext('%(all_locations)s e %(last_location)s') % {
            'all_locations': ', '.join(names[:-1]),
            'last_location': names[-1],
        }


def get_website_defaults(*, lang=None, content=None, contact_locations=None):
    localized_content = content if content is not None else get_website_content(lang=lang)
    website_base_url = get_website_base_url()
    pickup_locations_label = get_pickup_locations_label(lang=lang, contact_locations=contact_locations)

    with override(normalized_language(lang)):
        defaults = {
            'company_legal_name': DEFAULT_COMPANY_LEGAL_NAME,
            'company_address': DEFAULT_COMPANY_ADDRESS,
            'support_email': DEFAULT_SUPPORT_EMAIL,
            'whatsapp_number': DEFAULT_WHATSAPP_NUMBER,
            'pickup_locations_label': pickup_locations_label,
            'website_meta_description': gettext(
                'Biobrassica — produtos biológicos selecionados com cuidado no coração do Minho.'
            ),
            'shop_meta_description': gettext(
                'Loja online Biobrassica — produtos biológicos de Braga e Guimarães.'
            ),
            'contacts_meta_description': gettext(
                'Entre em contacto com a Biobrassica. Lojas em Braga e Guimarães, ou contacte-nos por telefone e email.'
            ),
            'home_shop_cta_body': gettext(
                'Entrega em todo o Portugal continental ou levantamento nas nossas lojas em Braga e Guimarães.'
            ),
            'shop_home_hero_body': gettext(
                'Do campo para a sua porta. Encomende online e receba em casa ou levante nas nossas lojas em Braga e Guimarães.'
            ),
            'shop_visit_cta_body': gettext(
                'Prefere ver e escolher pessoalmente? Visite as nossas lojas em Braga e Guimarães. Teremos todo o gosto em recebê-lo.'
            ),
            'about_video_body': gettext(
                'Visite as nossas lojas em Braga e Guimarães para conhecer os nossos produtos e a nossa equipa.'
            ),
            'core_home_body': gettext(
                'Produtos biológicos selecionados no Minho. Encomende online e levante na nossa loja de Braga ou Guimarães.'
            ),
        }

        website_contacts_url = f"{website_base_url}{reverse('website:contacts', urlconf='config.urls_website')}"

    def resolved_value(attribute):
        if localized_content is None:
            return defaults[attribute]
        return getattr(localized_content, attribute, '') or defaults[attribute]

    whatsapp_number = resolved_value('whatsapp_number')
    whatsapp_number_normalized = _normalize_whatsapp_number(whatsapp_number)

    return {
        'company_legal_name': resolved_value('company_legal_name'),
        'company_address': resolved_value('company_address'),
        'support_email': resolved_value('support_email'),
        'whatsapp_number': whatsapp_number,
        'whatsapp_number_normalized': whatsapp_number_normalized,
        'whatsapp_url': f'https://wa.me/{whatsapp_number_normalized}',
        'pickup_locations_label': defaults['pickup_locations_label'],
        'website_base_url': website_base_url,
        'website_contacts_url': website_contacts_url,
        'website_meta_description': resolved_value('website_meta_description'),
        'shop_meta_description': resolved_value('shop_meta_description'),
        'contacts_meta_description': defaults['contacts_meta_description'],
        'home_shop_cta_body': resolved_value('home_shop_cta_body'),
        'shop_home_hero_body': defaults['shop_home_hero_body'],
        'shop_visit_cta_body': defaults['shop_visit_cta_body'],
        'about_video_body': resolved_value('about_video_body'),
        'core_home_body': defaults['core_home_body'],
    }


def get_payments_availability(*, content=None):
    if getattr(settings, 'PAYMENTS_FORCE_DISABLED', False):
        return {
            'enabled': False,
            'source': 'settings',
        }

    resolved_content = content
    if resolved_content is None:
        resolved_content = WebsiteContent.objects.filter(pk=1).only('payments_enabled').first()

    if resolved_content is None:
        return {
            'enabled': True,
            'source': 'default',
        }

    return {
        'enabled': bool(getattr(resolved_content, 'payments_enabled', True)),
        'source': 'database',
    }


def payments_are_enabled(*, content=None):
    return get_payments_availability(content=content)['enabled']


def get_website_content(lang=None):
    content = WebsiteContent.objects.filter(pk=1).first()
    if content is None:
        return None
    return content.for_language(lang=lang)


def get_shop_base_url():
    return settings.SHOP_BASE_URL.rstrip('/')


def get_website_base_url():
    configured_base_url = getattr(settings, 'WEBSITE_BASE_URL', '').strip()
    if configured_base_url:
        return configured_base_url.rstrip('/')
    return get_shop_base_url().replace('://loja.', '://', 1)


def clear_contact_locations_cache():
    cache.delete(CONTACT_LOCATIONS_CACHE_KEY)


def _build_contact_locations():
    locations = []
    default_email = DEFAULT_SUPPORT_EMAIL

    for location in Location.objects.filter(is_active=True).order_by('order', 'name'):
        default_key = 'guimaraes' if 'guimar' in location.name.lower() else 'braga'
        defaults = DEFAULT_LOCATION_CONTENT[default_key]
        locations.append({
            'name': location.name,
            'address_lines': [line.strip() for line in (location.address or '').splitlines() if line.strip()],
            'phone': location.phone or defaults['phone'],
            'email': location.email or default_email or defaults['email'],
            'opening_hours': [line.strip() for line in (location.opening_hours or defaults['opening_hours']).splitlines() if line.strip()],
            'map_embed_url': location.map_embed_url or defaults['map_embed_url'],
            'static_image': defaults['image'],
            'image': location.image,
        })

    return locations


def get_contact_locations():
    cached_locations = cache.get(CONTACT_LOCATIONS_CACHE_KEY)
    if cached_locations is not None:
        return cached_locations

    locations = _build_contact_locations()
    cache.set(CONTACT_LOCATIONS_CACHE_KEY, locations, CONTACT_LOCATIONS_CACHE_TIMEOUT)
    return locations