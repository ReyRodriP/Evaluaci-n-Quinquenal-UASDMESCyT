from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from evaluation.models import (
    Asignacion,
    EstadoAsignacion,
    HistorialEstado
)
from .models import Periodo, Criterio, Indicador, Asignacion
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    PeriodoSerializer,
    CriterioSerializer,
    IndicadorSerializer,
    AsignacionSerializer
    
)
from accounts.permissions import CustomModelPermissions


from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class PeriodoViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Periodo.objects.all().order_by('-fecha_inicio')
    serializer_class = PeriodoSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class CriterioViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Criterio.objects.all().order_by('nombre')
    serializer_class = CriterioSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class IndicadorViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Indicador.objects.all().order_by('nombre')
    serializer_class = IndicadorSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

class AsignacionViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated, CustomModelPermissions]
    queryset = Asignacion.objects.all().order_by('periodo', 'departamento')
    serializer_class = AsignacionSerializer

    def crear_historial(self, asignacion, estado_anterior, estado_nuevo, request):
        HistorialEstado.objects.create(
            asignacion=asignacion,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario=request.user,
            comentario=request.data.get("comentario", "")

        )

    def validar_transicion(self, estado_actual, estado_nuevo):
        transiciones_validas = {
            EstadoAsignacion.PENDIENTE: [
                EstadoAsignacion.EN_PROGRESO
            ],
            EstadoAsignacion.OBSERVADA: [
                EstadoAsignacion.EN_PROGRESO
            ],
            EstadoAsignacion.EN_PROGRESO: [
                EstadoAsignacion.APROBADO,
                EstadoAsignacion.RECHAZADO,
                EstadoAsignacion.OBSERVADA
            ]
        }

        return estado_nuevo in transiciones_validas.get(
            estado_actual,
            []
        )

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        asignacion = self.get_object()

        if not self.validar_transicion(
            asignacion.estado,
            EstadoAsignacion.APROBADO
        ):
            return Response(
                {"error": f"No se puede cambiar de {asignacion.estado} a aprobado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.APROBADO
        asignacion.save()

        self.crear_historial(
            asignacion,
            estado_anterior,
            EstadoAsignacion.APROBADO,
            request
        )

        return Response(
            {"mensaje": "Asignación aprobada correctamente"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        asignacion = self.get_object()

        if not self.validar_transicion(
            asignacion.estado,
            EstadoAsignacion.RECHAZADO
        ):
            return Response(
                {"error": f"No se puede cambiar de {asignacion.estado} a rechazado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.RECHAZADO
        asignacion.save()

        self.crear_historial(
            asignacion,
            estado_anterior,
            EstadoAsignacion.RECHAZADO,
            request
        )

        return Response(
            {"mensaje": "Asignación rechazada correctamente"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def en_revision(self, request, pk=None):
        asignacion = self.get_object()

        if not self.validar_transicion(
            asignacion.estado,
            EstadoAsignacion.EN_PROGRESO
        ):
            return Response(
                {"error": f"No se puede cambiar de {asignacion.estado} a en_progreso"},
                status=status.HTTP_400_BAD_REQUEST
            )

        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.EN_PROGRESO
        asignacion.save()

        self.crear_historial(
            asignacion,
            estado_anterior,
            EstadoAsignacion.EN_PROGRESO,
            request
        )

        return Response(
            {"mensaje": "La asignación fue enviada a revisión correctamente"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        asignacion = self.get_object()

        evidencia = getattr(asignacion, "evidencia", None)

        versiones = []
        ultima_version = None
        cantidad_observaciones = 0
        fecha_ultima_modificacion = None

        if evidencia:
            versiones_queryset = evidencia.versiones.all().order_by("-version")

            versiones = [
                {
                    "id_version": v.id_version,
                    "version": v.version,
                    "comentario": v.comentario,
                    "fecha_subida": v.fecha_subida,
                }
                for v in versiones_queryset
            ]

            ultima = versiones_queryset.first()

            if ultima:
                ultima_version = ultima.version
                fecha_ultima_modificacion = ultima.fecha_subida
                cantidad_observaciones = ultima.observaciones.count()

        return Response({
            "asignacion": asignacion.pk,
            "indicador": asignacion.indicador.nombre,
            "departamento": asignacion.departamento.nombre,
            "estado": asignacion.estado,
            "evidencia": {
                "id": evidencia.id_evidencia,
                "titulo": evidencia.titulo,
                "descripcion": evidencia.descripcion,
                "estado": evidencia.estado,
            } if evidencia else None,
            "versiones": versiones,
            "ultima_version": ultima_version,
            "cantidad_observaciones": cantidad_observaciones,
            "fecha_ultima_modificacion": fecha_ultima_modificacion,
        })