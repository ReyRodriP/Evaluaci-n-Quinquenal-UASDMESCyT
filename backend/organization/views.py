"""
@file views.py
@brief Vistas API para la gestión de la organización.
@details Define los ViewSets que exponen los endpoints REST para
Facultad, Departamento y PerfilUsuario, incluyendo permisos
personalizados y registro de auditoría.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import (
    CustomModelPermissions,
    _grupos_usuario,
    departamentos_permitidos,
    facultades_permitidas,
)
from accounts.permissions import unidades_organizacionales_permitidas
from auditoria.utils import registrar_auditoria

from .models import AmbitoEvaluacion, Departamento, Facultad, PerfilUsuario, TipoUnidadOrganizacional, UnidadOrganizacional
from .serializers import (
    AmbitoEvaluacionSerializer,
    DepartamentoSerializer,
    FacultadSerializer,
    PerfilUsuarioSerializer,
    TipoUnidadOrganizacionalSerializer,
    UnidadOrganizacionalSerializer,
)


def _asegurar_unidad_departamento(departamento):
    tipo_universidad, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Universidad")
    tipo_facultad, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Facultad")
    tipo_departamento, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Departamento")
    universidad, _ = UnidadOrganizacional.objects.get_or_create(
        nombre="UASD",
        tipo=tipo_universidad,
        unidad_padre=None,
    )
    facultad, _ = UnidadOrganizacional.objects.get_or_create(
        nombre=departamento.facultad.nombre,
        tipo=tipo_facultad,
        unidad_padre=universidad,
        defaults={"activa": departamento.facultad.activo},
    )
    UnidadOrganizacional.objects.update_or_create(
        departamento_legacy=departamento,
        defaults={
            "nombre": departamento.nombre,
            "descripcion": departamento.descripcion,
            "tipo": tipo_departamento,
            "unidad_padre": facultad,
            "activa": departamento.activo,
        },
    )


class TipoUnidadOrganizacionalViewSet(viewsets.ModelViewSet):
    queryset = TipoUnidadOrganizacional.objects.all().order_by("nombre")
    serializer_class = TipoUnidadOrganizacionalSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        activo = self.request.query_params.get("activo")
        if activo in {"true", "false"}:
            queryset = queryset.filter(activo=activo == "true")
        return queryset


class UnidadOrganizacionalViewSet(viewsets.ModelViewSet):
    queryset = UnidadOrganizacional.objects.select_related("tipo", "unidad_padre").order_by("nombre")
    serializer_class = UnidadOrganizacionalSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        permitidas = unidades_organizacionales_permitidas(self.request)
        if permitidas is not None:
            queryset = queryset.filter(pk__in=permitidas)
        tipo = self.request.query_params.get("tipo")
        unidad_padre = self.request.query_params.get("unidad_padre")
        activa = self.request.query_params.get("activa")
        buscar = self.request.query_params.get("buscar", "").strip()

        if tipo:
            queryset = queryset.filter(tipo_id=tipo)
        if unidad_padre in {"null", "root"}:
            queryset = queryset.filter(unidad_padre__isnull=True)
        elif unidad_padre:
            queryset = queryset.filter(unidad_padre_id=unidad_padre)
        if activa in {"true", "false"}:
            queryset = queryset.filter(activa=activa == "true")
        if buscar:
            queryset = queryset.filter(nombre__icontains=buscar)
        return queryset


class FacultadViewSet(viewsets.ModelViewSet):
    """@class FacultadViewSet
    @brief ViewSet para el CRUD de facultades.
    @details Proporciona operaciones de listado, creación, actualización y
    eliminación de facultades. Filtra el queryset según las facultades
    permitidas para el usuario autenticado y registra auditoría al eliminar.
    """

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

    def perform_create(self, serializer):
        departamento = serializer.save()
        _asegurar_unidad_departamento(departamento)

    def perform_update(self, serializer):
        departamento = serializer.save()
        _asegurar_unidad_departamento(departamento)

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

    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        """@brief Obtiene el queryset filtrado por departamento si se especifica.
        @return QuerySet de PerfilUsuario, opcionalmente filtrado por departamento.
        """
        queryset = PerfilUsuario.objects.all().order_by("usuario__username")

        if "Evaluador Externo" in _grupos_usuario(self.request.user):
            queryset = queryset.filter(usuario=self.request.user)

        unidad_id = self.request.query_params.get("unidad_organizacional")
        departamento_id = self.request.query_params.get("departamento")

        if unidad_id:
            queryset = queryset.filter(unidad_organizacional_id=unidad_id)
        elif departamento_id:
            queryset = queryset.filter(unidad_organizacional__departamento_legacy_id=departamento_id)

        return queryset


class AmbitoEvaluacionViewSet(viewsets.ModelViewSet):
    queryset = AmbitoEvaluacion.objects.select_related(
        "usuario", "unidad_organizacional", "periodo"
    ).all()
    serializer_class = AmbitoEvaluacionSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        for parameter, field in (
            ("usuario", "usuario_id"),
            ("unidad_organizacional", "unidad_organizacional_id"),
            ("periodo", "periodo_id"),
        ):
            value = self.request.query_params.get(parameter)
            if value:
                queryset = queryset.filter(**{field: value})
        activo = self.request.query_params.get("activo")
        if activo in ("true", "false"):
            queryset = queryset.filter(activo=activo == "true")
        return queryset

    def perform_create(self, serializer):
        ambito = serializer.save()
        registrar_auditoria(
            usuario=self.request.user,
            accion="Asignar ámbito de evaluación",
            modelo="AmbitoEvaluacion",
            registro_id=ambito.pk,
            descripcion=(
                f"Se autorizó a '{ambito.usuario.username}' a evaluar "
                f"'{ambito.unidad_organizacional.nombre}' en '{ambito.periodo.nombre}'."
            ),
        )

    def perform_update(self, serializer):
        ambito_actual = serializer.instance
        cambios = {
            campo: (getattr(ambito_actual, campo), valor)
            for campo, valor in serializer.validated_data.items()
            if getattr(ambito_actual, campo) != valor
        }
        ambito = serializer.save()
        if cambios:
            detalle = "; ".join(f"{campo}: {anterior} -> {nuevo}" for campo, (anterior, nuevo) in cambios.items())
            registrar_auditoria(
                usuario=self.request.user,
                accion="Actualizar ámbito de evaluación",
                modelo="AmbitoEvaluacion",
                registro_id=ambito.pk,
                descripcion=f"Se actualizó el ámbito de '{ambito.usuario.username}'. Cambios: {detalle}.",
            )

    def perform_destroy(self, instance):
        if instance.activo:
            instance.activo = False
            instance.save(update_fields=["activo"])
            registrar_auditoria(
                usuario=self.request.user,
                accion="Desactivar ámbito de evaluación",
                modelo="AmbitoEvaluacion",
                registro_id=instance.pk,
                descripcion=(
                    f"Se desactivó el ámbito de '{instance.usuario.username}' para "
                    f"'{instance.unidad_organizacional.nombre}' en '{instance.periodo.nombre}'."
                ),
            )
