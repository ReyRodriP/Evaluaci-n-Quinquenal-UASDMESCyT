from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.http import FileResponse
from django.db.models import Max

from rest_framework.permissions import IsAuthenticated

from accounts.permissions import CustomModelPermissions

from evaluation.models import Asignacion, EstadoAsignacion

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

    def get_permissions(self):
        if self.action == 'cambiar_estado':
            return [IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        asignacion_id = request.data.get('asignacion')
        if asignacion_id:
            existing = Evidencia.objects.filter(asignacion_id=asignacion_id).first()
            if existing:
                if existing.estado == 'cancelada':
                    existing.estado = 'activa'
                    existing.save()
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def subir_version(self, request, pk=None):
        evidencia = self.get_object()

        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response(
                {'error': 'Debe adjuntar un archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comentario = request.data.get('comentario', '')

        if evidencia.estado == 'cancelada':
            evidencia.estado = 'activa'
            evidencia.save()

        ultima_version = evidencia.versiones.aggregate(
            max_version=Max('version')
        )['max_version'] or 0
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
            asignacion.estado = EstadoAsignacion.EN_PROGRESO
            asignacion.save()

        return Response(
            VersionEvidenciaSerializer(version).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def detalle(self, request, pk=None):
        evidencia = self.get_object()
        try:
            asignacion = evidencia.asignacion
        except:
            asignacion = None

        data = EvidenciaSerializer(evidencia, context={'request': request}).data
        if asignacion:
            from evaluation.serializers import AsignacionSerializer
            data['asignacion_info'] = AsignacionSerializer(asignacion).data

        data['puede_observar'] = request.user.has_perm('evidence.add_observacion')
        data['puede_subir_version'] = request.user.has_perm('evidence.add_versionevidencia') or request.user.has_perm('evidence.add_evidencia')
        data['puede_cambiar_estado'] = request.user.has_perm('evaluation.change_asignacion')

        return Response(data)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        if not request.user.has_perm('evaluation.change_asignacion'):
            return Response(
                {'error': 'No tiene permiso para cambiar el estado'},
                status=status.HTTP_403_FORBIDDEN
            )

        evidencia = self.get_object()
        nuevo_estado = request.data.get('estado')

        if nuevo_estado not in [
            EstadoAsignacion.APROBADO,
            EstadoAsignacion.RECHAZADO,
            EstadoAsignacion.OBSERVADA
        ]:
            return Response(
                {'error': 'Estado no válido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        asignacion = evidencia.asignacion
        asignacion.estado = nuevo_estado
        asignacion.save()

        comentario = request.data.get('comentario', '').strip()
        if comentario and request.user.has_perm('evidence.add_observacion'):
            ultima_version = evidencia.versiones.order_by('-version').first()
            if ultima_version:
                Observacion.objects.create(
                    version=ultima_version,
                    usuario=request.user,
                    comentario=comentario
                )

        return Response({'estado': nuevo_estado})

    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        evidencia = self.get_object()
        versiones = evidencia.versiones.order_by('-version')

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

    # 📌 Descargar archivo
    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        version = self.get_object()

        return FileResponse(
            version.archivo.open(),
            as_attachment=True,
            filename=version.archivo.name.split('/')[-1]
        )

    # 📌 Obtener observaciones de una versión
    @action(detail=True, methods=['get'])
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

        # 🔥 Cambiar estado automáticamente
        asignacion = observacion.version.evidencia.asignacion
        asignacion.estado = EstadoAsignacion.OBSERVADA
        asignacion.save()

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save()