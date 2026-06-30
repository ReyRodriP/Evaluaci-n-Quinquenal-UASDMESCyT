from rest_framework import serializers
from .models import Evidencia, VersionEvidencia


class VersionEvidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionEvidencia
        fields = '__all__'


class EvidenciaSerializer(serializers.ModelSerializer):
    # 👇 aquí se agregan las versiones automáticamente
    versiones = VersionEvidenciaSerializer(many=True, read_only=True)

    class Meta:
        model = Evidencia
        fields = '__all__'