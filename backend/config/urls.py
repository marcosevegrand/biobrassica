"""
Legacy URL configuration — kept as fallback for ROOT_URLCONF.
The SubdomainMiddleware overrides request.urlconf per subdomain:
  - biobrassica.pt → config.urls_website
  - loja.biobrassica.pt → config.urls_shop
  - admin.biobrassica.pt → config.urls_admin
"""
from config.urls_website import urlpatterns  # noqa: F401
