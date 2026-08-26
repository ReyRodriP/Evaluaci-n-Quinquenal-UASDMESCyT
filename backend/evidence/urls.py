"""@file urls.py
@brief Configuración de rutas URL para la app de evidencias
@details Define las rutas REST API utilizando un router de DRF para
los viewsets de Evidencia, Versión de Evidencia y Observación."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EvidenciaViewSet,
    VersionEvidenciaViewSet,
    ObservacionViewSet
)

router = DefaultRouter()
router.register(r'evidencias', EvidenciaViewSet)
router.register(r'versiones', VersionEvidenciaViewSet)
router.register(r'observaciones', ObservacionViewSet, basename='observaciones')

urlpatterns = [
    path('', include(router.urls)),
]
