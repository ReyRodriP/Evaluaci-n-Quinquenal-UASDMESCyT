from django.db import models


class Periodo(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Criterio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.CASCADE,
        related_name='criterios',
        null=True,
        blank=True
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Indicador(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    criterio = models.ForeignKey(
        Criterio,
        on_delete=models.CASCADE,
        related_name='indicadores'
    )
    obligatorio = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class EstadoAsignacion(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    EN_PROGRESO = 'en_progreso', 'En progreso'
    COMPLETADO = 'completado', 'Completado'
    APROBADO = 'aprobado', 'Aprobado'
    RECHAZADO = 'rechazado', 'Rechazado'
    OBSERVADA = 'observada', 'Observada' 

class Asignacion(models.Model):
    indicador = models.ForeignKey(
        Indicador,
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    departamento = models.ForeignKey(
        'organization.Departamento',
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    periodo = models.ForeignKey(
        Periodo,
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoAsignacion.choices,
        default=EstadoAsignacion.PENDIENTE
    )

    class Meta:
        unique_together = ('indicador', 'departamento', 'periodo')

    def __str__(self):
        return f"{self.indicador} - {self.departamento} ({self.periodo})"
