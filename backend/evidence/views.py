from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
import os
from django.db.models import Max

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

        # Validar que se envíe un archivo
        if not archivo:
            return Response(
                {"error": "No se envió archivo"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que el archivo no esté vacío
        if archivo.size == 0:
            return Response(
                {"error": "El archivo está vacío"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar extensión del archivo
        extensiones_permitidas = ('.pdf', '.doc', '.docx', '.xls', '.xlsx')

        extension = os.path.splitext(archivo.name)[1].lower()

        if extension not in extensiones_permitidas:
            return Response(
                {
                    "error": "Formato de archivo no permitido. Solo se aceptan archivos PDF, DOC, DOCX, XLS y XLSX."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcular automáticamente la siguiente versión
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

    # 📌 Ver historial de versiones
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        evidencia = self.get_object()
        versiones = evidencia.versiones.all()

        return Response(
            VersionEvidenciaSerializer(versiones, many=True).data
        )


# CRUD de Versiones (solo lectura)
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