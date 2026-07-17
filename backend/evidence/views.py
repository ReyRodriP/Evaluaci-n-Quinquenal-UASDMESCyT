from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.http import FileResponse
from django.db.models import Max

from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CustomModelPermissions
from auditoria.utils import registrar_auditoria
from notificaciones.utils import crear_notificacion

from evaluation.models import Asignacion, EstadoAsignacion, HistorialEstado

from .models import Evidencia, VersionEvidencia, Observacion
from .serializers import (
    EvidenciaSerializer,
    VersionEvidenciaSerializer,
    ObservacionSerializer
)

import os

# CRUD de Evidencias
class EvidenciaViewSet(viewsets.ModelViewSet):
    permission_classes = [
    IsAuthenticated,
    CustomModelPermissions
    ]
    queryset = Evidencia.objects.all()
    serializer_class = EvidenciaSerializer

    def create(self, request, *args, **kwargs):
        asignacion_id = request.data.get("asignacion")
        if asignacion_id:
            existing = Evidencia.objects.filter(asignacion_id=asignacion_id).first()
            if existing:
                if existing.estado == "cancelada":
                    existing.estado = "activa"
                    existing.save()
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def subir_version(self, request, pk=None):
        evidencia = self.get_object()

        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response(
                {"error": "Debe adjuntar un archivo"},
                status=status.HTTP_400_BAD_REQUEST
            )

        comentario = request.data.get("comentario", "")

        if evidencia.estado == "cancelada":
            evidencia.estado = "activa"
            evidencia.save()

        ultima_version = evidencia.versiones.aggregate(
            max_version=Max("version")
        )["max_version"] or 0
        nueva_version_num = ultima_version + 1

        version = VersionEvidencia.objects.create(
            evidencia=evidencia,
            archivo=archivo,
            version=nueva_version_num,
            comentario=comentario
        )

        asignacion = evidencia.asignacion
        if asignacion.estado in [
            EstadoAsignacion.PENDIENTE,
            EstadoAsignacion.OBSERVADA,
            EstadoAsignacion.RECHAZADO
        ]:
            estado_anterior = asignacion.estado
            asignacion.estado = EstadoAsignacion.EN_PROGRESO
            asignacion.save()
            HistorialEstado.objects.create(
                asignacion=asignacion,
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoAsignacion.EN_PROGRESO,
                usuario=request.user,
                comentario=f"Nueva versión subida: {comentario or 'Sin comentario'}"
            )

        return Response(
            VersionEvidenciaSerializer(version).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["get"])
    def detalle(self, request, pk=None):
        evidencia = self.get_object()
        try:
            asignacion = evidencia.asignacion
        except:
            asignacion = None

        data = EvidenciaSerializer(evidencia, context={"request": request}).data
        if asignacion:
            from evaluation.serializers import AsignacionSerializer, HistorialEstadoSerializer
            data["asignacion_info"] = AsignacionSerializer(asignacion).data
            historial = asignacion.historial_estados.all().order_by("-fecha")[:20]
            data["historial_estados"] = HistorialEstadoSerializer(historial, many=True).data

        data["puede_observar"] = request.user.has_perm("evidence.add_observacion")
        data["puede_subir_version"] = request.user.has_perm("evidence.add_versionevidencia") or request.user.has_perm("evidence.add_evidencia")
        data["puede_cambiar_estado"] = request.user.has_perm("evaluation.change_asignacion")

        return Response(data)

    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        evidencia = self.get_object()
        versiones = evidencia.versiones.order_by("-version")

        return Response(
            VersionEvidenciaSerializer(versiones, many=True).data
        )
# CRUD de Versiones
class VersionEvidenciaViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [
        IsAuthenticated,
        CustomModelPermissions
    ]
    queryset = VersionEvidencia.objects.all()
    serializer_class = VersionEvidenciaSerializer

    @action(detail=True, methods=["get"])
    def descargar(self, request, pk=None):
        version = self.get_object()

        return FileResponse(
            version.archivo.open(),
            as_attachment=True,
            filename=version.archivo.name.split("/")[-1]
        )

    @action(detail=True, methods=["get"])
    def observaciones(self, request, pk=None):
        version = self.get_object()

        return Response(
            ObservacionSerializer(
                version.observaciones.all(),
                many=True
            ).data
        )

# CRUD de Observaciones
class ObservacionViewSet(viewsets.ModelViewSet):
    queryset = Observacion.objects.filter(activo=True)
    serializer_class = ObservacionSerializer

    permission_classes = [
        IsAuthenticated,
        CustomModelPermissions
    ]

    def perform_create(self, serializer):
        observacion = serializer.save(usuario=self.request.user)

        evidencia = observacion.version.evidencia
        asignacion = evidencia.asignacion

        registrar_auditoria(
            usuario=self.request.user,
            accion="Crear observación",
            modelo="Observacion",
            registro_id=observacion.pk,
            descripcion=(
                f"Se creó una observación sobre la evidencia '{evidencia.titulo}' "
                f"(versión {observacion.version.version}): {observacion.comentario}"
            )
        )

        if hasattr(evidencia, 'subido_por') and evidencia.subido_por:
            crear_notificacion(
                usuario=evidencia.subido_por,
                titulo="Evidencia observada",
                mensaje=(
                    f"Tu evidencia '{evidencia.titulo}' ha recibido una observación: "
                    f"{observacion.comentario}"
                )
            )

        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.OBSERVADA
        asignacion.save()

        HistorialEstado.objects.create(
            asignacion=asignacion,
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoAsignacion.OBSERVADA,
            usuario=self.request.user,
            comentario=f"Observación creada: {observacion.comentario}"
        )

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save()
