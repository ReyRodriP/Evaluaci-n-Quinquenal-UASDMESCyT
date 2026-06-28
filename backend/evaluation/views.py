from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Periodo, Criterio, Indicador, Asignacion
from .serializers import (
    PeriodoSerializer,
    CriterioSerializer,
    IndicadorSerializer,
    AsignacionSerializer
)
from accounts.permissions import CustomModelPermissions


class PeriodoViewSet(viewsets.ModelViewSet):
    queryset = Periodo.objects.all().order_by('-fecha_inicio')
    serializer_class = PeriodoSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class CriterioViewSet(viewsets.ModelViewSet):
    queryset = Criterio.objects.all().order_by('nombre')
    serializer_class = CriterioSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class IndicadorViewSet(viewsets.ModelViewSet):
    queryset = Indicador.objects.all().order_by('nombre')
    serializer_class = IndicadorSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class AsignacionViewSet(viewsets.ModelViewSet):
    queryset = Asignacion.objects.all().order_by('periodo', 'departamento')
    serializer_class = AsignacionSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]
