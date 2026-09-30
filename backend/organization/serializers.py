"""
@file serializers.py
@brief Serializers para la serialización/deserialización de datos de organización.
@details Define los serializers ModelSerializer para Facultad, Departamento
y PerfilUsuario, incluyendo campos de solo lectura para nombres relacionados.
"""

from rest_framework import serializers

from .models import (
    AmbitoEvaluacion,
    Departamento,
    Facultad,
    PerfilUsuario,
    TipoUnidadOrganizacional,
    UnidadOrganizacional,
)


class TipoUnidadOrganizacionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoUnidadOrganizacional
        fields = "__all__"


class UnidadOrganizacionalSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="tipo.nombre", read_only=True)
    unidad_padre_nombre = serializers.CharField(source="unidad_padre.nombre", read_only=True, default=None)

    class Meta:
        model = UnidadOrganizacional
        fields = [
            "id",
            "nombre",
            "descripcion",
            "tipo",
            "tipo_nombre",
            "unidad_padre",
            "unidad_padre_nombre",
            "activa",
            "fecha_creacion",
        ]

    def validate(self, attrs):
        if "unidad_padre" in attrs:
            parent = attrs["unidad_padre"]
        elif self.instance:
            parent = self.instance.unidad_padre
        else:
            parent = None

        while parent is not None:
            if self.instance and parent.pk == self.instance.pk:
                raise serializers.ValidationError({"unidad_padre": "La jerarquía no puede contener ciclos."})
            parent = parent.unidad_padre

        return attrs


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
    @details Serializa el perfil y el nombre de la unidad organizacional asociada.
    """

    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)

    unidad_organizacional_nombre = serializers.CharField(source="unidad_organizacional.nombre", read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "usuario",
            "usuario_nombre",
            "unidad_organizacional",
            "unidad_organizacional_nombre",
        ]


class AmbitoEvaluacionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)
    unidad_nombre = serializers.CharField(source="unidad_organizacional.nombre", read_only=True)
    periodo_nombre = serializers.CharField(source="periodo.nombre", read_only=True)

    class Meta:
        model = AmbitoEvaluacion
        fields = [
            "id",
            "usuario",
            "usuario_nombre",
            "unidad_organizacional",
            "unidad_nombre",
            "periodo",
            "periodo_nombre",
            "activo",
            "fecha_asignacion",
        ]
        read_only_fields = ["fecha_asignacion"]

    def validate(self, attrs):
        usuario = attrs.get("usuario", getattr(self.instance, "usuario", None))
        unidad = attrs.get("unidad_organizacional", getattr(self.instance, "unidad_organizacional", None))
        periodo = attrs.get("periodo", getattr(self.instance, "periodo", None))
        if usuario and unidad and periodo:
            duplicate = AmbitoEvaluacion.objects.filter(
                usuario=usuario,
                unidad_organizacional=unidad,
                periodo=periodo,
            )
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError("Ya existe un ámbito para este usuario, unidad y período.")
        return attrs
