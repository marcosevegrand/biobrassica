from django.utils.translation import get_language

from apps.core.site_content import get_public_store_locations, get_website_defaults


def contact_locations(request):
    if getattr(request, 'subdomain', None) == 'admin':
        return {}

    locations = get_public_store_locations()

    return {
        'contact_locations': locations,
        'website_defaults': get_website_defaults(
            request=request,
            lang=getattr(request, 'LANGUAGE_CODE', None) or get_language(),
            contact_locations=locations,
        ),
    }
