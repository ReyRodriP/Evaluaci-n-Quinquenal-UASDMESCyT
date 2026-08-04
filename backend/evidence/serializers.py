from rest_framework import serializers
from .models import Evidencia, VersionEvidencia, Observacion

class ObservacionSerializer(serializers.ModelSerializer):
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
        if not value or not value.strip():
            raise serializers.ValidationError(
                "El comentario no puede estar vacío."
            )
        return value
class VersionEvidenciaSerializer(serializers.ModelSerializer):
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
        if obj.archivo:
            return f"/api/versiones/{obj.id_version}/descargar/"
        return None

    def get_nombre_archivo(self, obj):
        if obj.archivo:
            return obj.archivo.name.split('/')[-1]
        return None

class EditarVersionSerializer(serializers.Serializer):
    archivo = serializers.FileField(required=False, allow_null=True)
    comentario = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        archivo = validated_data.get('archivo')
        comentario = validated_data.get('comentario')

        if archivo:
            instance.archivo = archivo
        if comentario is not None:
            instance.comentario = comentario

        instance.save()
        return instance

class EvidenciaSerializer(serializers.ModelSerializer):
    versiones = VersionEvidenciaSerializer(many=True, read_only=True)
    ultima_version = serializers.SerializerMethodField()
    asignacion_estado = serializers.SerializerMethodField()
    asignacion_estado_display = serializers.SerializerMethodField()
    ultima_observacion = serializers.SerializerMethodField()

    class Meta:
        model = Evidencia
        fields = '__all__'

    def get_ultima_version(self, obj):
        ultima = obj.versiones.order_by('-version').first()
        if ultima:
            return VersionEvidenciaSerializer(ultima).data
        return None

    def get_asignacion_estado(self, obj):
        try:
            return obj.asignacion.estado
        except:
            return None

    def get_asignacion_estado_display(self, obj):
        try:
            return obj.asignacion.get_estado_display()
        except:
            return None

    def get_ultima_observacion(self, obj):
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