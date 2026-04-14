"""
Legacy URL configuration — kept as fallback for ROOT_URLCONF.
The SubdomainMiddleware overrides request.urlconf per subdomain:
  - marcosevegrand.com → config.urls_website
  - loja.marcosevegrand.com → config.urls_shop
  - admin.marcosevegrand.com → config.urls_admin
"""
from config.urls_website import urlpatterns  # noqa: F401
