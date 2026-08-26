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
    class Meta:
        model = Notificacion
        fields = '__all__'
        read_only_fields = ['usuario', 'titulo', 'mensaje', 'fecha_creacion']
