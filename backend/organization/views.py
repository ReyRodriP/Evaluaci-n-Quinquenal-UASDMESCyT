from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Facultad, Departamento, PerfilUsuario
from .serializers import (
    FacultadSerializer,
    DepartamentoSerializer,
    PerfilUsuarioSerializer
)
from accounts.permissions import CustomModelPermissions


from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class FacultadViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Facultad.objects.all().order_by('nombre')
    serializer_class = FacultadSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class DepartamentoViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Departamento.objects.all().order_by('nombre')
    serializer_class = DepartamentoSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        queryset = PerfilUsuario.objects.all().order_by('usuario__username')

        departamento_id = self.request.query_params.get('departamento')

        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)

        return queryset