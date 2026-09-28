"""@file models.py
@brief Modelos de datos para el módulo de evaluación.
@details Define los modelos ORM de Django que representan períodos de evaluación,
criterios, indicadores, asignaciones y el historial de estados de las asignaciones.
"""

from django.conf import settings
from django.db import models


class Periodo(models.Model):
    """@class Periodo
    @brief Modelo que representa un período de evaluación.
    @details Almacena la información de un período, incluyendo nombre,
    fechas de inicio y fin, y si se encuentra activo.
    """

    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Criterio(models.Model):
    """@class Criterio
    @brief Modelo que representa un criterio de evaluación.
    @details Un criterio agrupa indicadores y pertenece a un período.
    Contiene nombre, descripción y un enlace hacia el período asociado.
    """

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="criterios", null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Indicador(models.Model):
    """@class Indicador
    @brief Modelo que representa un indicador dentro de un criterio.
    @details Un indicador es el elemento base de evaluación, asociado a un criterio.
    Puede ser obligatorio o no y mantenerse activo o inactivo.
    """

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    criterio = models.ForeignKey(Criterio, on_delete=models.CASCADE, related_name="indicadores")
    obligatorio = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class EstadoAsignacion(models.TextChoices):
    """@class EstadoAsignacion
    @brief Enumeración de posibles estados de una asignación.
    @details Define los estados disponibles para una asignación:
    pendiente, en_progreso, completado, aprobado, rechazado y observada.
    """

    PENDIENTE = "pendiente", "Pendiente"
    EN_PROGRESO = "en_progreso", "En progreso"
    COMPLETADO = "completado", "Completado"
    APROBADO = "aprobado", "Aprobado"
    RECHAZADO = "rechazado", "Rechazado"
    OBSERVADA = "observada", "Observada"


class Asignacion(models.Model):
    """@class Asignacion
    @brief Modelo que representa la asignación de un indicador a un departamento.
    @details Vincula un indicador, un departamento y un período. Mantene el estado
    actual de la asignación y garantiza unicidad por la tripleta de claves foráneas.
    """

    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE, related_name="asignaciones")
    departamento = models.ForeignKey("organization.Departamento", on_delete=models.CASCADE, related_name="asignaciones")
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="asignaciones")
    estado = models.CharField(max_length=20, choices=EstadoAsignacion.choices, default=EstadoAsignacion.PENDIENTE)

    class Meta:
        unique_together = ("indicador", "departamento", "periodo")

    def __str__(self):
        return f"{self.indicador} - {self.departamento} ({self.periodo})"


class HistorialEstado(models.Model):
    """@class HistorialEstado
    @brief Modelo que registra el historial de cambios de estado de una asignación.
    @details Almacena cada transición de estado de una asignación, incluyendo
    el estado anterior, el nuevo estado, el usuario que realizó el cambio,
    un comentario opcional y la fecha de la transición.
    """

    asignacion = models.ForeignKey(Asignacion, on_delete=models.CASCADE, related_name="historial_estados")

    estado_anterior = models.CharField(max_length=20, choices=EstadoAsignacion.choices, null=True, blank=True)

    estado_nuevo = models.CharField(max_length=20, choices=EstadoAsignacion.choices)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="historial_estados"
    )

    comentario = models.TextField(blank=True, null=True)

    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asignacion} {self.estado_anterior} → {self.estado_nuevo}"

    class Meta:
        ordering = ["-fecha"]
