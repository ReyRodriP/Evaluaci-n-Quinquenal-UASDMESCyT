from rest_framework import viewsets
from .models import Periodo, Criterio, Indicador, Asignacion
from .serializers import (
    PeriodoSerializer,
    CriterioSerializer,
    IndicadorSerializer,
    AsignacionSerializer
)


class PeriodoViewSet(viewsets.ModelViewSet):
    queryset = Periodo.objects.all().order_by('-fecha_inicio')
    serializer_class = PeriodoSerializer


class CriterioViewSet(viewsets.ModelViewSet):
    queryset = Criterio.objects.all().order_by('nombre')
    serializer_class = CriterioSerializer


class IndicadorViewSet(viewsets.ModelViewSet):
    queryset = Indicador.objects.all().order_by('nombre')
    serializer_class = IndicadorSerializer


class AsignacionViewSet(viewsets.ModelViewSet):
    queryset = Asignacion.objects.all().order_by('periodo', 'departamento')
    serializer_class = AsignacionSerializer
