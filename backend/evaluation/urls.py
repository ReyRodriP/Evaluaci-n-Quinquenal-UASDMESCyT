"""@file urls.py
@brief Configuración de rutas URL para el módulo de evaluación.
@details Registra los ViewSets del módulo de evaluación en el router de
Django REST Framework, exponiendo los endpoints para períodos, criterios,
indicadores y asignaciones.
"""

from rest_framework.routers import DefaultRouter
from .views import (
    PeriodoViewSet,
    CriterioViewSet,
    IndicadorViewSet,
    AsignacionViewSet
)

router = DefaultRouter()

router.register(r'periodos', PeriodoViewSet)
router.register(r'criterios', CriterioViewSet)
router.register(r'indicadores', IndicadorViewSet)
router.register(r'asignaciones', AsignacionViewSet)

urlpatterns = router.urls
