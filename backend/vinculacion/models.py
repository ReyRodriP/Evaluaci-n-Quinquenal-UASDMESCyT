"""Modelos de la app de vinculación catálogo ↔ operativo.

Correspondencia: tabla de unión explícita entre un nodo operativo
(evaluation.Criterio o evaluation.Indicador) y un nodo del marco oficial
(catalogo.Dimension, catalogo.Estandar o catalogo.IndicadorMarco), anclada a la
versión del marco de la que proviene el destino.

Garantías:
- Nivel de base de datos: exactamente un origen, exactamente un destino,
  unicidad de pares vivos (propuesta/confirmada) por combinación válida,
  coherencia de sellos de fecha con el estado y comentario obligatorio al rechazar.
- Nivel de aplicación: pertenencia del destino a version_marco, máquina de
  transiciones (confirmar/rechazar/desconfirmar) con actor y auditoría, y bloqueo
  de escrituras directas de estado o del par origen-destino-version.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from auditoria.utils import registrar_auditoria
from .validaciones import validar_destino_en_version


class EstadoCorrespondencia(models.TextChoices):
    """Estados del acuerdo técnico de una correspondencia.

    No confundir con la aprobación institucional del marco (D13).
    """

    PROPUESTA = "propuesta", "Propuesta"
    CONFIRMADA = "confirmada", "Confirmada"
    RECHAZADA = "rechazada", "Rechazada"


class ProcedenciaCorrespondencia(models.TextChoices):
    """Origen del registro: captura manual o sugerencia derivada de nombres."""

    MANUAL = "manual", "Manual"
    DERIVADA = "derivada", "Derivada"


class Correspondencia(models.Model):
    """Correspondencia entre un nodo operativo y un nodo del marco EQ-SIDACES."""

    criterio_op = models.ForeignKey(
        "evaluation.Criterio",
        on_delete=models.PROTECT,
        related_name="correspondencias_catalogo",
        null=True,
        blank=True,
    )
    indicador_op = models.ForeignKey(
        "evaluation.Indicador",
        on_delete=models.PROTECT,
        related_name="correspondencias_catalogo",
        null=True,
        blank=True,
    )
    dimension = models.ForeignKey(
        "catalogo.Dimension",
        on_delete=models.PROTECT,
        related_name="correspondencias",
        null=True,
        blank=True,
    )
    estandar = models.ForeignKey(
        "catalogo.Estandar",
        on_delete=models.PROTECT,
        related_name="correspondencias",
        null=True,
        blank=True,
    )
    indicador_marco = models.ForeignKey(
        "catalogo.IndicadorMarco",
        on_delete=models.PROTECT,
        related_name="correspondencias",
        null=True,
        blank=True,
    )
    version_marco = models.ForeignKey(
        "catalogo.VersionMarcoEvaluacion",
        on_delete=models.PROTECT,
        related_name="correspondencias",
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoCorrespondencia.choices,
        default=EstadoCorrespondencia.PROPUESTA,
    )
    procedencia = models.CharField(
        max_length=20,
        choices=ProcedenciaCorrespondencia.choices,
        default=ProcedenciaCorrespondencia.MANUAL,
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correspondencias_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correspondencias_confirmadas",
    )
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    rechazado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="correspondencias_rechazadas",
    )
    fecha_rechazo = models.DateTimeField(null=True, blank=True)
    comentario = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_creacion", "-id"]
        constraints = [
            models.CheckConstraint(
                name="vinculacion_correspondencia_origen_unico",
                condition=(
                    models.Q(criterio_op__isnull=False, indicador_op__isnull=True)
                    | models.Q(criterio_op__isnull=True, indicador_op__isnull=False)
                ),
            ),
            models.CheckConstraint(
                name="vinculacion_correspondencia_destino_unico",
                condition=(
                    models.Q(dimension__isnull=False, estandar__isnull=True, indicador_marco__isnull=True)
                    | models.Q(dimension__isnull=True, estandar__isnull=False, indicador_marco__isnull=True)
                    | models.Q(dimension__isnull=True, estandar__isnull=True, indicador_marco__isnull=False)
                ),
            ),
            models.CheckConstraint(
                name="vinculacion_correspondencia_sello_confirmada",
                condition=(
                    ~models.Q(estado=EstadoCorrespondencia.CONFIRMADA)
                    | models.Q(fecha_confirmacion__isnull=False)
                ),
            ),
            models.CheckConstraint(
                name="vinculacion_correspondencia_sello_rechazada",
                condition=(
                    ~models.Q(estado=EstadoCorrespondencia.RECHAZADA)
                    | models.Q(fecha_rechazo__isnull=False) & ~models.Q(comentario="")
                ),
            ),
            models.CheckConstraint(
                name="vinculacion_correspondencia_sello_propuesta",
                condition=(
                    ~models.Q(estado=EstadoCorrespondencia.PROPUESTA)
                    | models.Q(fecha_confirmacion__isnull=True, fecha_rechazo__isnull=True)
                ),
            ),
            # Unicidad de pares vivos: una restricción parcial por cada
            # combinación válida origen × destino (evita el pseudo-campo
            # genérico origen_id/destino_id). rechazada no participa: una fila
            # rechazada no bloquea re-propuestas del mismo par.
            models.UniqueConstraint(
                fields=["criterio_op", "dimension"],
                condition=models.Q(estado__in=["propuesta", "confirmada"])
                & models.Q(criterio_op__isnull=False, dimension__isnull=False),
                name="vinculacion_corr_crit_dim_viva",
            ),
            models.UniqueConstraint(
                fields=["criterio_op", "estandar"],
                condition=models.Q(estado__in=["propuesta", "confirmada"])
                & models.Q(criterio_op__isnull=False, estandar__isnull=False),
                name="vinculacion_corr_crit_std_viva",
            ),
            models.UniqueConstraint(
                fields=["criterio_op", "indicador_marco"],
                condition=models.Q(estado__in=["propuesta", "confirmada"])
                & models.Q(criterio_op__isnull=False, indicador_marco__isnull=False),
                name="vinculacion_corr_crit_indmarco_viva",
            ),
            models.UniqueConstraint(
                fields=["indicador_op", "dimension"],
                condition=models.Q(estado__in=["propuesta", "confirmada"])
                & models.Q(indicador_op__isnull=False, dimension__isnull=False),
                name="vinculacion_corr_indop_dim_viva",
            ),
            models.UniqueConstraint(
                fields=["indicador_op", "estandar"],
                condition=models.Q(estado__in=["propuesta", "confirmada"])
                & models.Q(indicador_op__isnull=False, estandar__isnull=False),
                name="vinculacion_corr_indop_std_viva",
            ),
            models.UniqueConstraint(
                fields=["indicador_op", "indicador_marco"],
                condition=models.Q(estado__in=["propuesta", "confirmada"])
                & models.Q(indicador_op__isnull=False, indicador_marco__isnull=False),
                name="vinculacion_corr_indop_indmarco_viva",
            ),
        ]

    def __str__(self):
        origen = self.criterio_op or self.indicador_op
        destino = self.dimension or self.estandar or self.indicador_marco
        return f"{origen} → {destino} ({self.estado})"

    def clean(self):
        super().clean()
        if self.version_marco_id:
            validar_destino_en_version(
                self.version_marco_id,
                dimension=self.dimension,
                estandar=self.estandar,
                indicador_marco=self.indicador_marco,
            )

    def save(self, *args, **kwargs):
        """Bloquea escrituras directas del estado o del par origen-destino-versión.

        Las transiciones legítimas pasan por confirmar()/rechazar()/desconfirmar(),
        que marcan _transicion_autorizada antes de guardar.
        """
        if self.pk and not getattr(self, "_transicion_autorizada", False):
            previo = (
                Correspondencia.objects.filter(pk=self.pk)
                .values(
                    "estado",
                    "criterio_op_id",
                    "indicador_op_id",
                    "dimension_id",
                    "estandar_id",
                    "indicador_marco_id",
                    "version_marco_id",
                )
                .first()
            )
            if previo:
                if previo["estado"] != self.estado:
                    raise ValidationError(
                        "Los cambios de estado deben realizarse mediante los métodos "
                        "confirmar(), rechazar() o desconfirmar()."
                    )
                fijos = (
                    "criterio_op_id",
                    "indicador_op_id",
                    "dimension_id",
                    "estandar_id",
                    "indicador_marco_id",
                    "version_marco_id",
                )
                if any(previo[campo] != getattr(self, campo) for campo in fijos):
                    raise ValidationError(
                        "El origen, el destino y la versión del marco no pueden "
                        "modificarse después de la creación."
                    )
        super().save(*args, **kwargs)

    @classmethod
    def crear_propuesta(
        cls,
        *,
        actor,
        version_marco,
        dimension=None,
        estandar=None,
        indicador_marco=None,
        criterio_op=None,
        indicador_op=None,
        procedencia=ProcedenciaCorrespondencia.MANUAL,
        comentario="",
    ):
        """Crea una correspondencia en estado propuesta y registra su auditoría."""
        if (criterio_op is None) == (indicador_op is None):
            raise ValidationError("Debe indicarse exactamente un origen operativo (criterio_op o indicador_op).")
        validar_destino_en_version(version_marco, dimension=dimension, estandar=estandar, indicador_marco=indicador_marco)
        correspondencia = cls(
            criterio_op=criterio_op,
            indicador_op=indicador_op,
            dimension=dimension,
            estandar=estandar,
            indicador_marco=indicador_marco,
            version_marco=version_marco,
            procedencia=procedencia,
            creado_por=actor,
            comentario=comentario,
        )
        correspondencia.full_clean()
        with transaction.atomic():
            correspondencia.save()
            registrar_auditoria(
                usuario=actor,
                accion="crear correspondencia",
                modelo="Correspondencia",
                registro_id=correspondencia.pk,
                descripcion=(
                    "Correspondencia creada en estado propuesta. "
                    f"Comentario: {comentario or '(sin comentario)'}"
                ),
            )
        return correspondencia

    def confirmar(self, actor, comentario=""):
        """Transición propuesta → confirmada. Requiere actor."""
        self._transicionar(
            desde=EstadoCorrespondencia.PROPUESTA,
            hacia=EstadoCorrespondencia.CONFIRMADA,
            actor=actor,
            comentario=comentario,
            accion="confirmar correspondencia",
            comentario_obligatorio=False,
        )

    def rechazar(self, actor, comentario):
        """Transición propuesta → rechazada. Requiere comentario y actor."""
        self._transicionar(
            desde=EstadoCorrespondencia.PROPUESTA,
            hacia=EstadoCorrespondencia.RECHAZADA,
            actor=actor,
            comentario=comentario,
            accion="rechazar correspondencia",
            comentario_obligatorio=True,
        )

    def desconfirmar(self, actor, comentario):
        """Transición confirmada → propuesta (desconfirmación explícita)."""
        self._transicionar(
            desde=EstadoCorrespondencia.CONFIRMADA,
            hacia=EstadoCorrespondencia.PROPUESTA,
            actor=actor,
            comentario=comentario,
            accion="desconfirmar correspondencia",
            comentario_obligatorio=True,
        )

    def _transicionar(self, *, desde, hacia, actor, comentario, accion, comentario_obligatorio):
        if self.estado != desde:
            raise ValidationError(f"Transición no permitida: solo puede pasar de «{desde}» a «{hacia}».")
        if actor is None:
            raise ValidationError("Debe indicarse el usuario que realiza la transición.")
        if comentario_obligatorio and not (comentario or "").strip():
            raise ValidationError("Esta transición requiere un comentario.")
        estado_anterior = self.estado
        self.estado = hacia
        self.comentario = comentario or ""
        if hacia == EstadoCorrespondencia.CONFIRMADA:
            self.confirmado_por = actor
            self.fecha_confirmacion = timezone.now()
            self.rechazado_por = None
            self.fecha_rechazo = None
        elif hacia == EstadoCorrespondencia.RECHAZADA:
            self.rechazado_por = actor
            self.fecha_rechazo = timezone.now()
            self.confirmado_por = None
            self.fecha_confirmacion = None
        else:  # propuesta (desconfirmación)
            self.confirmado_por = None
            self.fecha_confirmacion = None
            self.rechazado_por = None
            self.fecha_rechazo = None
        with transaction.atomic():
            self._transicion_autorizada = True
            self.save()
            registrar_auditoria(
                usuario=actor,
                accion=accion,
                modelo="Correspondencia",
                registro_id=self.pk,
                descripcion=(
                    f"Transición de correspondencia: estado «{estado_anterior}» → «{hacia}». "
                    f"Comentario: {comentario or '(sin comentario)'}"
                ),
            )
