from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import include, path

# Shop: loja.marcosevegrand.com
# E-commerce — products, cart, checkout, payments, accounts

# Non-i18n URLs (webhooks)
urlpatterns = [
    path('api/payments/callback/', include('apps.payments.callback_urls')),
    path('_health/', include('apps.core.health_urls')),
]

# i18n URLs (prefixed with /pt/, /en/, /fr/)
urlpatterns += i18n_patterns(
    path('', include('apps.catalog.urls')),
    path('carrinho/', include('apps.cart.urls')),
    path('checkout/', include('apps.orders.urls')),
    path('conta/', include('apps.accounts.urls')),
    path('', include('apps.website.urls_legal')),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
