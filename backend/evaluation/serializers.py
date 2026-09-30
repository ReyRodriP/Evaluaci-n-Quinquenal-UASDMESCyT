"""@file serializers.py
@brief Serializadores para el módulo de evaluación.
@details Define los serializadores de Django REST Framework para convertir
las instancias de los modelos del módulo de evaluación a formato JSON y viceversa.
"""

from rest_framework import serializers

from organization.models import UnidadOrganizacional

from .models import Asignacion, Criterio, HistorialEstado, Indicador, Periodo
from .services import finalizar_periodos_vencidos


class HistorialEstadoSerializer(serializers.ModelSerializer):
    """@class HistorialEstadoSerializer
    @brief Serializador para el modelo HistorialEstado.
    @details Serializa los registros de historial de estados de las asignaciones,
    incluyendo el nombre completo del usuario que realizó el cambio.
    """

    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True, default="")

    class Meta:
        model = HistorialEstado
        fields = [
            "id",
            "asignacion",
            "estado_anterior",
            "estado_nuevo",
            "usuario",
            "usuario_nombre",
            "comentario",
            "fecha",
        ]
        read_only_fields = ["usuario", "fecha"]


class PeriodoSerializer(serializers.ModelSerializer):
    """@class PeriodoSerializer
    @brief Serializador para el modelo Periodo.
    @details Serializa todos los campos del modelo Periodo para su
    representación en formato JSON.
    """

    class Meta:
        model = Periodo
        fields = "__all__"

    def validate(self, attrs):
        finalizar_periodos_vencidos()
        if self.instance is not None:
            self.instance.refresh_from_db(fields=["activo"])

        fecha_inicio = attrs.get("fecha_inicio", getattr(self.instance, "fecha_inicio", None))
        fecha_fin = attrs.get("fecha_fin", getattr(self.instance, "fecha_fin", None))
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError({"fecha_fin": "Debe ser posterior a la fecha de inicio."})

        activo = attrs.get("activo", getattr(self.instance, "activo", True))
        if activo:
            periodos_activos = Periodo.objects.filter(activo=True)
            if self.instance:
                periodos_activos = periodos_activos.exclude(pk=self.instance.pk)
            if periodos_activos.exists():
                raise serializers.ValidationError(
                    {"activo": "Ya existe otro período activo. Desactívelo antes de activar este período."}
                )
        return attrs


class IndicadorSerializer(serializers.ModelSerializer):
    """@class IndicadorSerializer
    @brief Serializador para el modelo Indicador.
    @details Serializa los campos del indicador incluyendo el nombre
    del criterio asociado como campo de solo lectura.
    """

    criterio_nombre = serializers.CharField(source="criterio.nombre", read_only=True)

    class Meta:
        model = Indicador
        fields = ["id", "nombre", "descripcion", "criterio", "criterio_nombre", "obligatorio", "activo"]


class CriterioSerializer(serializers.ModelSerializer):
    """@class CriterioSerializer
    @brief Serializador para el modelo Criterio.
    @details Serializa los campos del criterio incluyendo el nombre del período
    asociado y una lista anidada de indicadores en modo de solo lectura.
    """

    periodo_nombre = serializers.CharField(source="periodo.nombre", read_only=True)
    indicadores = IndicadorSerializer(many=True, read_only=True)

    class Meta:
        model = Criterio
        fields = ["id", "nombre", "descripcion", "periodo", "periodo_nombre", "indicadores", "activo"]


class AsignacionSerializer(serializers.ModelSerializer):
    """@class AsignacionSerializer
    @brief Serializador para el modelo Asignacion.
    @details Serializa los campos de la asignación incluyendo los nombres
    del indicador, unidad responsable y período asociados, así como la
    representación textual del estado.
    """

    indicador_nombre = serializers.CharField(source="indicador.nombre", read_only=True)
    unidad_responsable_nombre = serializers.CharField(source="unidad_responsable.nombre", read_only=True)
    departamento = serializers.SerializerMethodField()
    departamento_nombre = serializers.CharField(source="unidad_responsable.nombre", read_only=True)
    periodo_nombre = serializers.CharField(source="periodo.nombre", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Asignacion
        fields = [
            "id",
            "indicador",
            "indicador_nombre",
            "unidad_responsable",
            "unidad_responsable_nombre",
            "departamento_nombre",
            "departamento",
            "periodo",
            "periodo_nombre",
            "estado",
            "estado_display",
        ]

    def validate(self, attrs):
        finalizar_periodos_vencidos()
        periodo = attrs.get("periodo", getattr(self.instance, "periodo", None))
        if periodo is not None:
            periodo.refresh_from_db(fields=["activo"])
            if not periodo.activo:
                raise serializers.ValidationError(
                    {"periodo": "Solo se pueden gestionar asignaciones del período activo."}
                )
        return attrs

    def get_departamento(self, obj):
        return obj.unidad_responsable.departamento_legacy_id

    def to_internal_value(self, data):
        data = data.copy()
        departamento_id = data.get("departamento")
        data.pop("departamento", None)
        if departamento_id is not None and not data.get("unidad_responsable"):
            unidad = UnidadOrganizacional.objects.filter(departamento_legacy_id=departamento_id).first()
            if unidad is None:
                raise serializers.ValidationError({"departamento": "No existe una unidad para ese departamento."})
            data["unidad_responsable"] = unidad.pk
        return super().to_internal_value(data)
