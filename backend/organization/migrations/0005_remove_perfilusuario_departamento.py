from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0004_migrar_perfilusuario_a_unidad'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='perfilusuario',
            name='departamento',
        ),
    ]