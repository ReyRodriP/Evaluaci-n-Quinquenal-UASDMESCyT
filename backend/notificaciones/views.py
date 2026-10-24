"""
@file views.py
@brief Vistas de la app de notificaciones.
@details Define los viewsets para la gestión de notificaciones
de los usuarios, incluyendo listado y marcado de leídas.
"""

from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notificacion
from .serializers import NotificacionSerializer


class NotificacionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """@class NotificacionViewSet
    @brief ViewSet para la gestión de notificaciones de usuario.
    @details Permite listar notificaciones del usuario autenticado,
    marcar una notificación individual como leída y marcar todas
    las notificaciones como leídas. Solo autenticados.
    """

    permission_classes = [IsAuthenticated]
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        from .documentales import asignaciones_notificables

        return Notificacion.objects.filter(usuario=self.request.user).filter(
            Q(destino_documental__isnull=True) | Q(destino_documental__asignacion__in=asignaciones_notificables(self.request))
        ).select_related('destino_documental__asignacion').order_by('-fecha_creacion', '-pk')

    @action(detail=True, methods=["patch"])
    def leer(self, request, pk=None):
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.save()
        return Response(NotificacionSerializer(notificacion).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def marcar_todas(self, request):
        actualizadas = self.get_queryset().filter(leida=False).update(leida=True)
        return Response({"actualizadas": actualizadas}, status=status.HTTP_200_OK)
