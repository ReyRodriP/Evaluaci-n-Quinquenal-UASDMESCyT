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
            'fecha_creacion'
        ]

class VersionEvidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionEvidencia
        fields = '__all__'


class EvidenciaSerializer(serializers.ModelSerializer):
    versiones = VersionEvidenciaSerializer(many=True, read_only=True)

    class Meta:
        model = Evidencia
        fields = '__all__'