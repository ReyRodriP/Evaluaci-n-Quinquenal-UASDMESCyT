from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import Periodo, Criterio, Indicador, Asignacion, EstadoAsignacion, HistorialEstado
from .serializers import (
    PeriodoSerializer,
    CriterioSerializer,
    IndicadorSerializer,
    AsignacionSerializer,
    HistorialEstadoSerializer
)
from accounts.permissions import CustomModelPermissions
from auditoria.utils import registrar_auditoria
from notificaciones.utils import crear_notificacion
from organization.models import PerfilUsuario
from evidence.models import Evidencia, VersionEvidencia, Observacion

class PeriodoViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
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
    authentication_classes = [TokenAuthentication]
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
    authentication_classes = [TokenAuthentication]
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
    authentication_classes = [TokenAuthentication]
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

    def _notificar_subido_por(self, instance, titulo, mensaje):
        try:
            evidencia = instance.evidencia
            if evidencia and hasattr(evidencia, 'subido_por') and evidencia.subido_por:
                crear_notificacion(
                    usuario=evidencia.subido_por,
                    titulo=titulo,
                    mensaje=mensaje
                )
        except Evidencia.DoesNotExist:
            pass

    def _crear_historial(self, asignacion, estado_anterior, estado_nuevo, usuario, comentario=""):
        return HistorialEstado.objects.create(
            asignacion=asignacion,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario=usuario,
            comentario=comentario
        )

    def _crear_observacion(self, asignacion, usuario, comentario):
        if not comentario:
            return
        try:
            evidencia = asignacion.evidencia
            ultima_version = evidencia.versiones.order_by("-version").first()
            if ultima_version:
                Observacion.objects.create(
                    version=ultima_version,
                    usuario=usuario,
                    comentario=comentario
                )
        except Evidencia.DoesNotExist:
            pass

    def _validar_transicion(self, estado_actual, estado_nuevo):
        transiciones_validas = {
            EstadoAsignacion.PENDIENTE: [EstadoAsignacion.EN_PROGRESO, EstadoAsignacion.OBSERVADA],
            EstadoAsignacion.EN_PROGRESO: [EstadoAsignacion.APROBADO, EstadoAsignacion.RECHAZADO, EstadoAsignacion.OBSERVADA],
            EstadoAsignacion.OBSERVADA: [EstadoAsignacion.EN_PROGRESO, EstadoAsignacion.RECHAZADO],
            EstadoAsignacion.RECHAZADO: [EstadoAsignacion.EN_PROGRESO],
            EstadoAsignacion.APROBADO: [],
            EstadoAsignacion.COMPLETADO: [],
        }
        return estado_nuevo in transiciones_validas.get(estado_actual, [])

    @action(detail=True, methods=["get"])
    def resumen(self, request, pk=None):
        asignacion = self.get_object()
        data = self.get_serializer(asignacion).data
        try:
            evidencia = asignacion.evidencia
            data["total_evidencias"] = 1
            ultima_version = evidencia.versiones.order_by("-fecha_subida").first()
            data["ultima_actualizacion"] = ultima_version.fecha_subida if ultima_version else None
        except Evidencia.DoesNotExist:
            data["total_evidencias"] = 0
            data["ultima_actualizacion"] = None
        historial = asignacion.historial_estados.all()[:10]
        data["historial_reciente"] = HistorialEstadoSerializer(historial, many=True).data
        return Response(data)

    @action(detail=True, methods=["post"])
    def en_revision(self, request, pk=None):
        asignacion = self.get_object()
        if not self._validar_transicion(asignacion.estado, EstadoAsignacion.EN_PROGRESO):
            return Response({"error": "Transición no válida"}, status=status.HTTP_400_BAD_REQUEST)
        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.EN_PROGRESO
        asignacion.save()
        self._crear_historial(asignacion, estado_anterior, EstadoAsignacion.EN_PROGRESO, request.user)
        registrar_auditoria(
            usuario=request.user,
            accion="Enviar a revisión",
            modelo="Asignacion",
            registro_id=asignacion.pk,
            descripcion=f"La asignación '{asignacion.indicador.nombre}' fue enviada a revisión"
        )
        return Response({"estado": EstadoAsignacion.EN_PROGRESO})

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        asignacion = self.get_object()
        if not self._validar_transicion(asignacion.estado, EstadoAsignacion.APROBADO):
            return Response({"error": "Transición no válida"}, status=status.HTTP_400_BAD_REQUEST)
        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.APROBADO
        asignacion.save()
        comentario = request.data.get("comentario", "")
        self._crear_historial(asignacion, estado_anterior, EstadoAsignacion.APROBADO, request.user, comentario)
        self._crear_observacion(asignacion, request.user, comentario)
        registrar_auditoria(
            usuario=request.user,
            accion="Aprobar evidencia",
            modelo="Asignacion",
            registro_id=asignacion.pk,
            descripcion=f"La evidencia para '{asignacion.indicador.nombre}' fue aprobada"
        )
        self._notificar_subido_por(
            instance=asignacion,
            titulo="Evidencia aprobada",
            mensaje=f"Tu evidencia para '{asignacion.indicador.nombre}' ha sido aprobada."
        )
        if comentario:
            self._notificar_departamento(
                departamento=asignacion.departamento,
                titulo="Evidencia aprobada con comentarios",
                mensaje=f"Tu evidencia para '{asignacion.indicador.nombre}' fue aprobada. Comentario: {comentario}"
            )
        return Response({"estado": EstadoAsignacion.APROBADO})

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        asignacion = self.get_object()
        if not self._validar_transicion(asignacion.estado, EstadoAsignacion.RECHAZADO):
            return Response({"error": "Transición no válida"}, status=status.HTTP_400_BAD_REQUEST)
        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.RECHAZADO
        asignacion.save()
        comentario = request.data.get("comentario", "")
        self._crear_historial(asignacion, estado_anterior, EstadoAsignacion.RECHAZADO, request.user, comentario)
        self._crear_observacion(asignacion, request.user, comentario)
        registrar_auditoria(
            usuario=request.user,
            accion="Rechazar evidencia",
            modelo="Asignacion",
            registro_id=asignacion.pk,
            descripcion=f"La evidencia para '{asignacion.indicador.nombre}' fue rechazada. Motivo: {comentario}"
        )
        self._notificar_subido_por(
            instance=asignacion,
            titulo="Evidencia rechazada",
            mensaje=f"Tu evidencia para '{asignacion.indicador.nombre}' ha sido rechazada. Motivo: {comentario}"
        )
        return Response({"estado": EstadoAsignacion.RECHAZADO})

    @action(detail=True, methods=["post"])
    def observada(self, request, pk=None):
        asignacion = self.get_object()
        if not self._validar_transicion(asignacion.estado, EstadoAsignacion.OBSERVADA):
            return Response({"error": "Transición no válida"}, status=status.HTTP_400_BAD_REQUEST)
        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.OBSERVADA
        asignacion.save()
        comentario = request.data.get("comentario", "")
        self._crear_historial(asignacion, estado_anterior, EstadoAsignacion.OBSERVADA, request.user, comentario)
        self._crear_observacion(asignacion, request.user, comentario)
        registrar_auditoria(
            usuario=request.user,
            accion="Solicitar cambios",
            modelo="Asignacion",
            registro_id=asignacion.pk,
            descripcion=f"Se solicitaron cambios para '{asignacion.indicador.nombre}'. Observación: {comentario}"
        )
        self._notificar_subido_por(
            instance=asignacion,
            titulo="Cambios solicitados",
            mensaje=f"Se solicitaron cambios para tu evidencia '{asignacion.indicador.nombre}'. Observación: {comentario}"
        )
        return Response({"estado": EstadoAsignacion.OBSERVADA})

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
            self._crear_historial(instance, old_estado, instance.estado, self.request.user)
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
            if instance.estado == EstadoAsignacion.APROBADO:
                self._notificar_subido_por(
                    instance=instance,
                    titulo="Evidencia aprobada",
                    mensaje=(
                        f"Tu evidencia para el indicador '{instance.indicador.nombre}' "
                        f"ha sido aprobada"
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
