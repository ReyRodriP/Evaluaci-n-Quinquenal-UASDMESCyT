"""@file models.py
@brief Modelos de datos para el módulo de evaluación.
@details Define los modelos ORM de Django que representan períodos de evaluación,
criterios, indicadores, asignaciones y el historial de estados de las asignaciones.
"""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


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
    version_marco = models.ForeignKey(
        "catalogo.VersionMarcoEvaluacion", on_delete=models.PROTECT,
        null=True, blank=True, related_name="periodos",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__gt=models.F("fecha_inicio")),
                name="periodo_fecha_fin_posterior_inicio",
            ),
            models.UniqueConstraint(
                fields=["activo"],
                condition=models.Q(activo=True),
                name="periodo_unico_activo",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio >= self.fecha_fin:
            errors["fecha_fin"] = "La fecha de fin debe ser posterior a la fecha de inicio."
        if self.activo and Periodo.objects.exclude(pk=self.pk).filter(activo=True).exists():
            errors["activo"] = "Ya existe otro período activo. Desactívelo antes de activar este período."
        if self.pk:
            anterior = Periodo.objects.filter(pk=self.pk).values_list("version_marco_id", flat=True).first()
            if anterior != self.version_marco_id and self.asignaciones.filter(indicador_marco__isnull=False).exists():
                errors["version_marco"] = "El período ya tiene asignaciones del marco; no puede sustituir su versión."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self._state.adding:
            return super().save(*args, **kwargs)
        with transaction.atomic():
            anterior = Periodo.objects.select_for_update().get(pk=self.pk)
            campos = kwargs.get("update_fields")
            if campos is None or "version_marco" in campos or "version_marco_id" in campos:
                if anterior.version_marco_id != self.version_marco_id and self.asignaciones.filter(indicador_marco__isnull=False).exists():
                    raise ValidationError({"version_marco": "El período ya tiene asignaciones del marco; no puede sustituir su versión."})
            return super().save(*args, **kwargs)

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

    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE, related_name="asignaciones", null=True, blank=True)
    indicador_marco = models.ForeignKey(
        "catalogo.IndicadorMarco", on_delete=models.PROTECT,
        null=True, blank=True, related_name="asignaciones",
    )
    encargado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="asignaciones_encargadas",
    )
    unidad_responsable = models.ForeignKey(
        "organization.UnidadOrganizacional",
        on_delete=models.CASCADE,
        related_name="asignaciones",
    )
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="asignaciones")
    estado = models.CharField(max_length=20, choices=EstadoAsignacion.choices, default=EstadoAsignacion.PENDIENTE)
    gestion_documental = models.BooleanField(default=False, editable=False)

    class Meta:
        unique_together = ("indicador", "unidad_responsable", "periodo")
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(indicador__isnull=False, indicador_marco__isnull=True)
                    | models.Q(indicador__isnull=True, indicador_marco__isnull=False)
                ),
                name="asignacion_origen_unico",
            ),
            models.UniqueConstraint(
                fields=["indicador_marco", "unidad_responsable", "periodo"],
                condition=models.Q(indicador_marco__isnull=False),
                name="asignacion_marco_unidad_periodo_unica",
            ),
        ]

    @property
    def tipo_origen(self):
        return "marco" if self.indicador_marco_id else "operativo"

    @property
    def indicador_nombre(self):
        return self.indicador_marco.redaccion_oficial if self.indicador_marco_id else self.indicador.nombre

    @property
    def criterio_nombre(self):
        return self.indicador_marco.estandar.criterio_marco.nombre if self.indicador_marco_id else self.indicador.criterio.nombre

    @property
    def ruta_marco(self):
        if not self.indicador_marco_id:
            return None
        indicador = self.indicador_marco
        estandar = indicador.estandar
        criterio = estandar.criterio_marco
        componente = criterio.componente
        dimension = componente.dimension
        return {
            "version": {"id": indicador.version_marco_id, "nombre": indicador.version_marco.nombre, "slug": indicador.version_marco.slug, "activo": indicador.version_marco.activo},
            "dimension": {"id": dimension.pk, "codigo": dimension.codigo, "nombre": dimension.nombre},
            "componente": {"id": componente.pk, "codigo": componente.codigo_completo, "nombre": componente.nombre},
            "criterio": {"id": criterio.pk, "codigo": criterio.codigo_completo, "nombre": criterio.nombre},
            "estandar": {"id": estandar.pk, "codigo": estandar.codigo_completo, "nombre": estandar.redaccion},
            "indicador": {"id": indicador.pk, "codigo": indicador.codigo_completo, "nombre": indicador.redaccion_oficial, "orden": indicador.orden, "codigo_sintetico": bool(re.fullmatch(r".+-IND-\d{2}", indicador.codigo or ""))},
        }

    def clean(self):
        super().clean()
        if bool(self.indicador_id) == bool(self.indicador_marco_id):
            raise ValidationError({"indicador_marco": "Indique exactamente un indicador: operativo o del marco."})
        if self.indicador_marco_id and self.periodo_id:
            from .services import validar_encargado, validar_referencia_marco

            validar_referencia_marco(self.indicador_marco, self.periodo)
            if self._state.adding:
                validar_encargado(self.encargado, self.unidad_responsable)
                if not self.indicador_marco.activo or not self.unidad_responsable.activa:
                    raise ValidationError("El indicador y la unidad responsable deben estar activos.")
                if self.estado != EstadoAsignacion.PENDIENTE:
                    raise ValidationError({"estado": "La asignación del marco debe crearse pendiente de entrega y revisión."})

    def save(self, *args, **kwargs):
        if not self.indicador_marco_id:
            return super().save(*args, **kwargs)
        # Comparte el bloqueo del período con su actualización de versión.
        with transaction.atomic():
            periodo = Periodo.objects.select_for_update().get(pk=self.periodo_id)
            from .services import validar_referencia_marco

            if not self._state.adding:
                anterior = Asignacion.objects.select_for_update().get(pk=self.pk)
                if anterior.gestion_documental:
                    self.gestion_documental = True
                    if any(getattr(anterior, campo) != getattr(self, campo) for campo in (
                        'indicador_id', 'indicador_marco_id', 'unidad_responsable_id', 'periodo_id'
                    )):
                        raise ValidationError('La asignación con gestión documental conserva su origen, unidad y período.')
            validar_referencia_marco(self.indicador_marco, periodo)
            if self.gestion_documental and self.estado == EstadoAsignacion.APROBADO:
                from evidence.documentos import validar_cierre_documental

                validar_cierre_documental(self)
            if self._state.adding:
                self.clean()
            return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.indicador_nombre} - {self.unidad_responsable} ({self.periodo})"


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
