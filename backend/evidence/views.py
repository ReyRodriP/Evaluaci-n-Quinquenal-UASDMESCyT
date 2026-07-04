from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.db.models import Max
import os
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Observacion
from .serializers import ObservacionSerializer
from evaluation.models import EstadoAsignacion
from evaluation.models import Asignacion, EstadoAsignacion

from .models import Evidencia, VersionEvidencia, Observacion
from .serializers import (
    EvidenciaSerializer,
    VersionEvidenciaSerializer,
    ObservacionSerializer
)

# CRUD de Evidencias
class EvidenciaViewSet(viewsets.ModelViewSet):
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
        evidencia = self.get_object()

        archivo = request.FILES.get('archivo')
        comentario = request.data.get('comentario', '')

        if not archivo:
            return Response({"error": "No se envió archivo"}, status=status.HTTP_400_BAD_REQUEST)

        if archivo.size == 0:
            return Response({"error": "El archivo está vacío"}, status=status.HTTP_400_BAD_REQUEST)

        extensiones_permitidas = ('.pdf', '.doc', '.docx', '.xls', '.xlsx')
        extension = os.path.splitext(archivo.name)[1].lower()

        if extension not in extensiones_permitidas:
            return Response(
                {"error": "Formato de archivo no permitido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ultima_version = VersionEvidencia.objects.filter(
            evidencia=evidencia
        ).aggregate(Max('version'))['version__max'] or 0

        version = VersionEvidencia.objects.create(
            evidencia=evidencia,
            archivo=archivo,
            version=ultima_version + 1,
            comentario=comentario
        )

        return Response(
            VersionEvidenciaSerializer(version).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        evidencia = self.get_object()
        versiones = evidencia.versiones.all()

        return Response(
            VersionEvidenciaSerializer(versiones, many=True).data
        )

    # 📌 Ver historial de versiones
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        evidencia = self.get_object()
        versiones = evidencia.versiones.all()

        return Response(
            VersionEvidenciaSerializer(versiones, many=True).data
        )


# CRUD de Versiones
class VersionEvidenciaViewSet(viewsets.ReadOnlyModelViewSet):
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
    
        # 📌 Obtener observaciones de una versión
    @action(detail=True, methods=['get'])
    def observaciones(self, request, pk=None):
        version = self.get_object()

        serializer = ObservacionSerializer(
            version.observaciones.all(),
            many=True
        )

        return Response(serializer.data)


# CRUD de Observaciones
class ObservacionViewSet(viewsets.ModelViewSet):
    queryset = Observacion.objects.all()
    serializer_class = ObservacionSerializer

    def perform_create(self, serializer):
        observacion = serializer.save(usuario=self.request.user)

        # 🔥 cambiar estado automáticamente
        asignacion = observacion.version.evidencia.asignacion
        asignacion.estado = EstadoAsignacion.OBSERVADA
        asignacion.save()