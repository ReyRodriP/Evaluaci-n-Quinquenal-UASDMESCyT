"""
@file serializers.py
@brief Serializers de la app de auditoría.
@details Define el serializer para la serialización de datos
del modelo Auditoria a formato JSON.
"""

from rest_framework import serializers

from .models import Auditoria


class AuditoriaSerializer(serializers.ModelSerializer):
    """@class AuditoriaSerializer
    @brief Serializer para el modelo Auditoria.
    @details Serializa todos los campos del modelo Auditoria e incluye
    el nombre de usuario del usuario que realizó la acción.
    """

    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = Auditoria
        fields = "__all__"
