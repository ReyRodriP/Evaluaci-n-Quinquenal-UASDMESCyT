from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .models import Auditoria
from .serializers import AuditoriaSerializer


class AuditoriaViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Auditoria.objects.all()
    serializer_class = AuditoriaSerializer
    ordering = ['-fecha']
