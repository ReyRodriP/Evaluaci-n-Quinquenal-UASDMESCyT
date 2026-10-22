import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("evaluation", "0006_periodo_periodo_fecha_fin_posterior_inicio_and_more"),
        ("catalogo", "0002_alter_criteriomarco_nombre"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="periodo", name="version_marco",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="periodos", to="catalogo.versionmarcoevaluacion"),
        ),
        migrations.AlterField(
            model_name="asignacion", name="indicador",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="asignaciones", to="evaluation.indicador"),
        ),
        migrations.AddField(
            model_name="asignacion", name="indicador_marco",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="asignaciones", to="catalogo.indicadormarco"),
        ),
        migrations.AddField(
            model_name="asignacion", name="encargado",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="asignaciones_encargadas", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name="asignacion",
            constraint=models.CheckConstraint(condition=models.Q(indicador__isnull=False, indicador_marco__isnull=True) | models.Q(indicador__isnull=True, indicador_marco__isnull=False), name="asignacion_origen_unico"),
        ),
        migrations.AddConstraint(
            model_name="asignacion",
            constraint=models.UniqueConstraint(fields=("indicador_marco", "unidad_responsable", "periodo"), condition=models.Q(indicador_marco__isnull=False), name="asignacion_marco_unidad_periodo_unica"),
        ),
    ]
