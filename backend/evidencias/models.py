"""
@file models.py
@brief Modelos de la app de evidencias.
@details Define el modelo Evidencia y la función de ruta para
el almacenamiento de archivos de evidencia.
"""

from django.db import models
from django.conf import settings
from evaluation.models import Asignacion


def evidencia_upload_path(instance, filename):
    """@brief Genera la ruta de subida para archivos de evidencia.
    @param instance Instancia del modelo Evidencia.
    @param filename Nombre del archivo a subir.
    @return String con la ruta de almacenamiento.
    """
    return f'evidencias/{instance.asignacion.periodo.pk}/{instance.asignacion.departamento.pk}/{instance.asignacion.indicador.pk}/{filename}'


class Evidencia(models.Model):
    """@class Evidencia
    @brief Modelo para las evidencias del sistema de evaluación.
    @details Almacena archivos de evidencia asociados a asignaciones
    de indicadores, incluyendo metadatos del archivo, versión
    y observaciones.
    """
    asignacion = models.ForeignKey(
        Asignacion,
        on_delete=models.CASCADE,
        related_name='evidencias'
    )
    archivo = models.FileField(
        upload_to=evidencia_upload_path
    )
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    tipo_archivo = models.CharField(max_length=50)
    tamano = models.BigIntegerField()
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='evidencias_subidas'
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=1)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_subida']
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'

    def __str__(self):
        return self.nombre
