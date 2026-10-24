"""
@file serializers.py
@brief Serializers de la app de notificaciones.
@details Define el serializer para la serialización de datos
del modelo Notificacion a formato JSON.
"""

from rest_framework import serializers

from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    """@class NotificacionSerializer
    @brief Serializer para el modelo Notificacion.
    @details Serializa los campos del modelo Notificacion con
    campos de solo lectura para usuario, título, mensaje y fecha.
    """

    destino = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = ['id', 'usuario', 'titulo', 'mensaje', 'leida', 'fecha_creacion', 'destino']
        read_only_fields = ["usuario", "titulo", "mensaje", "fecha_creacion"]

    def get_destino(self, obj):
        destino = getattr(obj, 'destino_documental', None)
        if not destino or not destino.asignacion_id:
            return None
        return {'asignacion_id': destino.asignacion_id, 'periodo_id': destino.asignacion.periodo_id,
            'solicitud_id': destino.solicitud_id, 'version_id': destino.version_id}
