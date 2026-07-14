from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response

from .models import Notificacion
from .serializers import NotificacionSerializer


class NotificacionViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user)

    @action(detail=True, methods=['patch'])
    def leer(self, request, pk=None):
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.save()
        return Response(
            NotificacionSerializer(notificacion).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def marcar_todas(self, request):
        actualizadas = Notificacion.objects.filter(
            usuario=request.user, leida=False
        ).update(leida=True)
        return Response(
            {'actualizadas': actualizadas},
            status=status.HTTP_200_OK
        )
