from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_alter_usuario_email_alter_usuario_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usuario",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
    ]
