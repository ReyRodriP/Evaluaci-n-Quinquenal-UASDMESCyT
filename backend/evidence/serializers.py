from rest_framework import serializers
from .models import Evidencia, VersionEvidencia, Observacion
from rest_framework import serializers
from .models import Observacion

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

    class Meta:
        model = VersionEvidencia
        fields = [
            'id_version',
            'evidencia',
            'archivo',
            'version',
            'comentario',
            'fecha_subida',
            'observaciones'
        ]

class EvidenciaSerializer(serializers.ModelSerializer):
    versiones = VersionEvidenciaSerializer(many=True, read_only=True)

    class Meta:
        model = Evidencia
        fields = '__all__'