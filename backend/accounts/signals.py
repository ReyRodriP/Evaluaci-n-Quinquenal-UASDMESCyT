from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from .role_permissions import sync_group_permissions, _re_syncing


@receiver(m2m_changed, sender=Group.permissions.through)
def prevent_manual_permission_change(sender, instance, action, **kwargs):
    if action in ('pre_add', 'pre_remove', 'pre_clear'):
        if instance.pk in _re_syncing:
            return
        raise PermissionError(
            f"Los permisos del grupo '{instance.name}' son fijos "
            f"y no pueden modificarse manualmente."
        )


@receiver(m2m_changed, sender=get_user_model().groups.through)
def sync_permissions_on_group_change(sender, instance, action, pk_set, **kwargs):
    if action != 'post_add':
        return
    for group in Group.objects.filter(pk__in=pk_set):
        sync_group_permissions(group)
