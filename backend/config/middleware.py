from django.http import Http404
from django.utils import translation


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
        request.subdomain = None

        if host.startswith('loja.'):
            request.urlconf = 'config.urls_shop'
            request.subdomain = 'shop'
        elif host.startswith('admin.'):
            request.urlconf = 'config.urls_admin'
            request.subdomain = 'admin'
        else:
            request.urlconf = 'config.urls_website'
            request.subdomain = 'website'

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
