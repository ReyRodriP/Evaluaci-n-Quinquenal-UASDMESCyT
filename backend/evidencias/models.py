from django.db import models
from django.conf import settings
from evaluation.models import Asignacion


def evidencia_upload_path(instance, filename):
    return f'evidencias/{instance.asignacion.periodo.pk}/{instance.asignacion.departamento.pk}/{instance.asignacion.indicador.pk}/{filename}'


class Evidencia(models.Model):
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
