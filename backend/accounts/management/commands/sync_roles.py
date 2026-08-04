from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.role_permissions import ROLE_PERMISSIONS, sync_group_permissions


class Command(BaseCommand):
    help = 'Sincroniza los permisos de todos los grupos definidos en ROLE_PERMISSIONS'

    def handle(self, *args, **options):
        for role_name in ROLE_PERMISSIONS:
            group, created = Group.objects.get_or_create(name=role_name)
            sync_group_permissions(group)
            status = 'creado' if created else 'actualizado'
            self.stdout.write(
                self.style.SUCCESS(f'  {group.name}: {group.permissions.count()} permisos ({status})')
            )
        self.stdout.write(self.style.SUCCESS('\nSincronización completa.'))
