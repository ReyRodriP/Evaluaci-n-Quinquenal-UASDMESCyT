from django.db import migrations


def seed_initial_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    admin_group, _ = Group.objects.get_or_create(name='Administrador General')
    consulta_group, _ = Group.objects.get_or_create(name='Consulta')

    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)

    consulta_group.permissions.clear()


class Migration(migrations.Migration):

    dependencies = [
    ('accounts', '0001_initial'),
    ('organization', '0001_initial'),
    ('evaluation', '0001_initial'),
]

    operations = [
        migrations.RunPython(seed_initial_permissions),
    ]
