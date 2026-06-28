from rest_framework import serializers
from .models import Evidencia, VersionEvidencia


class EvidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidencia
        fields = '__all__'


class VersionEvidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = VersionEvidencia
        fields = '__all__'