"""
@file urls.py
@brief URLs principales del proyecto Evaluación Quinquenal.
@details Define las rutas URL raíz del proyecto, incluyendo
las URLs de todas las aplicaciones del sistema y el admin.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),  # Proteger en produccion con staff_member_required (ver settings.py)
    path("api/", include("dashboard.urls")),
    path("api/", include("search.urls")),
    path("api/", include("organization.urls")),
    path("api/", include("evaluation.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("auditoria.urls")),
    path("api/", include("notificaciones.urls")),
    path("api/", include("evidence.urls")),
    path("api/", include("evidencias.urls")),
    path("api/", include("reportes.urls")),
    path("api-auth/", include("rest_framework.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
