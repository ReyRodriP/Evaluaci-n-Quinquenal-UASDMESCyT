"""
@file models.py
@brief Modelos de la app de notificaciones.
@details Define el modelo Notificacion para el envío y gestión
de notificaciones a los usuarios del sistema.
"""

from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    """@class Notificacion
    @brief Modelo para las notificaciones del sistema.
    @details Almacena notificaciones enviadas a los usuarios,
    incluyendo título, mensaje, estado de lectura y fecha de creación.
    """

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones")
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"


class DestinoNotificacionDocumental(models.Model):
    """Destino estructurado de un aviso nuevo; no se deduce de mensajes históricos."""

    notificacion = models.OneToOneField(Notificacion, on_delete=models.CASCADE, primary_key=True, related_name='destino_documental')
    asignacion = models.ForeignKey('evaluation.Asignacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    solicitud = models.ForeignKey('evidence.SolicitudDocumental', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    version = models.ForeignKey('evidence.VersionDocumento', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        if self._state.adding and not self.asignacion_id:
            raise ValidationError({'asignacion': 'El aviso documental requiere una asignación.'})
        if self.solicitud_id and self.solicitud.asignacion_id != self.asignacion_id:
            raise ValidationError({'solicitud': 'La solicitud no pertenece a la asignación del aviso.'})
        if self.version_id and self.version.solicitud_id != self.solicitud_id:
            raise ValidationError({'version': 'La versión no pertenece a la solicitud del aviso.'})
