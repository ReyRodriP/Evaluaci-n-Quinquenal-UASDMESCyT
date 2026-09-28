"""
@file models.py
@brief Modelos de datos para la aplicación de organización.
@details Define los modelos Facultad, Departamento y PerfilUsuario que
representan la estructura organizativa de la institución.
"""

from django.conf import settings
from django.db import models


class Facultad(models.Model):
    """@class Facultad
    @brief Modelo que representa una facultad de la universidad.
    @details Almacena el nombre, descripción, estado de actividad y fecha
    de creación de cada facultad registrada en el sistema.
    """

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Departamento(models.Model):
    """@class Departamento
    @brief Modelo que representa un departamento dentro de una facultad.
    @details Cada departamento está vinculado a una facultad mediante una
    relación ForeignKey. Almacena nombre, descripción, estado y fecha de creación.
    """

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    facultad = models.ForeignKey(Facultad, on_delete=models.CASCADE, related_name="departamentos")

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    """@class PerfilUsuario
    @brief Modelo que representa el perfil organizativo de un usuario.
    @details Vincula un usuario del sistema con un departamento específico,
    permitiendo la gestión de pertenencia organizativa.
    """

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.usuario.username
