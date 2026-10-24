"""@file serializers.py
@brief Serializadores para el módulo de evaluación.
@details Define los serializadores de Django REST Framework para convertir
las instancias de los modelos del módulo de evaluación a formato JSON y viceversa.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from accounts.permissions import asignacion_revision_permitida, es_evaluador_externo, filtrar_por_rol
from organization.models import UnidadOrganizacional

from .models import Asignacion, Criterio, HistorialEstado, Indicador, Periodo
from .services import finalizar_periodos_vencidos, validar_encargado, validar_referencia_marco


class HistorialEstadoSerializer(serializers.ModelSerializer):
    """@class HistorialEstadoSerializer
    @brief Serializador para el modelo HistorialEstado.
    @details Serializa los registros de historial de estados de las asignaciones,
    incluyendo el nombre completo del usuario que realizó el cambio.
    """

    usuario_nombre = serializers.CharField(source="usuario.get_full_name", read_only=True, default="")
    usuario_identificador = serializers.CharField(source='usuario.username', read_only=True, default=None)
    estado_anterior_display = serializers.CharField(source='get_estado_anterior_display', read_only=True, default=None)
    estado_nuevo_display = serializers.CharField(source='get_estado_nuevo_display', read_only=True)

    class Meta:
        model = HistorialEstado
        fields = [
            "id",
            "asignacion",
            "estado_anterior",
            "estado_anterior_display",
            "estado_nuevo",
            "estado_nuevo_display",
            "usuario",
            "usuario_nombre",
            "usuario_identificador",
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

    version_marco_nombre = serializers.CharField(source="version_marco.nombre", read_only=True, default=None)

    class Meta:
        model = Periodo
        fields = "__all__"

    def validate(self, attrs):
        finalizar_periodos_vencidos()
        if self.instance is not None:
            self.instance.refresh_from_db(fields=["activo"])

        version = attrs.get("version_marco", getattr(self.instance, "version_marco", None))
        if self.instance and (version.pk if version else None) != self.instance.version_marco_id:
            if self.instance.asignaciones.filter(indicador_marco__isnull=False).exists():
                raise serializers.ValidationError({"version_marco": "El período ya tiene asignaciones del marco; no puede sustituir su versión."})

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

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                self.instance = Periodo.objects.select_for_update().get(pk=instance.pk)
                self.validate(validated_data)
                return super().update(self.instance, validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc


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
    indicadores = serializers.SerializerMethodField()

    class Meta:
        model = Criterio
        fields = ["id", "nombre", "descripcion", "periodo", "periodo_nombre", "indicadores", "activo"]

    def get_indicadores(self, obj):
        indicadores = obj.indicadores.all()
        request = self.context.get("request")
        if request is not None and es_evaluador_externo(request):
            indicadores = filtrar_por_rol(indicadores, request, dept_field="unidad_responsable")
        return IndicadorSerializer(indicadores, many=True, context=self.context).data


class AsignacionSerializer(serializers.ModelSerializer):
    """@class AsignacionSerializer
    @brief Serializador para el modelo Asignacion.
    @details Serializa los campos de la asignación incluyendo los nombres
    del indicador, unidad responsable y período asociados, así como la
    representación textual del estado.
    """

    indicador_nombre = serializers.CharField(read_only=True)
    criterio_nombre = serializers.CharField(read_only=True)
    tipo_origen = serializers.CharField(read_only=True)
    ruta_marco = serializers.ReadOnlyField()
    documentos_resumen = serializers.SerializerMethodField()
    encargado_nombre = serializers.CharField(source="encargado.username", read_only=True, default=None)
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
            "indicador_marco",
            "tipo_origen",
            "criterio_nombre",
            "ruta_marco",
            "encargado",
            "encargado_nombre",
            "gestion_documental",
            "documentos_resumen",
            "unidad_responsable",
            "unidad_responsable_nombre",
            "departamento_nombre",
            "departamento",
            "periodo",
            "periodo_nombre",
            "estado",
            "estado_display",
        ]
        # Las dos claves de origen son opcionales individualmente. La validación
        # conjunta y las restricciones SQL garantizan origen y unicidad.
        validators = []
        read_only_fields = ['gestion_documental']

    def validate(self, attrs):
        finalizar_periodos_vencidos()
        periodo = attrs.get("periodo", getattr(self.instance, "periodo", None))
        unidad = attrs.get("unidad_responsable", getattr(self.instance, "unidad_responsable", None))
        request = self.context.get("request")
        if request and periodo and unidad and not asignacion_revision_permitida(request, unidad.pk, periodo.pk):
            raise serializers.ValidationError({"unidad_responsable": "La unidad y el período están fuera de sus ámbitos de revisión."})
        if periodo is not None:
            periodo.refresh_from_db(fields=["activo", "version_marco"])
            if not periodo.activo:
                raise serializers.ValidationError(
                    {"periodo": "Solo se pueden gestionar asignaciones del período activo."}
                )
        operativo = attrs.get("indicador", getattr(self.instance, "indicador", None))
        marco = attrs.get("indicador_marco", getattr(self.instance, "indicador_marco", None))
        if bool(operativo) == bool(marco):
            raise serializers.ValidationError({"indicador_marco": "Indique exactamente un indicador: operativo o del marco."})
        identidad = ("indicador", "indicador_marco", "unidad_responsable", "periodo")
        cambia_identidad = self.instance and any(
            campo in attrs and getattr(attrs[campo], "pk", None) != getattr(self.instance, campo + "_id")
            for campo in identidad
        )
        if self.instance and self.instance.gestion_documental:
            if cambia_identidad:
                raise serializers.ValidationError('La asignación documental conserva su origen, unidad y período.')
            if 'estado' in attrs and attrs['estado'] != self.instance.estado:
                raise serializers.ValidationError({'estado': 'Use la aprobación global explícita; la revisión se gestiona por documento.'})
        if cambia_identidad and (marco or self.instance.indicador_marco_id):
            if hasattr(self.instance, "evidencia") or self.instance.evidencias.exists():
                raise serializers.ValidationError("No puede cambiar el origen, la unidad o el período de una asignación del marco con evidencias.")
        if marco:
            if not unidad.activa:
                raise serializers.ValidationError({"unidad_responsable": "La unidad responsable debe estar activa."})
            try:
                validar_referencia_marco(marco, periodo)
                if self.instance is None or cambia_identidad or "encargado" in attrs:
                    validar_encargado(attrs.get("encargado", getattr(self.instance, "encargado", None)), unidad)
                if (self.instance is None or self.instance.indicador_marco_id != marco.pk) and not marco.activo:
                    raise DjangoValidationError({"indicador_marco": "El indicador del marco debe estar activo."})
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.message_dict) from exc
            if self.instance is None and attrs.get("estado", "pendiente") != "pendiente":
                raise serializers.ValidationError({"estado": "La asignación del marco debe crearse pendiente de entrega y revisión."})
        elif "encargado" in attrs and attrs["encargado"] is not None:
            try:
                validar_encargado(attrs["encargado"], unidad)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.message_dict) from exc
        origen = {"indicador_marco": marco} if marco else {"indicador": operativo}
        duplicadas = Asignacion.objects.filter(**origen, unidad_responsable=unidad, periodo=periodo)
        if self.instance:
            duplicadas = duplicadas.exclude(pk=self.instance.pk)
        if duplicadas.exists():
            raise serializers.ValidationError("Ya existe una asignación de este indicador a la unidad en el período.")
        return attrs

    def _guardar(self, validated_data, instance=None):
        try:
            with transaction.atomic():
                periodo = validated_data.get("periodo", getattr(instance, "periodo", None))
                periodos = {periodo.pk}
                if instance:
                    periodos.add(instance.periodo_id)
                list(Periodo.objects.select_for_update().filter(pk__in=periodos).order_by("pk"))
                if instance:
                    self.instance = Asignacion.objects.select_for_update().get(pk=instance.pk)
                self.validate(validated_data)
                if instance:
                    return super().update(self.instance, validated_data)
                return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise serializers.ValidationError("Conflicto al guardar la asignación; compruebe el origen y que no exista un duplicado.") from exc

    def create(self, validated_data):
        return self._guardar(validated_data)

    def update(self, instance, validated_data):
        return self._guardar(validated_data, instance)

    def get_departamento(self, obj):
        return obj.unidad_responsable.departamento_legacy_id

    def get_documentos_resumen(self, obj):
        if not obj.gestion_documental:
            return None
        solicitudes = obj.solicitudes_documentales.all()
        return {'solicitados': solicitudes.count(), 'aprobados': solicitudes.filter(estado='aprobada').count(),
                'entregados': solicitudes.filter(versiones__isnull=False).distinct().count(),
                'observados': solicitudes.filter(estado='observada').count()}

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
