from rest_framework import viewsets, parsers
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from rest_framework.decorators import action
from .models import Evidencia
from .serializers import EvidenciaSerializer
from accounts.permissions import CustomModelPermissions, filtrar_por_rol
from auditoria.utils import registrar_auditoria
from notificaciones.utils import crear_notificacion
from evaluation.models import EstadoAsignacion


class EvidenciaViewSet(viewsets.ModelViewSet):
    queryset = Evidencia.objects.all()
    serializer_class = EvidenciaSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        queryset = Evidencia.objects.all()
        asignacion_id = self.request.query_params.get('asignacion')
        if asignacion_id:
            queryset = queryset.filter(asignacion_id=asignacion_id)
        return filtrar_por_rol(queryset, self.request, dept_field='asignacion__departamento')

    def perform_create(self, serializer):
        instance = serializer.save()
        accion = "Subir versión" if instance.version > 1 else "Crear evidencia"
        desc = (
            f"{'Se subió una nueva versión' if instance.version > 1 else 'Se creó la evidencia'}"
            f" '{instance.nombre}' v{instance.version} "
            f"para el indicador '{instance.asignacion.indicador.nombre}' "
            f"del departamento '{instance.asignacion.departamento.nombre}'"
        )
        registrar_auditoria(
            usuario=self.request.user,
            accion=accion,
            modelo="Evidencia",
            registro_id=instance.pk,
            descripcion=desc
        )

    def perform_destroy(self, instance):
        registrar_auditoria(
            usuario=self.request.user,
            accion="Eliminar evidencia",
            modelo="Evidencia",
            registro_id=instance.pk,
            descripcion=f"Se eliminó la evidencia '{instance.nombre}'"
        )
        instance.delete()

    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        evidencia = self.get_object()
        response = FileResponse(
            evidencia.archivo.open('rb'),
            as_attachment=True,
            filename=evidencia.archivo.name.split('/')[-1]
        )
        registrar_auditoria(
            usuario=request.user,
            accion="Descargar evidencia",
            modelo="Evidencia",
            registro_id=evidencia.pk,
            descripcion=f"Se descargó la evidencia '{evidencia.nombre}'"
        )
        return response
