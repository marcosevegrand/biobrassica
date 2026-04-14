from django.utils.translation import get_language

from apps.core.site_content import get_contact_locations, get_website_defaults


def contact_locations(request):
    if getattr(request, 'subdomain', None) == 'admin':
        return {}

    locations = get_contact_locations()

    return {
        'contact_locations': locations,
        'website_defaults': get_website_defaults(
            lang=getattr(request, 'LANGUAGE_CODE', None) or get_language(),
            contact_locations=locations,
        ),
    }