import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organization", "0007_remove_perfilusuario_periodos_autorizados_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AmbitoRevision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("activo", models.BooleanField(default=True)),
                ("fecha_asignacion", models.DateTimeField(auto_now_add=True)),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ambitos_revision", to=settings.AUTH_USER_MODEL)),
                ("unidad_organizacional", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ambitos_revision", to="organization.unidadorganizacional")),
                ("periodo", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ambitos_revision", to="evaluation.periodo")),
            ],
            options={
                "ordering": ["usuario__username", "periodo__fecha_inicio", "unidad_organizacional__nombre"],
                "constraints": [models.UniqueConstraint(fields=("usuario", "unidad_organizacional", "periodo"), name="ambito_revision_usuario_unidad_periodo_unico")],
            },
        ),
    ]
