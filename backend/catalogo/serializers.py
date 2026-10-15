"""@file serializers.py
@brief Serializadores de solo lectura para el catalogo normativo EQ-SIDACES.
@details Convierten VersionMarcoEvaluacion y la jerarquia Dimension -> Componente
-> CriterioMarco -> Estandar -> IndicadorMarco a JSON. Los codigos de indicadores
son sinteticos (no oficiales) y se marcan con codigo_sintetico; estado_revision
refleja el invariante del importador (solo se importan registros confirmados).
"""

import re

from rest_framework import serializers

from .models import (
    Componente,
    CriterioMarco,
    Dimension,
    Estandar,
    IndicadorMarco,
    VersionMarcoEvaluacion,
)

CODIGO_SINTETICO_INDICADOR = re.compile(r".+-IND-\d{2}$")


def es_codigo_sintetico(codigo: str) -> bool:
    """Los indicadores oficiales no traen codigo; el importador genera {std}-IND-NN."""
    return bool(CODIGO_SINTETICO_INDICADOR.match(codigo or ""))


class EstadoRevisionMixin(serializers.Serializer):
    """Todo lo presente en la BD proviene de registros confirmados del dataset.

    El importador import_eq_sidaces omite por diseño los registros pendientes de
    revision; el campo describe ese invariante, no un dato almacenado por fila.
    """

    estado_revision = serializers.SerializerMethodField()

    def get_estado_revision(self, obj) -> str:
        return "confirmado"


class VersionResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionMarcoEvaluacion
        fields = ["id", "nombre", "slug", "activo"]


class DimensionResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dimension
        fields = ["id", "codigo", "nombre", "orden"]


class ComponenteResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Componente
        fields = ["id", "codigo", "codigo_completo", "nombre", "orden"]


class CriterioResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = CriterioMarco
        fields = ["id", "codigo", "codigo_completo", "nombre", "orden"]


class EstandarResumenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estandar
        fields = ["id", "codigo", "codigo_completo", "orden"]


class IndicadorResumenSerializer(serializers.ModelSerializer):
    codigo_sintetico = serializers.SerializerMethodField()

    class Meta:
        model = IndicadorMarco
        fields = ["id", "codigo", "codigo_completo", "codigo_sintetico", "orden"]

    def get_codigo_sintetico(self, obj) -> bool:
        return es_codigo_sintetico(obj.codigo)


class IndicadorSerializer(EstadoRevisionMixin, serializers.ModelSerializer):
    codigo_sintetico = serializers.SerializerMethodField()
    codigo_oficial = serializers.SerializerMethodField()
    estandar = serializers.PrimaryKeyRelatedField(read_only=True)
    estandar_codigo = serializers.CharField(source="estandar.codigo_completo", read_only=True)
    version = VersionResumenSerializer(source="version_marco", read_only=True)

    class Meta:
        model = IndicadorMarco
        fields = [
            "id",
            "codigo",
            "codigo_completo",
            "codigo_sintetico",
            "codigo_oficial",
            "redaccion_oficial",
            "orden",
            "activo",
            "estado_revision",
            "estandar",
            "estandar_codigo",
            "version",
        ]

    def get_codigo_sintetico(self, obj) -> bool:
        return es_codigo_sintetico(obj.codigo)

    def get_codigo_oficial(self, obj):
        """La fuente oficial EQ-SIDACES no asigna codigo a los indicadores."""
        return None


class EstandarSerializer(EstadoRevisionMixin, serializers.ModelSerializer):
    criterio = CriterioResumenSerializer(source="criterio_marco", read_only=True)
    componente = ComponenteResumenSerializer(
        source="criterio_marco.componente", read_only=True
    )
    dimension = DimensionResumenSerializer(
        source="criterio_marco.componente.dimension", read_only=True
    )
    version = VersionResumenSerializer(source="version_marco", read_only=True)
    indicadores = serializers.SerializerMethodField()

    class Meta:
        model = Estandar
        fields = [
            "id",
            "codigo",
            "codigo_completo",
            "redaccion",
            "tipo_valor",
            "umbral_min",
            "umbral_max",
            "unidad",
            "orden",
            "estado_revision",
            "criterio",
            "componente",
            "dimension",
            "version",
            "indicadores",
        ]

    def get_indicadores(self, obj):
        hijos = obj.indicadores_marco.order_by("orden", "id")
        return IndicadorResumenSerializer(hijos, many=True).data


class CriterioSerializer(EstadoRevisionMixin, serializers.ModelSerializer):
    componente = ComponenteResumenSerializer(read_only=True)
    dimension = DimensionResumenSerializer(
        source="componente.dimension", read_only=True
    )
    version = VersionResumenSerializer(source="version_marco", read_only=True)
    estandares = serializers.SerializerMethodField()

    class Meta:
        model = CriterioMarco
        fields = [
            "id",
            "codigo",
            "codigo_completo",
            "nombre",
            "definicion",
            "orden",
            "estado_revision",
            "componente",
            "dimension",
            "version",
            "estandares",
        ]

    def get_estandares(self, obj):
        hijos = obj.estandares.order_by("orden", "id")
        return EstandarResumenSerializer(hijos, many=True).data


class ComponenteSerializer(EstadoRevisionMixin, serializers.ModelSerializer):
    dimension = DimensionResumenSerializer(read_only=True)
    version = VersionResumenSerializer(source="version_marco", read_only=True)
    criterios = serializers.SerializerMethodField()

    class Meta:
        model = Componente
        fields = [
            "id",
            "codigo",
            "codigo_completo",
            "nombre",
            "definicion",
            "orden",
            "estado_revision",
            "dimension",
            "version",
            "criterios",
        ]

    def get_criterios(self, obj):
        hijos = obj.criterios_marco.order_by("orden", "id")
        return CriterioResumenSerializer(hijos, many=True).data


class DimensionSerializer(EstadoRevisionMixin, serializers.ModelSerializer):
    version = VersionResumenSerializer(source="version_marco", read_only=True)
    componentes = serializers.SerializerMethodField()

    class Meta:
        model = Dimension
        fields = [
            "id",
            "codigo",
            "nombre",
            "definicion",
            "orden",
            "estado_revision",
            "version",
            "componentes",
        ]

    def get_componentes(self, obj):
        hijos = obj.componentes.order_by("orden", "id")
        return ComponenteResumenSerializer(hijos, many=True).data


class VersionMarcoEvaluacionSerializer(serializers.ModelSerializer):
    conteos = serializers.SerializerMethodField()

    class Meta:
        model = VersionMarcoEvaluacion
        fields = [
            "id",
            "nombre",
            "slug",
            "fecha_vigencia",
            "activo",
            "fuente",
            "nota",
            "conteos",
        ]

    def get_conteos(self, obj) -> dict:
        return {
            "dimensiones": obj.dimensiones.count(),
            "componentes": obj.componentes.count(),
            "criterios_marco": obj.criterios_marco.count(),
            "estandares": obj.estandares.count(),
            "indicadores_marco": obj.indicadores_marco.count(),
            "evidencias_indicativas": obj.evidencias_indicativas.count(),
        }
