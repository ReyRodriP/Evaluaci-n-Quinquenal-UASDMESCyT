from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Periodo, Criterio, Indicador, Asignacion, EstadoAsignacion
from .serializers import (
    PeriodoSerializer,
    CriterioSerializer,
    IndicadorSerializer,
    AsignacionSerializer
)
from accounts.permissions import CustomModelPermissions
from auditoria.utils import registrar_auditoria
from notificaciones.utils import crear_notificacion
from organization.models import PerfilUsuario


class PeriodoViewSet(viewsets.ModelViewSet):
    queryset = Periodo.objects.all().order_by('-fecha_inicio')
    serializer_class = PeriodoSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def perform_destroy(self, instance):
        registrar_auditoria(
            usuario=self.request.user,
            accion="Eliminar registro",
            modelo="Periodo",
            registro_id=instance.pk,
            descripcion=f"Se eliminó el período '{instance.nombre}'"
        )
        instance.delete()


class CriterioViewSet(viewsets.ModelViewSet):
    queryset = Criterio.objects.all().order_by('nombre')
    serializer_class = CriterioSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def perform_destroy(self, instance):
        registrar_auditoria(
            usuario=self.request.user,
            accion="Eliminar registro",
            modelo="Criterio",
            registro_id=instance.pk,
            descripcion=f"Se eliminó el criterio '{instance.nombre}'"
        )
        instance.delete()


class IndicadorViewSet(viewsets.ModelViewSet):
    queryset = Indicador.objects.all().order_by('nombre')
    serializer_class = IndicadorSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def perform_destroy(self, instance):
        registrar_auditoria(
            usuario=self.request.user,
            accion="Eliminar registro",
            modelo="Indicador",
            registro_id=instance.pk,
            descripcion=f"Se eliminó el indicador '{instance.nombre}'"
        )
        instance.delete()


class AsignacionViewSet(viewsets.ModelViewSet):
    queryset = Asignacion.objects.all().order_by('periodo', 'departamento')
    serializer_class = AsignacionSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def _notificar_departamento(self, departamento, titulo, mensaje):
        perfiles = PerfilUsuario.objects.filter(departamento=departamento)
        for perfil in perfiles:
            crear_notificacion(
                usuario=perfil.usuario,
                titulo=titulo,
                mensaje=mensaje
            )

    def perform_create(self, serializer):
        instance = serializer.save()
        registrar_auditoria(
            usuario=self.request.user,
            accion="Crear asignación",
            modelo="Asignacion",
            registro_id=instance.pk,
            descripcion=(
                f"Se asignó el indicador '{instance.indicador.nombre}' "
                f"al departamento '{instance.departamento.nombre}' "
                f"en el período '{instance.periodo.nombre}'"
            )
        )
        self._notificar_departamento(
            departamento=instance.departamento,
            titulo="Nuevo indicador asignado",
            mensaje=f"Se te ha asignado el indicador '{instance.indicador.nombre}' en el período {instance.periodo.nombre}"
        )

    def perform_update(self, serializer):
        old_estado = self.get_object().estado
        instance = serializer.save()

        if old_estado != instance.estado:
            registrar_auditoria(
                usuario=self.request.user,
                accion="Cambiar estado",
                modelo="Asignacion",
                registro_id=instance.pk,
                descripcion=(
                    f"La asignación '{instance.indicador.nombre}' cambió de "
                    f"'{old_estado}' a '{instance.estado}'"
                )
            )
            estado_choices = {k: v for k, v in EstadoAsignacion.choices}
            self._notificar_departamento(
                departamento=instance.departamento,
                titulo=f"Estado actualizado: {instance.get_estado_display()}",
                mensaje=(
                    f"La asignación '{instance.indicador.nombre}' cambió de "
                    f"'{estado_choices.get(old_estado, old_estado)}' "
                    f"a '{instance.get_estado_display()}'"
                )
            )

    def perform_destroy(self, instance):
        registrar_auditoria(
            usuario=self.request.user,
            accion="Eliminar registro",
            modelo="Asignacion",
            registro_id=instance.pk,
            descripcion=(
                f"Se eliminó la asignación del indicador '{instance.indicador.nombre}' "
                f"del departamento '{instance.departamento.nombre}'"
            )
        )
        instance.delete()
