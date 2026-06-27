from rest_framework import viewsets
from .models import Facultad, Departamento, PerfilUsuario
from .serializers import (
    FacultadSerializer,
    DepartamentoSerializer,
    PerfilUsuarioSerializer
)


from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class FacultadViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Facultad.objects.all().order_by('nombre')
    serializer_class = FacultadSerializer


class DepartamentoViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Departamento.objects.all().order_by('nombre')
    serializer_class = DepartamentoSerializer


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = PerfilUsuario.objects.all()
    serializer_class = PerfilUsuarioSerializer

    def get_queryset(self):
        queryset = PerfilUsuario.objects.all().order_by('usuario__username')

        departamento_id = self.request.query_params.get('departamento')

        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)

        return queryset