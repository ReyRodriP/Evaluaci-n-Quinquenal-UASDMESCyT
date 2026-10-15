"""@file urls.py
@brief Rutas del catalogo EQ-SIDACES (solo lectura).
@details Montadas en /api/catalogo/ desde evaluacionQuinquenal/urls.py.
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ComponenteViewSet,
    CriterioViewSet,
    DimensionViewSet,
    EstandarViewSet,
    ExportarArbolCSV,
    IndicadorViewSet,
    VersionMarcoEvaluacionViewSet,
)

router = DefaultRouter()

router.register(r"versiones", VersionMarcoEvaluacionViewSet)
router.register(r"dimensiones", DimensionViewSet)
router.register(r"componentes", ComponenteViewSet)
router.register(r"criterios", CriterioViewSet)
router.register(r"estandares", EstandarViewSet)
router.register(r"indicadores", IndicadorViewSet)

urlpatterns = [path("exportar/", ExportarArbolCSV.as_view())] + router.urls
