"""
@file urls.py
@brief Configuración de rutas URL para la aplicación de organización.
@details Registra los ViewSets de Facultad, Departamento y PerfilUsuario
en el router de DRF, exponiendo los endpoints /facultades/,
/departamentos/ y /perfiles/.
"""

from rest_framework.routers import DefaultRouter

from .views import (
	DepartamentoViewSet,
	FacultadViewSet,
	PerfilUsuarioViewSet,
	TipoUnidadOrganizacionalViewSet,
	UnidadOrganizacionalViewSet,
)

router = DefaultRouter()

router.register(r"facultades", FacultadViewSet)
router.register(r"departamentos", DepartamentoViewSet)
router.register(r"perfiles", PerfilUsuarioViewSet)
router.register(r"tipos-unidad-organizacional", TipoUnidadOrganizacionalViewSet)
router.register(r"unidades-organizacionales", UnidadOrganizacionalViewSet)

urlpatterns = router.urls
