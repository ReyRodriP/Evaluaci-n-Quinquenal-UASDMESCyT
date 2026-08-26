"""
@file models.py
@brief Modelos de la app de auditoría.
@details Define el modelo Auditoria para el registro de acciones
realizadas sobre los registros del sistema.
"""

from django.db import models
from django.conf import settings


class Auditoria(models.Model):
    """@class Auditoria
    @brief Modelo para el registro de auditoría del sistema.
    @details Almacena información sobre cada acción realizada
    por un usuario sobre un registro del sistema, incluyendo
    la acción, el modelo afectado, el ID del registro y una
    descripción detallada.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    accion = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    registro_id = models.IntegerField(null=True, blank=True)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.accion} - {self.fecha}"
