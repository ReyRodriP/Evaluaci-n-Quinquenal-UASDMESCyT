"""
@file urls.py
@brief Configuración de rutas URL para la aplicación de organización.
@details Registra los ViewSets de Facultad, Departamento y PerfilUsuario
en el router de DRF, exponiendo los endpoints /facultades/,
/departamentos/ y /perfiles/.
"""

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
