"""Modelos del catálogo normativo EQ-SIDACES.

Jerarquía oficial: Dimensión → Componente → Criterio → Estándar → Indicador → Evidencia.
Todos los niveles cuelgan de una VersionMarcoEvaluacion para permitir coexistencia de
versiones del marco sin ambigüedad.
"""

from django.db import models


class VersionMarcoEvaluacion(models.Model):
    """Versión del marco de estándares (p. ej. EQ-SIDACES 2019, Res. 27-2019 CONESCyT)."""

    nombre = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    fecha_vigencia = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=False)
    fuente = models.CharField(max_length=255, blank=True)
    nota = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_vigencia", "-id"]
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(activo=True),
                fields=["activo"],
                name="catalogo_versionmarcoevaluacion_activa_unica",
            ),
        ]

    def __str__(self):
        return self.nombre


class Dimension(models.Model):
    """Nivel 1 de la jerarquía oficial (8 dimensiones, códigos romanos I–VIII)."""

    version_marco = models.ForeignKey(VersionMarcoEvaluacion, on_delete=models.CASCADE, related_name="dimensiones")
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=255)
    definicion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["version_marco", "orden", "id"]
        unique_together = [("version_marco", "codigo")]

    def __str__(self):
        return f"{self.codigo} {self.nombre}"


class Componente(models.Model):
    """Nivel 2 (36 componentes, código X.Y)."""

    version_marco = models.ForeignKey(VersionMarcoEvaluacion, on_delete=models.CASCADE, related_name="componentes")
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name="componentes")
    codigo = models.CharField(max_length=20)
    codigo_completo = models.CharField(max_length=30)
    nombre = models.CharField(max_length=255)
    definicion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["version_marco", "orden", "id"]
        unique_together = [("version_marco", "codigo_completo"), ("version_marco", "dimension", "codigo")]

    def __str__(self):
        return f"{self.codigo_completo} {self.nombre}"


class CriterioMarco(models.Model):
    """Nivel 3 (77 criterios, código X.Y.Z)."""

    version_marco = models.ForeignKey(VersionMarcoEvaluacion, on_delete=models.CASCADE, related_name="criterios_marco")
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, related_name="criterios_marco")
    codigo = models.CharField(max_length=30)
    codigo_completo = models.CharField(max_length=40)
    nombre = models.TextField()
    definicion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["version_marco", "orden", "id"]
        unique_together = [("version_marco", "codigo_completo"), ("version_marco", "componente", "codigo")]

    def __str__(self):
        return f"{self.codigo_completo} {self.nombre}"


class Estandar(models.Model):
    """Nivel 4 (~210 estándares, código X.Y.Z.W)."""

    version_marco = models.ForeignKey(VersionMarcoEvaluacion, on_delete=models.CASCADE, related_name="estandares")
    criterio_marco = models.ForeignKey(CriterioMarco, on_delete=models.CASCADE, related_name="estandares")
    codigo = models.CharField(max_length=40)
    codigo_completo = models.CharField(max_length=50)
    redaccion = models.TextField()
    tipo_valor = models.CharField(max_length=20, blank=True)
    umbral_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    umbral_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unidad = models.CharField(max_length=50, blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["version_marco", "orden", "id"]
        unique_together = [("version_marco", "codigo_completo"), ("version_marco", "criterio_marco", "codigo")]

    def __str__(self):
        return self.codigo_completo


class IndicadorMarco(models.Model):
    """Nivel 5 (indicadores). En la fuente oficial no llevan código: se identifican por
    estándar + orden de aparición (codigo/codigo_completo son opcionales)."""

    version_marco = models.ForeignKey(VersionMarcoEvaluacion, on_delete=models.CASCADE, related_name="indicadores_marco")
    estandar = models.ForeignKey(Estandar, on_delete=models.CASCADE, related_name="indicadores_marco")
    codigo = models.CharField(max_length=60)
    codigo_completo = models.CharField(max_length=80)
    redaccion_oficial = models.TextField()
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["version_marco", "orden", "id"]
        unique_together = [("version_marco", "codigo_completo"), ("version_marco", "estandar", "codigo")]

    def __str__(self):
        return self.codigo_completo or f"Indicador {self.orden}"


class EvidenciaIndicativa(models.Model):
    """Nivel 6 (evidencias indicativas). En la fuente oficial no llevan código ni
    obligatoriedad declarada: obligatoria permanece en None hasta confirmación."""

    version_marco = models.ForeignKey(
        VersionMarcoEvaluacion, on_delete=models.CASCADE, related_name="evidencias_indicativas"
    )
    indicador_marco = models.ForeignKey(
        IndicadorMarco, on_delete=models.CASCADE, related_name="evidencias_indicativas"
    )
    codigo = models.CharField(max_length=90)
    codigo_completo = models.CharField(max_length=100)
    descripcion = models.TextField()
    orden = models.PositiveIntegerField(default=0)
    obligatoria = models.BooleanField(blank=True, null=True)

    class Meta:
        ordering = ["version_marco", "orden", "id"]
        unique_together = [("version_marco", "codigo_completo"), ("version_marco", "indicador_marco", "codigo")]

    def __str__(self):
        return self.codigo_completo or f"Evidencia {self.orden}"
