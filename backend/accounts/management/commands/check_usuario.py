from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnostica permisos y perfil de un usuario'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str)

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Usuario "{username}" no existe'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f'=== Usuario: {user.username} ==='))
        self.stdout.write(f'  Superuser: {user.is_superuser}')
        self.stdout.write(f'  Email: {user.email}')

        grupos = list(user.groups.all())
        self.stdout.write(f'\n  Grupos ({len(grupos)}):')
        for g in grupos:
            self.stdout.write(f'    - {g.name} ({g.permissions.count()} permisos)')
            for p in g.permissions.all().order_by('content_type__app_label', 'codename'):
                self.stdout.write(f'        {p.content_type.app_label}.{p.codename}')

        try:
            perfil = user.perfilusuario
            self.stdout.write(f'\n  PerfilUsuario: OK')
            if perfil.departamento:
                self.stdout.write(f'    Departamento: {perfil.departamento.nombre} (ID {perfil.departamento_id})')
                self.stdout.write(f'    Facultad: {perfil.departamento.facultad.nombre}')
            else:
                self.stdout.write(self.style.WARNING('    Departamento: NO ASIGNADO'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n  PerfilUsuario: NO EXISTE ({e})'))

        total_assign = user.groups.count()
        self.stdout.write(f'\n  Resumen: {total_assign} grupo(s), permisos directos: {user.user_permissions.count()}')
        self.stdout.write(self.style.SUCCESS('\nHecho.'))
