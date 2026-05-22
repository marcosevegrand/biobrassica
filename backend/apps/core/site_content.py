import re
from ipaddress import ip_address

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import DisallowedHost, ValidationError
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import override

from apps.accounts.validators import normalize_portuguese_mobile_phone
from apps.catalog.models import Location
from apps.core.translations import normalized_language
from apps.website.models import WebsiteContent


DEFAULT_LOCATION_CONTENT = {
    'braga': {
        'image': 'images/shop/loja-braga.webp',
        'phone': '253 271 187',
        'email': 'geral@biobrassica.pt',
        'opening_hours': 'Segunda a Sábado\n9h00 – 19h30',
        'map_embed_url': 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Braga+Avenida+Doutor+Ant%C3%B3nio+Palha&t=&z=16&ie=UTF8&iwloc=&output=embed',
    },
    'guimaraes': {
        'image': 'images/shop/loja-guima.webp',
        'phone': '253 145 388',
        'email': 'geral@biobrassica.pt',
        'opening_hours': 'Segunda a Sábado\n9h00 – 19h30',
        'map_embed_url': 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Guimar%C3%A3es+Rua+Calouste+Gulbenkian&t=&z=16&ie=UTF8&iwloc=&output=embed',
    },
}

PUBLIC_STORE_LOCATIONS = [
    {
        'name': 'Loja Braga',
        'address_lines': ['Avenida Doutor António Palha', 'Braga'],
        'phone': DEFAULT_LOCATION_CONTENT['braga']['phone'],
        'email': DEFAULT_LOCATION_CONTENT['braga']['email'],
        'opening_hours': [line.strip() for line in DEFAULT_LOCATION_CONTENT['braga']['opening_hours'].splitlines() if line.strip()],
        'map_embed_url': DEFAULT_LOCATION_CONTENT['braga']['map_embed_url'],
        'static_image': DEFAULT_LOCATION_CONTENT['braga']['image'],
        'image': None,
    },
    {
        'name': 'Loja Guimarães',
        'address_lines': ['Rua Calouste Gulbenkian', 'Guimarães'],
        'phone': DEFAULT_LOCATION_CONTENT['guimaraes']['phone'],
        'email': DEFAULT_LOCATION_CONTENT['guimaraes']['email'],
        'opening_hours': [line.strip() for line in DEFAULT_LOCATION_CONTENT['guimaraes']['opening_hours'].splitlines() if line.strip()],
        'map_embed_url': DEFAULT_LOCATION_CONTENT['guimaraes']['map_embed_url'],
        'static_image': DEFAULT_LOCATION_CONTENT['guimaraes']['image'],
        'image': None,
    },
]

DEFAULT_COMPANY_LEGAL_NAME = 'Biobrassica, Lda.'
DEFAULT_COMPANY_ADDRESS = 'R. dos Capelistas 121, 4700-215 Braga'
DEFAULT_SUPPORT_EMAIL = 'geral@biobrassica.pt'
DEFAULT_WHATSAPP_NUMBER = '+351938722638'
CONTACT_LOCATIONS_CACHE_KEY = 'core:contact_locations:v1'
CONTACT_LOCATIONS_CACHE_TIMEOUT = 300
HOST_ROLE_PREFIXES = ('www.', 'loja.', 'admin.')
IBAN_RE = re.compile(r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$')
BIC_RE = re.compile(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$')


def _normalize_whatsapp_number(number):
    return ''.join(character for character in str(number or '') if character.isdigit())


def _display_location_name(name):
    return str(name or '').removeprefix('Loja ').strip()


def _strip_host_port(host):
    return str(host or '').split(':', 1)[0].strip().lower()


def _is_ip_host(host):
    try:
        ip_address(host)
    except ValueError:
        return False
    return True


def _host_family_domain(host):
    normalized_host = _strip_host_port(host)
    if not normalized_host or normalized_host == '*' or _is_ip_host(normalized_host):
        return ''
    if '.' not in normalized_host and normalized_host != 'localhost':
        return ''

    for prefix in HOST_ROLE_PREFIXES:
        if normalized_host.startswith(prefix):
            return normalized_host.removeprefix(prefix)

    return normalized_host


def _configured_public_domains():
    configured_domains = []
    configured_hosts = [
        *(getattr(settings, 'PUBLIC_DOMAINS', []) or []),
        *(getattr(settings, 'WEBSITE_ALLOWED_HOSTS', []) or []),
        *(getattr(settings, 'SHOP_ALLOWED_HOSTS', []) or []),
        *(getattr(settings, 'ADMIN_ALLOWED_HOSTS', []) or []),
        *(getattr(settings, 'ALLOWED_HOSTS', []) or []),
        getattr(settings, 'WEBSITE_HOST', ''),
        getattr(settings, 'SHOP_HOST', ''),
        getattr(settings, 'ADMIN_HOST', ''),
    ]

    for configured_host in configured_hosts:
        resolved_domain = _host_family_domain(configured_host)
        if resolved_domain:
            configured_domains.append(resolved_domain)

    return list(dict.fromkeys(configured_domains))


def _request_public_domain(request):
    if request is None:
        return ''

    try:
        request_host = _strip_host_port(request.get_host())
    except DisallowedHost:
        return ''

    for domain in _configured_public_domains():
        if request_host in {
            domain,
            f'www.{domain}',
            f'loja.{domain}',
            f'admin.{domain}',
        }:
            return domain

    return ''


def get_pickup_locations_label(*, lang=None, contact_locations=None):
    with override(normalized_language(lang)):
        if contact_locations is None:
            names = [
                _display_location_name(location['name'])
                for location in PUBLIC_STORE_LOCATIONS
                if _display_location_name(location['name'])
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


def get_website_defaults(*, request=None, lang=None, content=None, contact_locations=None):
    localized_content = content if content is not None else get_website_content(lang=lang)
    website_base_url = get_website_base_url(request=request)
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
        'is_shop_brevemente': _get_is_shop_brevemente(),
    }


def get_payments_availability(*, content=None):
    """Return whether the shop is open for payments.

    Reads the shop pause toggle from ``ShopSettings`` and method credentials
    from environment-backed Django settings. The ``content`` kwarg is kept for
    backwards compatibility but is ignored.
    """
    from apps.core.models import ShopSettings

    settings_obj = ShopSettings.objects.filter(pk=1).only('is_shop_active').first()
    if settings_obj is None:
        return {'enabled': False, 'source': 'default'}
    has_configured_payment_method = (
        get_manual_mbway_details()['configured']
        or get_bank_transfer_details()['configured']
    )

    return {
        'enabled': bool(settings_obj.is_shop_active and has_configured_payment_method),
        'source': 'database',
    }


def get_manual_mbway_details(*, content=None):
    from apps.core.models import ShopSettings

    settings_obj = ShopSettings.objects.filter(pk=1).only('mbway_enabled').first()
    number = ''
    enabled = False
    if settings_obj is not None:
        enabled = bool(settings_obj.mbway_enabled)
    configured_number = str(getattr(settings, 'MANUAL_MBWAY_NUMBER', '') or '')
    if configured_number:
        try:
            number = normalize_portuguese_mobile_phone(configured_number)
        except ValidationError:
            number = ''

    return {
        'configured': bool(enabled and number),
        'enabled': enabled,
        'number': number,
        'digits': _normalize_whatsapp_number(number),
    }


def get_bank_transfer_details(*, content=None):
    from apps.core.models import ShopSettings

    settings_obj = ShopSettings.objects.filter(pk=1).only('bank_transfer_enabled').first()
    enabled = bool(settings_obj and settings_obj.bank_transfer_enabled)
    beneficiary = str(getattr(settings, 'BANK_TRANSFER_BENEFICIARY', '') or '').strip()
    iban = ''.join(str(getattr(settings, 'BANK_TRANSFER_IBAN', '') or '').split()).upper()
    bic = ''.join(str(getattr(settings, 'BANK_TRANSFER_BIC', '') or '').split()).upper()
    has_valid_bank_details = bool(
        beneficiary
        and iban
        and IBAN_RE.match(iban)
        and (not bic or BIC_RE.match(bic))
    )

    return {
        'configured': bool(enabled and has_valid_bank_details),
        'enabled': enabled,
        'beneficiary': beneficiary,
        'iban': iban,
        'bic': bic,
    }


def payments_are_enabled(*, content=None):
    return get_payments_availability(content=content)['enabled']


def get_website_content(lang=None):
    content = WebsiteContent.objects.filter(pk=1).first()
    if content is None:
        return None
    return content.for_language(lang=lang)


def _get_is_shop_brevemente():
    from apps.core.models import ShopSettings

    settings_obj = ShopSettings.objects.filter(pk=1).only('is_shop_brevemente').first()
    if settings_obj is None:
        return False
    return bool(settings_obj.is_shop_brevemente)


def get_shop_base_url(*, request=None):
    request_domain = _request_public_domain(request)
    if request_domain:
        return f'https://loja.{request_domain}'

    return settings.SHOP_BASE_URL.rstrip('/')


def get_website_base_url(*, request=None):
    request_domain = _request_public_domain(request)
    if request_domain:
        return f'https://{request_domain}'

    configured_base_url = getattr(settings, 'WEBSITE_BASE_URL', '').strip()
    if configured_base_url:
        return configured_base_url.rstrip('/')
    return get_shop_base_url().replace('://loja.', '://', 1)


def clear_contact_locations_cache():
    cache.delete(CONTACT_LOCATIONS_CACHE_KEY)


def _build_contact_locations():
    locations = []
    default_email = DEFAULT_SUPPORT_EMAIL

    for location in Location.objects.filter(is_active=True).select_related('sort_order').order_by('sort_order__position', 'name', 'pk'):
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


def get_public_store_locations():
    return [dict(location) for location in PUBLIC_STORE_LOCATIONS]


def get_contact_locations():
    cached_locations = cache.get(CONTACT_LOCATIONS_CACHE_KEY)
    if cached_locations is not None:
        return cached_locations

    locations = _build_contact_locations()
    cache.set(CONTACT_LOCATIONS_CACHE_KEY, locations, CONTACT_LOCATIONS_CACHE_TIMEOUT)
    return locations
