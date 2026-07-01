from django.db import models
from evaluation.models import Asignacion

class Evidencia(models.Model):
    id_evidencia = models.AutoField(primary_key=True)

    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    asignacion = models.OneToOneField(
        Asignacion,
        on_delete=models.CASCADE,
        related_name='evidencia'
    )

    def __str__(self):
        return self.titulo


class VersionEvidencia(models.Model):
    id_version = models.AutoField(primary_key=True)

    evidencia = models.ForeignKey(
        Evidencia,
        on_delete=models.CASCADE,
        related_name='versiones'
    )

    archivo = models.FileField(upload_to='evidencias/')
    version = models.IntegerField(default=1)
    comentario = models.TextField(blank=True, null=True)

    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evidencia.titulo} - v{self.version}"