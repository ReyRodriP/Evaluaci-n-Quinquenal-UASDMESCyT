from rest_framework import serializers
from .models import Evidencia


class EvidenciaSerializer(serializers.ModelSerializer):
    asignacion_indicador = serializers.CharField(
        source='asignacion.indicador.nombre',
        read_only=True
    )
    asignacion_departamento = serializers.CharField(
        source='asignacion.departamento.nombre',
        read_only=True
    )
    asignacion_periodo = serializers.CharField(
        source='asignacion.periodo.nombre',
        read_only=True
    )
    subido_por_username = serializers.CharField(
        source='subido_por.username',
        read_only=True
    )

    class Meta:
        model = Evidencia
        fields = [
            'id',
            'asignacion',
            'asignacion_indicador',
            'asignacion_departamento',
            'asignacion_periodo',
            'archivo',
            'nombre',
            'descripcion',
            'tipo_archivo',
            'tamano',
            'subido_por',
            'subido_por_username',
            'fecha_subida',
            'version',
            'observaciones'
        ]
        read_only_fields = [
            'subido_por',
            'tipo_archivo',
            'tamano',
            'fecha_subida',
            'version'
        ]

    def validate_archivo(self, value):
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg',
            'image/png',
            'image/gif',
            'text/plain',
            'application/zip',
            'application/x-rar-compressed'
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Tipo de archivo '{value.content_type}' no permitido. "
                f"Tipos permitidos: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF, TXT, ZIP, RAR"
            )
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                "El archivo no puede superar los 50 MB."
            )
        return value

    def create(self, validated_data):
        validated_data['subido_por'] = self.context['request'].user
        validated_data['tipo_archivo'] = validated_data['archivo'].content_type
        validated_data['tamano'] = validated_data['archivo'].size

        asignacion = validated_data['asignacion']
        existing = Evidencia.objects.filter(asignacion=asignacion)
        if existing.exists():
            validated_data['version'] = existing.count() + 1

        return super().create(validated_data)
