from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Facultad, Departamento, PerfilUsuario
from .serializers import (
    FacultadSerializer,
    DepartamentoSerializer,
    PerfilUsuarioSerializer
)
from accounts.permissions import CustomModelPermissions


class FacultadViewSet(viewsets.ModelViewSet):
    queryset = Facultad.objects.all().order_by('nombre')
    serializer_class = FacultadSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all().order_by('nombre')
    serializer_class = DepartamentoSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        queryset = PerfilUsuario.objects.all().order_by('usuario__username')

        departamento_id = self.request.query_params.get('departamento')

        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)

        return queryset