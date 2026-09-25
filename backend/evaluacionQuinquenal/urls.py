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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    path("admin/", admin.site.urls),  # Proteger en produccion con staff_member_required (ver settings.py)
    path("", include("health.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
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
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
