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

    def create(self, request, *args, **kwargs):
        asignacion_id = request.data.get('asignacion')
        if asignacion_id:
            existing = Evidencia.objects.filter(asignacion_id=asignacion_id).first()
            if existing:
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def subir_version(self, request, pk=None):
        ...
        # Todo este método queda igual

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