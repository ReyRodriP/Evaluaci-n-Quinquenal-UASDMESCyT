"""
@file views.py
@brief Vistas de la app de auditoría.
@details Define los viewsets para la visualización de registros
de auditoría del sistema.
"""

from rest_framework import mixins, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import PuedeVerAuditoria

from .models import Auditoria
from .serializers import AuditoriaSerializer


class AuditoriaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """@class AuditoriaViewSet
    @brief ViewSet de solo lectura para registros de auditoría.
    @details Permite listar y consultar registros de auditoría.
    Requiere autenticación por token y el permiso PuedeVerAuditoria.
    Solo usuarios con permisos especiales pueden acceder a la información.
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, PuedeVerAuditoria]
    queryset = Auditoria.objects.all()
    serializer_class = AuditoriaSerializer
    ordering = ["-fecha"]
