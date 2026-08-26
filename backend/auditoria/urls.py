"""
@file urls.py
@brief URLs de la app de auditoría.
@details Define las rutas URL para los endpoints de auditoría
del sistema.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditoriaViewSet

router = DefaultRouter()
router.register(r"auditoria", AuditoriaViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
