from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0002_criterio_activo_criterio_periodo_indicador_activo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asignacion',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('en_progreso', 'En progreso'), ('completado', 'Completado'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado'), ('observada', 'Observada')], default='pendiente', max_length=20),
        ),
    ]
