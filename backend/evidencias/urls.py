"""
@file urls.py
@brief URLs de la app de evidencias.
@details Define las rutas URL para los endpoints de evidencias
del sistema.
"""

from rest_framework.routers import DefaultRouter
from .views import EvidenciaViewSet

router = DefaultRouter()
router.register(r'evidencias', EvidenciaViewSet)
urlpatterns = router.urls
