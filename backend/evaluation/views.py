"""@file views.py
@brief Vistas y ViewSets para el módulo de evaluación.
@details Define los ViewSets de Django REST Framework para gestionar períodos,
criterios, indicadores y asignaciones, incluyendo acciones personalizadas
para el flujo de revisión, aprobación y rechazo de evidencias.
"""

from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
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
from accounts.permissions import CustomModelPermissions, filtrar_por_rol, departamentos_permitidos
from auditoria.utils import registrar_auditoria
from notificaciones.utils import crear_notificacion
from organization.models import PerfilUsuario
from evidence.models import Evidencia, VersionEvidencia, Observacion

class PeriodoViewSet(viewsets.ModelViewSet):
    """@class PeriodoViewSet
    @brief ViewSet para gestionar períodos de evaluación.
    @details Proporciona operaciones CRUD completas para el modelo Periodo.
    Incluye registro de auditoría al eliminar un período.
    """
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
    """@class CriterioViewSet
    @brief ViewSet para gestionar criterios de evaluación.
    @details Proporciona operaciones CRUD completas para el modelo Criterio.
    Incluye registro de auditoría al eliminar un criterio.
    """
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
    """@class IndicadorViewSet
    @brief ViewSet para gestionar indicadores de evaluación.
    @details Proporciona operaciones CRUD completas para el modelo Indicador.
    Incluye registro de auditoría al eliminar un indicador.
    """
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
    """@class AsignacionViewSet
    @brief ViewSet para gestionar asignaciones de indicadores a departamentos.
    @details Proporciona operaciones CRUD y acciones personalizadas para el flujo
    de trabajo de evaluación: envío a revisión, aprobación, rechazo y observaciones.
    Filtra el queryset según el rol del usuario autenticado.
    """
    authentication_classes = [TokenAuthentication]
    queryset = Asignacion.objects.all().order_by('periodo', 'departamento')
    serializer_class = AsignacionSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        qs = Asignacion.objects.all().order_by('periodo', 'departamento')
        return filtrar_por_rol(qs, self.request, dept_field='departamento')

    def _notificar_departamento(self, departamento, titulo, mensaje):
        """@brief Envía una notificación a todos los usuarios del departamento.
        @param departamento Instancia del departamento a notificar.
        @param titulo Título de la notificación.
        @param mensaje Mensaje descriptivo de la notificación.
        @return None
        """
        perfiles = PerfilUsuario.objects.filter(departamento=departamento)
        for perfil in perfiles:
            crear_notificacion(
                usuario=perfil.usuario,
                titulo=titulo,
                mensaje=mensaje
            )

    def _notificar_subido_por(self, instance, titulo, mensaje):
        """@brief Envía una notificación al usuario que subió la evidencia.
        @param instance Instancia de la asignación asociada.
        @param titulo Título de la notificación.
        @param mensaje Mensaje descriptivo de la notificación.
        @return None
        """
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
        """@brief Crea un registro en el historial de estados.
        @param asignacion Instancia de la asignación.
        @param estado_anterior Estado previo de la asignación.
        @param estado_nuevo Estado nuevo de la asignación.
        @param usuario Usuario que realizó el cambio de estado.
        @param comentario Comentario opcional sobre el cambio.
        @return Instancia del HistorialEstado creado.
        """
        return HistorialEstado.objects.create(
            asignacion=asignacion,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario=usuario,
            comentario=comentario
        )

    def _crear_observacion(self, asignacion, usuario, comentario):
        """@brief Crea una observación en la última versión de la evidencia.
        @param asignacion Instancia de la asignación.
        @param usuario Usuario que realiza la observación.
        @param comentario Texto de la observación.
        @return None
        """
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
        """@brief Valida si una transición de estado es permitida.
        @param estado_actual Estado actual de la asignación.
        @param estado_nuevo Estado al que se desea transicionar.
        @return True si la transición es válida, False de lo contrario.
        """
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
        """@brief Obtiene un resumen detallado de una asignación.
        @param request Objeto de solicitud HTTP.
        @param pk Identificador de la asignación.
        @return Response con los datos del resumen incluyendo evidencia e historial reciente.
        """
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
        """@brief Envía una asignación a estado de revisión.
        @param request Objeto de solicitud HTTP.
        @param pk Identificador de la asignación.
        @return Response con el nuevo estado de la asignación.
        @raises ValidationError Si la transición de estado no es válida.
        """
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
        """@brief Aprueba la evidencia de una asignación.
        @param request Objeto de solicitud HTTP.
        @param pk Identificador de la asignación.
        @return Response con el nuevo estado de la asignación.
        @raises ValidationError Si la transición de estado no es válida.
        """
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
        """@brief Rechaza la evidencia de una asignación.
        @param request Objeto de solicitud HTTP.
        @param pk Identificador de la asignación.
        @return Response con el nuevo estado de la asignación.
        @raises ValidationError Si la transición de estado no es válida.
        """
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
        """@brief Marca una asignación como observada, solicitando cambios.
        @param request Objeto de solicitud HTTP.
        @param pk Identificador de la asignación.
        @return Response con el nuevo estado de la asignación.
        @raises ValidationError Si la transición de estado no es válida.
        """
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

    def _validar_departamento_permitido(self, validated_data):
        """@brief Valida que el departamento indicado esté permitido para el usuario.
        @param validated_data Datos validados del serializador.
        @return None
        @raises ValidationError Si el departamento no está permitido.
        """
        departamento = validated_data.get('departamento')
        if not departamento:
            return
        permitidos = departamentos_permitidos(self.request)
        if permitidos is not None and departamento.pk not in permitidos:
            raise ValidationError({
                'departamento': 'No tiene permiso para asignar indicadores a este departamento.'
            })

    def perform_create(self, serializer):
        """@brief Crea una nueva asignación validando el departamento permitido.
        @param serializer Serializador con los datos validados.
        @return None
        """
        self._validar_departamento_permitido(serializer.validated_data)
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
        """@brief Actualiza una asignación, registrando cambios de estado.
        @param serializer Serializador con los datos validados.
        @return None
        """
        self._validar_departamento_permitido(serializer.validated_data)
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
        """@brief Elimina una asignación y registra la acción en auditoría.
        @param instance Instancia de la asignación a eliminar.
        @return None
        """
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
