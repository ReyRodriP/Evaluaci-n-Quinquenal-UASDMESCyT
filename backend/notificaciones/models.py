"""
@file models.py
@brief Modelos de la app de notificaciones.
@details Define el modelo Notificacion para el envío y gestión
de notificaciones a los usuarios del sistema.
"""

from django.db import models
from django.conf import settings


class Notificacion(models.Model):
    """@class Notificacion
    @brief Modelo para las notificaciones del sistema.
    @details Almacena notificaciones enviadas a los usuarios,
    incluyendo título, mensaje, estado de lectura y fecha de creación.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
