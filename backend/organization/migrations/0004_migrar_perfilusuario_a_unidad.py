from django.db import migrations


def migrar_perfiles_a_unidades(apps, schema_editor):
    PerfilUsuario = apps.get_model("organization", "PerfilUsuario")
    UnidadOrganizacional = apps.get_model("organization", "UnidadOrganizacional")

    perfiles = PerfilUsuario.objects.filter(unidad_organizacional__isnull=True, departamento__isnull=False)
    for perfil in perfiles.iterator():
        unidad = UnidadOrganizacional.objects.filter(departamento_legacy_id=perfil.departamento_id).first()
        if unidad:
            PerfilUsuario.objects.filter(pk=perfil.pk).update(unidad_organizacional_id=unidad.pk)


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0003_perfilusuario_unidad_organizacional'),
    ]

    operations = [
        migrations.RunPython(migrar_perfiles_a_unidades, migrations.RunPython.noop),
    ]