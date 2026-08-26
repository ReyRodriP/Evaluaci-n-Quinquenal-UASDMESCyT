"""
@file serializers.py
@brief Serializers para la serialización/deserialización de datos de organización.
@details Define los serializers ModelSerializer para Facultad, Departamento
y PerfilUsuario, incluyendo campos de solo lectura para nombres relacionados.
"""

from rest_framework import serializers

from .models import Departamento, Facultad, PerfilUsuario


class FacultadSerializer(serializers.ModelSerializer):
    """@class FacultadSerializer
    @brief Serializer para el modelo Facultad.
    @details Serializa todos los campos del modelo Facultad incluyendo
    nombre, descripción, estado de actividad y fecha de creación.
    """

    class Meta:
        model = Facultad
        fields = "__all__"


class DepartamentoSerializer(serializers.ModelSerializer):
    """@class DepartamentoSerializer
    @brief Serializer para el modelo Departamento.
    @details Serializa los campos del departamento incluyendo el nombre
    de la facultad padre como campo de solo lectura.
    """

    facultad_nombre = serializers.CharField(source="facultad.nombre", read_only=True)

    class Meta:
        model = Departamento
        fields = ["id", "nombre", "descripcion", "facultad", "facultad_nombre", "activo", "fecha_creacion"]


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """@class PerfilUsuarioSerializer
    @brief Serializer para el modelo PerfilUsuario.
    @details Serializa los campos del perfil de usuario incluyendo los
    nombres del usuario y del departamento como campos de solo lectura.
    """

    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)

    departamento_nombre = serializers.CharField(source="departamento.nombre", read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = ["id", "usuario", "usuario_nombre", "departamento", "departamento_nombre"]
