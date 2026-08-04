from rest_framework import serializers
from .models import Auditoria


class AuditoriaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(
        source='usuario.username',
        read_only=True
    )

    class Meta:
        model = Auditoria
        fields = '__all__'
