from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse

from .models import Evidencia, VersionEvidencia
from .serializers import EvidenciaSerializer, VersionEvidenciaSerializer


# CRUD de Evidencias
class EvidenciaViewSet(viewsets.ModelViewSet):
    queryset = Evidencia.objects.all()
    serializer_class = EvidenciaSerializer

    # 📌 Subir nueva versión de archivo
    @action(detail=True, methods=['post'])
    def subir_version(self, request, pk=None):
        evidencia = self.get_object()

        archivo = request.FILES.get('archivo')
        comentario = request.data.get('comentario', '')

        if not archivo:
            return Response(
                {"error": "No se envió archivo"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ultima_version = VersionEvidencia.objects.filter(
            evidencia=evidencia
        ).count()

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

    # 📌 Ver historial
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        evidencia = self.get_object()
        versiones = evidencia.versiones.all()
        return Response(
            VersionEvidenciaSerializer(versiones, many=True).data
        )


# CRUD de Versiones
class VersionEvidenciaViewSet(viewsets.ModelViewSet):
    queryset = VersionEvidencia.objects.all()
    serializer_class = VersionEvidenciaSerializer

    # 📌 DESCARGAR ARCHIVO (NUEVO)
    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        version = self.get_object()
        return FileResponse(
            version.archivo.open(),
            as_attachment=True,
            filename=version.archivo.name.split('/')[-1]
        )