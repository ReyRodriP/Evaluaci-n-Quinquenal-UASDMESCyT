from rest_framework import viewsets
from .models import Periodo, Criterio, Indicador, Asignacion
from .serializers import (
    PeriodoSerializer,
    CriterioSerializer,
    IndicadorSerializer,
    AsignacionSerializer
)


from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class PeriodoViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Periodo.objects.all().order_by('-fecha_inicio')
    serializer_class = PeriodoSerializer


class CriterioViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Criterio.objects.all().order_by('nombre')
    serializer_class = CriterioSerializer


class IndicadorViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Indicador.objects.all().order_by('nombre')
    serializer_class = IndicadorSerializer


class AsignacionViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Asignacion.objects.all().order_by('periodo', 'departamento')
    serializer_class = AsignacionSerializer
