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


class TipoUnidadOrganizacional(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class UnidadOrganizacional(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.ForeignKey(TipoUnidadOrganizacional, on_delete=models.PROTECT, related_name="unidades")
    unidad_padre = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subunidades"
    )
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    departamento_legacy = models.OneToOneField(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="unidades_organizacionales",
    )

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    """@class PerfilUsuario
    @brief Modelo que representa el perfil organizativo de un usuario.
    @details Vincula un usuario del sistema con un departamento específico,
    permitiendo la gestión de pertenencia organizativa.
    """

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    unidad_organizacional = models.ForeignKey(
        UnidadOrganizacional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="perfiles",
    )
    def __str__(self):
        return self.usuario.username


class AmbitoEvaluacion(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ambitos_evaluacion",
    )
    unidad_organizacional = models.ForeignKey(
        UnidadOrganizacional,
        on_delete=models.PROTECT,
        related_name="ambitos_evaluacion",
    )
    periodo = models.ForeignKey(
        "evaluation.Periodo",
        on_delete=models.PROTECT,
        related_name="ambitos_evaluacion",
    )
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "unidad_organizacional", "periodo"],
                name="ambito_evaluacion_usuario_unidad_periodo_unico",
            )
        ]
        ordering = ["usuario__username", "periodo__fecha_inicio", "unidad_organizacional__nombre"]

    def __str__(self):
        return f"{self.usuario} · {self.unidad_organizacional} · {self.periodo}"
