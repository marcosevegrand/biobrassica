from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.core.admin_views import calendario_view

# Admin: admin.marcosevegrand.com
# Django admin dashboard — manage everything

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('admin/operacoes/calendario/', admin.site.admin_view(calendario_view), name='operacoes_calendario'),
    path('admin/', admin.site.urls),
    path('_health/', include('apps.core.health_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
