from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='criterio',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='criterio',
            name='periodo',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='criterios', to='evaluation.periodo'),
        ),
        migrations.AddField(
            model_name='indicador',
            name='activo',
            field=models.BooleanField(default=True),
        ),
    ]
