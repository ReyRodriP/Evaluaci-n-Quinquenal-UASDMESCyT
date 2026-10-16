"""Serializadores de la API de vinculación.

CorrespondenciaSerializer (lectura) anida resúmenes del origen operativo y del
destino del marco. CorrespondenciaCreacionSerializer acepta solo identificadores
de origen/destino/versión; los sellos de auditoría (creado_por, confirmado_por,
rechazado_por y sus fechas) y el estado nunca son aceptables desde el cliente.
"""

from rest_framework import serializers

from catalogo.models import Dimension, Estandar, IndicadorMarco, VersionMarcoEvaluacion
from evaluation.models import Criterio, Indicador

from .models import Correspondencia, EstadoCorrespondencia, ProcedenciaCorrespondencia
from .validaciones import validar_destino_en_version


class VersionMarcoResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionMarcoEvaluacion
        fields = ["id", "nombre", "slug", "activo"]


class CorrespondenciaSerializer(serializers.ModelSerializer):
    """Representación de lectura con origen/destino resumidos y sellos del servidor."""

    version_marco = VersionMarcoResumenSerializer(read_only=True)
    origen = serializers.SerializerMethodField()
    destino = serializers.SerializerMethodField()
    creado_por = serializers.SlugRelatedField(slug_field="username", read_only=True)
    confirmado_por = serializers.SlugRelatedField(slug_field="username", read_only=True)
    rechazado_por = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = Correspondencia
        fields = [
            "id",
            "estado",
            "procedencia",
            "criterio_op",
            "indicador_op",
            "dimension",
            "estandar",
            "indicador_marco",
            "version_marco",
            "origen",
            "destino",
            "creado_por",
            "fecha_creacion",
            "confirmado_por",
            "fecha_confirmacion",
            "rechazado_por",
            "fecha_rechazo",
            "comentario",
        ]
        read_only_fields = [
            "estado",
            "criterio_op",
            "indicador_op",
            "dimension",
            "estandar",
            "indicador_marco",
            "creado_por",
            "fecha_creacion",
            "confirmado_por",
            "fecha_confirmacion",
            "rechazado_por",
            "fecha_rechazo",
        ]

    def get_origen(self, obj):
        if obj.criterio_op_id is not None:
            return {"nivel": "criterio", "id": obj.criterio_op_id, "texto": obj.criterio_op.nombre}
        if obj.indicador_op_id is not None:
            return {"nivel": "indicador", "id": obj.indicador_op_id, "texto": obj.indicador_op.nombre}
        return None

    def get_destino(self, obj):
        if obj.dimension_id is not None:
            return {"nivel": "dimension", "id": obj.dimension_id, "texto": str(obj.dimension)}
        if obj.estandar_id is not None:
            return {"nivel": "estandar", "id": obj.estandar_id, "texto": str(obj.estandar)}
        if obj.indicador_marco_id is not None:
            return {"nivel": "indicador_marco", "id": obj.indicador_marco_id, "texto": str(obj.indicador_marco)}
        return None


class CorrespondenciaCreacionSerializer(serializers.Serializer):
    """Datos de creación de una propuesta: solo PKs operativos, de marco y versión."""

    version_marco = serializers.PrimaryKeyRelatedField(queryset=VersionMarcoEvaluacion.objects.all())
    criterio_op = serializers.PrimaryKeyRelatedField(queryset=Criterio.objects.all(), required=False, allow_null=True)
    indicador_op = serializers.PrimaryKeyRelatedField(queryset=Indicador.objects.all(), required=False, allow_null=True)
    dimension = serializers.PrimaryKeyRelatedField(queryset=Dimension.objects.all(), required=False, allow_null=True)
    estandar = serializers.PrimaryKeyRelatedField(queryset=Estandar.objects.all(), required=False, allow_null=True)
    indicador_marco = serializers.PrimaryKeyRelatedField(
        queryset=IndicadorMarco.objects.all(), required=False, allow_null=True
    )
    procedencia = serializers.ChoiceField(
        choices=ProcedenciaCorrespondencia.choices, default=ProcedenciaCorrespondencia.MANUAL
    )
    comentario = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        origines = [attrs.get("criterio_op"), attrs.get("indicador_op")]
        if sum(1 for origen in origines if origen is not None) != 1:
            raise serializers.ValidationError(
                "Debe indicarse exactamente un origen operativo (criterio_op o indicador_op)."
            )
        destinos = [attrs.get("dimension"), attrs.get("estandar"), attrs.get("indicador_marco")]
        if sum(1 for destino in destinos if destino is not None) != 1:
            raise serializers.ValidationError(
                "Debe indicarse exactamente un destino del marco (dimension, estandar o indicador_marco)."
            )
        validar_destino_en_version(
            attrs["version_marco"],
            dimension=attrs.get("dimension"),
            estandar=attrs.get("estandar"),
            indicador_marco=attrs.get("indicador_marco"),
        )
        return attrs


class TransicionCorrespondenciaSerializer(serializers.Serializer):
    """Cuerpo de las acciones de estado; el comentario es la única entrada posible."""

    comentario = serializers.CharField(required=False, allow_blank=True, default="")


__all__ = [
    "CorrespondenciaSerializer",
    "CorrespondenciaCreacionSerializer",
    "TransicionCorrespondenciaSerializer",
    "VersionMarcoResumenSerializer",
    "EstadoCorrespondencia",
]
