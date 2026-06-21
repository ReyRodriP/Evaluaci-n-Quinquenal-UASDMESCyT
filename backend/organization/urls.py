from rest_framework.routers import DefaultRouter
from .views import (
    FacultadViewSet,
    DepartamentoViewSet,
    PerfilUsuarioViewSet
)

router = DefaultRouter()

router.register(r'facultades', FacultadViewSet)
router.register(r'departamentos', DepartamentoViewSet)
router.register(r'perfiles', PerfilUsuarioViewSet)

urlpatterns = router.urls