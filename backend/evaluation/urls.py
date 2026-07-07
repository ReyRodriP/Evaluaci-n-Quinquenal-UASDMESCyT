from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    PeriodoViewSet,
    CriterioViewSet,
    IndicadorViewSet,
    AsignacionViewSet,
    dashboard_resumen,
    dashboard_departamento,
    dashboard_periodo,
    dashboard_avance,
    search_view,
)

router = DefaultRouter()

router.register(r'periodos', PeriodoViewSet)
router.register(r'criterios', CriterioViewSet)
router.register(r'indicadores', IndicadorViewSet)
router.register(r'asignaciones', AsignacionViewSet)

urlpatterns = [
    path('dashboard/resumen/', dashboard_resumen, name='dashboard-resumen'),
    path('dashboard/departamento/<int:departamento_id>/', dashboard_departamento, name='dashboard-departamento'),
    path('dashboard/periodo/', dashboard_periodo, name='dashboard-periodo'),
    path('dashboard/avance/', dashboard_avance, name='dashboard-avance'),
    path('search/', search_view, name='search'),
] + router.urls
