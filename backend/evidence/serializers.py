"""@file serializers.py
@brief Serializadores para la app de evidencias
@details Define los serializers de Django REST Framework para la
serialización y deserialización de datos de evidencias, versiones
y observaciones, incluyendo campos calculados y validaciones."""

from rest_framework import serializers
from .models import Evidencia, VersionEvidencia, Observacion

class ObservacionSerializer(serializers.ModelSerializer):
    """@class ObservacionSerializer
    @brief Serializer para el modelo Observacion
    @details Serializa los campos de observación incluyendo el nombre
    del usuario y validación del comentario para evitar valores vacíos."""

    usuario_nombre = serializers.ReadOnlyField(source='usuario.username')

    class Meta:
        model = Observacion
        fields = [
            'id',
            'version',
            'usuario',
            'usuario_nombre',
            'comentario',
            'fecha_creacion',
            'activo'
        ]

        read_only_fields = [
            'usuario',
            'fecha_creacion',
            'activo'
        ]

    def validate_comentario(self, value):
        """@brief Valida que el comentario no esté vacío
        @param value Valor del comentario a validar
        @return value Comentario validado
        @raises ValidationError Si el comentario está vacío o contiene solo espacios"""

        if not value or not value.strip():
            raise serializers.ValidationError(
                "El comentario no puede estar vacío."
            )
        return value
class VersionEvidenciaSerializer(serializers.ModelSerializer):
    """@class VersionEvidenciaSerializer
    @brief Serializer para el modelo VersionEvidencia
    @details Serializa las versiones de evidencia incluyendo observaciones
    anidadas, URL de descarga y nombre del archivo."""

    observaciones = ObservacionSerializer(many=True, read_only=True)
    descargar_url = serializers.SerializerMethodField()
    nombre_archivo = serializers.SerializerMethodField()

    class Meta:
        model = VersionEvidencia
        fields = [
            'id_version',
            'evidencia',
            'archivo',
            'descargar_url',
            'nombre_archivo',
            'version',
            'comentario',
            'fecha_subida',
            'observaciones'
        ]

    def get_descargar_url(self, obj):
        """@brief Genera la URL de descarga del archivo de la versión
        @param obj Instancia de VersionEvidencia
        @return str URL de descarga o None si no hay archivo"""

        if obj.archivo:
            return f"/api/versiones/{obj.id_version}/descargar/"
        return None

    def get_nombre_archivo(self, obj):
        """@brief Extrae el nombre del archivo sin la ruta
        @param obj Instancia de VersionEvidencia
        @return str Nombre del archivo o None si no hay archivo"""

        if obj.archivo:
            return obj.archivo.name.split('/')[-1]
        return None

class EditarVersionSerializer(serializers.Serializer):
    """@class EditarVersionSerializer
    @brief Serializer para la edición de versiones existentes
    @details Serializer no basado en modelo para permitir la actualización
    parcial del archivo y comentario de una versión."""

    archivo = serializers.FileField(required=False, allow_null=True)
    comentario = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        """@brief Actualiza los campos de una versión existente
        @details Actualiza solo los campos proporcionados en validated_data.
        @param instance Instancia de VersionEvidencia a actualizar
        @param validated_data Diccionario con los campos a actualizar
        @return instance Instancia actualizada"""

        archivo = validated_data.get('archivo')
        comentario = validated_data.get('comentario')

        if archivo:
            instance.archivo = archivo
        if comentario is not None:
            instance.comentario = comentario

        instance.save()
        return instance

class EvidenciaSerializer(serializers.ModelSerializer):
    """@class EvidenciaSerializer
    @brief Serializer para el modelo Evidencia
    @details Serializa las evidencias con versiones anidadas, última versión,
    estado de la asignación y última observación recibida."""

    versiones = VersionEvidenciaSerializer(many=True, read_only=True)
    ultima_version = serializers.SerializerMethodField()
    asignacion_estado = serializers.SerializerMethodField()
    asignacion_estado_display = serializers.SerializerMethodField()
    ultima_observacion = serializers.SerializerMethodField()

    class Meta:
        model = Evidencia
        fields = '__all__'

    def get_ultima_version(self, obj):
        """@brief Obtiene la versión más reciente de la evidencia
        @param obj Instancia de Evidencia
        @return dict Datos serializados de la última versión o None"""

        ultima = obj.versiones.order_by('-version').first()
        if ultima:
            return VersionEvidenciaSerializer(ultima).data
        return None

    def get_asignacion_estado(self, obj):
        """@brief Obtiene el estado actual de la asignación asociada
        @param obj Instancia de Evidencia
        @return str Código del estado o None"""

        try:
            return obj.asignacion.estado
        except:
            return None

    def get_asignacion_estado_display(self, obj):
        """@brief Obtiene la representación legible del estado de la asignación
        @param obj Instancia de Evidencia
        @return str Nombre legible del estado o None"""

        try:
            return obj.asignacion.get_estado_display()
        except:
            return None

    def get_ultima_observacion(self, obj):
        """@brief Obtiene la observación más reciente de la última versión
        @param obj Instancia de Evidencia
        @return dict Datos de la última observación activa o None"""

        ultima_version = obj.versiones.order_by('-version').first()
        if ultima_version:
            ultima_obs = ultima_version.observaciones.filter(activo=True).order_by('-fecha_creacion').first()
            if ultima_obs:
                return {
                    'comentario': ultima_obs.comentario,
                    'usuario_nombre': ultima_obs.usuario.username,
                    'fecha_creacion': ultima_obs.fecha_creacion
                }
        return None
