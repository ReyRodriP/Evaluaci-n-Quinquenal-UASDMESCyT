"""
@file views.py
@brief Vistas API para la gestión de la organización.
@details Define los ViewSets que exponen los endpoints REST para
Facultad, Departamento y PerfilUsuario, incluyendo permisos
personalizados y registro de auditoría.
"""

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CustomModelPermissions, departamentos_permitidos, facultades_permitidas
from auditoria.utils import registrar_auditoria

from .models import Departamento, Facultad, PerfilUsuario
from .serializers import DepartamentoSerializer, FacultadSerializer, PerfilUsuarioSerializer


class FacultadViewSet(viewsets.ModelViewSet):
    """@class FacultadViewSet
    @brief ViewSet para el CRUD de facultades.
    @details Proporciona operaciones de listado, creación, actualización y
    eliminación de facultades. Filtra el queryset según las facultades
    permitidas para el usuario autenticado y registra auditoría al eliminar.
    """

    authentication_classes = [TokenAuthentication]
    queryset = Facultad.objects.all().order_by("nombre")
    serializer_class = FacultadSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        """@brief Obtiene el queryset filtrado por facultades permitidas.
        @return QuerySet de Facultad filtrado según permisos del usuario.
        """
        queryset = Facultad.objects.all().order_by("nombre")
        permitidas = facultades_permitidas(self.request)
        if permitidas is not None:
            queryset = queryset.filter(pk__in=permitidas)
        return queryset

    def perform_destroy(self, instance):
        """@brief Elimina una facultad registrando la acción en auditoría.
        @param instance Instancia de Facultad a eliminar.
        """
        registrar_auditoria(
            usuario=self.request.user,
            accion="Eliminar registro",
            modelo="Facultad",
            registro_id=instance.pk,
            descripcion=f"Se eliminó la facultad '{instance.nombre}'",
        )
        instance.delete()


class DepartamentoViewSet(viewsets.ModelViewSet):
    """@class DepartamentoViewSet
    @brief ViewSet para el CRUD de departamentos.
    @details Proporciona operaciones de listado, creación, actualización y
    eliminación de departamentos. Filtra el queryset según los departamentos
    permitidos para el usuario autenticado y registra auditoría al eliminar.
    """

    authentication_classes = [TokenAuthentication]
    queryset = Departamento.objects.all().order_by("nombre")
    serializer_class = DepartamentoSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        """@brief Obtiene el queryset filtrado por departamentos permitidos.
        @return QuerySet de Departamento filtrado según permisos del usuario.
        """
        queryset = Departamento.objects.all().order_by("nombre")
        permitidos = departamentos_permitidos(self.request)
        if permitidos is not None:
            queryset = queryset.filter(pk__in=permitidos)
        return queryset

    def perform_destroy(self, instance):
        """@brief Elimina un departamento registrando la acción en auditoría.
        @param instance Instancia de Departamento a eliminar.
        """
        registrar_auditoria(
            usuario=self.request.user,
            accion="Eliminar registro",
            modelo="Departamento",
            registro_id=instance.pk,
            descripcion=f"Se eliminó el departamento '{instance.nombre}'",
        )
        instance.delete()


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    """@class PerfilUsuarioViewSet
    @brief ViewSet para el CRUD de perfiles de usuario.
    @details Proporciona operaciones de listado, creación, actualización y
    eliminación de perfiles de usuario. Permite filtrar por departamento
    mediante el parámetro de consulta 'departamento'.
    """

    authentication_classes = [TokenAuthentication]
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        """@brief Obtiene el queryset filtrado por departamento si se especifica.
        @return QuerySet de PerfilUsuario, opcionalmente filtrado por departamento.
        """
        queryset = PerfilUsuario.objects.all().order_by("usuario__username")

        departamento_id = self.request.query_params.get("departamento")

        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)

        return queryset
