from rest_framework import serializers
from .models import Facultad, Departamento, PerfilUsuario


class FacultadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facultad
        fields = '__all__'


class DepartamentoSerializer(serializers.ModelSerializer):
    facultad_nombre = serializers.CharField(
        source='facultad.nombre',
        read_only=True
    )

    class Meta:
        model = Departamento
        fields = [
            'id',
            'nombre',
            'descripcion',
            'facultad',
            'facultad_nombre'
        ]


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(
        source='usuario.username',
        read_only=True
    )

    departamento_nombre = serializers.CharField(
        source='departamento.nombre',
        read_only=True
    )

    class Meta:
        model = PerfilUsuario
        fields = [
            'id',
            'usuario',
            'usuario_nombre',
            'departamento',
            'departamento_nombre'
        ]