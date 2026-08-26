"""@file models.py
@brief Modelos de datos para la app de evidencias
@details Define los modelos principales para la gestión de evidencias,
versiones de evidencia, observaciones y sus estados en el sistema."""

from django.db import models
from django.conf import settings
from evaluation.models import Asignacion


class EstadoEvidencia(models.TextChoices):
    """@class EstadoEvidencia
    @brief Enumeración de estados posibles para una evidencia
    @details Define los estados disponibles: ACTIVA (evidencia activa y
    en proceso de revisión) y CANCELADA (evidencia deshabilitada)."""

    ACTIVA = 'activa', 'Activa'
    CANCELADA = 'cancelada', 'Cancelada'


class Evidencia(models.Model):
    """@class Evidencia
    @brief Modelo principal que representa una evidencia asociada a una asignación
    @details Cada evidencia está vinculada a una única asignación y puede tener
    múltiples versiones de archivo. Gestiona el título, descripción, estado
    y fecha de creación."""

    id_evidencia = models.AutoField(primary_key=True)

    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=EstadoEvidencia.choices,
        default=EstadoEvidencia.ACTIVA
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    asignacion = models.OneToOneField(
        Asignacion,
        on_delete=models.CASCADE,
        related_name='evidencia'
    )

    def __str__(self):
        return self.titulo


class VersionEvidencia(models.Model):
    """@class VersionEvidencia
    @brief Modelo que representa una versión de archivo subido para una evidencia
    @details Cada vez que se sube un archivo nuevo para una evidencia, se crea
    una nueva versión incremental. Almacena el archivo, número de versión,
    comentario opcional y fecha de subida."""

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


class Observacion(models.Model):
    """@class Observacion
    @brief Modelo que representa una observación realizada sobre una versión de evidencia
    @details Permite a los usuarios con permisos agregar comentarios y observaciones
    sobre versiones específicas de evidencias. Las observaciones pueden desactivarse
    (soft delete) y se ordenan por fecha de creación descendente."""

    id = models.AutoField(primary_key=True)

    version = models.ForeignKey(
        VersionEvidencia,
        on_delete=models.CASCADE,
        related_name='observaciones'
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='observaciones'
    )

    comentario = models.TextField()

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Observación #{self.id} - Versión {self.version.version}"

    class Meta:
        ordering = ['-fecha_creacion']
