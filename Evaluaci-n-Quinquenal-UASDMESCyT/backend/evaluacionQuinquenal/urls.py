from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('dashboard.urls')),
    path('api/', include('search.urls')),
    path('api/', include('organization.urls')),
    path('api/', include('evaluation.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('auditoria.urls')),
    path('api/', include('notificaciones.urls')),
    path('api/', include('evidence.urls')),
    path('api/', include('evidencias.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
