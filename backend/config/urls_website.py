from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import include, path

# Website: biobrassica.pt
# Brand site — company info, blog, recipes, contacts

urlpatterns = [
    path('_health/', include('apps.core.health_urls')),
]

urlpatterns += i18n_patterns(
    path('', include('apps.website.urls')),
    path('', include('apps.content.urls')),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
