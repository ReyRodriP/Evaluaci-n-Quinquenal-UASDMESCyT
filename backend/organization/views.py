from rest_framework import viewsets
from .models import Facultad, Departamento, PerfilUsuario
from .serializers import (
    FacultadSerializer,
    DepartamentoSerializer,
    PerfilUsuarioSerializer
)


class FacultadViewSet(viewsets.ModelViewSet):
    queryset = Facultad.objects.all().order_by('nombre')
    serializer_class = FacultadSerializer


class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all().order_by('nombre')
    serializer_class = DepartamentoSerializer


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    queryset = PerfilUsuario.objects.all().order_by('usuario__username')
    serializer_class = PerfilUsuarioSerializer