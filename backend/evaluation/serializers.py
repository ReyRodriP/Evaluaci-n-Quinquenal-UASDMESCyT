from rest_framework import serializers
from .models import Periodo, Criterio, Indicador, Asignacion


class PeriodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Periodo
        fields = '__all__'


class IndicadorSerializer(serializers.ModelSerializer):
    criterio_nombre = serializers.CharField(
        source='criterio.nombre',
        read_only=True
    )

    class Meta:
        model = Indicador
        fields = [
            'id',
            'nombre',
            'descripcion',
            'criterio',
            'criterio_nombre',
            'obligatorio',
            'activo'
        ]


class CriterioSerializer(serializers.ModelSerializer):
    periodo_nombre = serializers.CharField(
        source='periodo.nombre',
        read_only=True
    )
    indicadores = IndicadorSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Criterio
        fields = [
            'id',
            'nombre',
            'descripcion',
            'periodo',
            'periodo_nombre',
            'indicadores',
            'activo'
        ]


class AsignacionSerializer(serializers.ModelSerializer):
    indicador_nombre = serializers.CharField(
        source='indicador.nombre',
        read_only=True
    )
    departamento_nombre = serializers.CharField(
        source='departamento.nombre',
        read_only=True
    )
    periodo_nombre = serializers.CharField(
        source='periodo.nombre',
        read_only=True
    )
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )

    class Meta:
        model = Asignacion
        fields = [
            'id',
            'indicador',
            'indicador_nombre',
            'departamento',
            'departamento_nombre',
            'periodo',
            'periodo_nombre',
            'estado',
            'estado_display'
        ]
