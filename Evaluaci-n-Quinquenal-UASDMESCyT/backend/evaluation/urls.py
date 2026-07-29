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
