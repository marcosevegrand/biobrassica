from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils import translation


SITE_URLCONFS = {
    'website': 'config.urls_website',
    'shop': 'config.urls_shop',
    'admin': 'config.urls_admin',
}


def resolve_site_role(host):
    forced_site_role = getattr(settings, 'SITE_ROLE', '')
    if forced_site_role in SITE_URLCONFS:
        return forced_site_role, SITE_URLCONFS[forced_site_role]

    if host.startswith('loja.'):
        return 'shop', SITE_URLCONFS['shop']
    if host.startswith('admin.'):
        return 'admin', SITE_URLCONFS['admin']
    return 'website', SITE_URLCONFS['website']


class SubdomainMiddleware:
    """
    Route requests to subdomain-specific URL configurations.

    - loja.* → config.urls_shop
    - admin.* → config.urls_admin
    - everything else → config.urls_website
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        request.subdomain, request.urlconf = resolve_site_role(host)

        if request.subdomain == 'admin':
            previous_language = translation.get_language()
            translation.activate('pt')
            request.LANGUAGE_CODE = 'pt'
            try:
                response = self.get_response(request)
            finally:
                translation.activate(previous_language)
        else:
            response = self.get_response(request)

        if request.subdomain == 'admin':
            response.headers.setdefault('Content-Language', 'pt')
        return response


class SubdomainSecurityMiddleware:
    """
    Defense-in-depth: block admin paths on non-admin subdomains,
    block non-admin paths on admin subdomain.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        subdomain = getattr(request, 'subdomain', None)
        if not subdomain:
            host = request.get_host().split(':')[0].lower()
            subdomain, _ = resolve_site_role(host)
            request.subdomain = subdomain
        path = request.path

        # Block /admin/ access from shop or website subdomains
        if subdomain in ('shop', 'website') and path.startswith('/admin/'):
            raise Http404

        # On admin subdomain, only allow /admin/, /static/, /media/
        if subdomain == 'admin':
            allowed_prefixes = ('/admin/', '/static/', '/media/', '/_health/')
            if not any(path.startswith(p) for p in allowed_prefixes) and path != '/':
                raise Http404

        return self.get_response(request)


class ShopBrevementeMiddleware:
    """
    When the shop is in 'brevemente' mode (is_shop_brevemente=True),
    intercept all shop-subdomain requests and render the brevemente page.

    Health checks and payment callbacks are excluded so that essential
    infrastructure and incoming webhooks remain operational.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, 'subdomain', None) == 'shop':
            if self._is_brevemente_active():
                path = request.path
                if not path.startswith('/_health/') and not path.startswith('/api/payments/'):
                    return render(request, 'core/brevemente.html', status=200)

        return self.get_response(request)

    @staticmethod
    def _is_brevemente_active():
        from apps.core.models import ShopSettings

        settings_obj = ShopSettings.objects.filter(pk=1).only('is_shop_brevemente').first()
        if settings_obj is None:
            return False
        return bool(settings_obj.is_shop_brevemente)
