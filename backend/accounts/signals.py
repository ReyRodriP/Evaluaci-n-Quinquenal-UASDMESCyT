"""
@file signals.py
@brief Signals para sincronizar permisos de grupos en el modelo de usuario
@details Implementa signal handlers que previenen la modificacion manual de permisos
y sincronizan los permisos cuando un usuario es asignado a un grupo.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .role_permissions import _re_syncing, sync_group_permissions


@receiver(m2m_changed, sender=Group.permissions.through)
def prevent_manual_permission_change(sender, instance, action, **kwargs):
    """
    @brief Previene la modificacion manual de permisos de un grupo
    @param sender Clase del modelo que emite la senal
    @param instance Instancia del grupo cuyos permisos se estan modificando
    @param action Tipo de accion M2M (pre_add, pre_remove, pre_clear)
    @return None
    @raises PermissionError Si se intenta modificar permisos manualmente
    """
    if action in ("pre_add", "pre_remove", "pre_clear"):
        if instance.pk in _re_syncing:
            return
        raise PermissionError(
            f"Los permisos del grupo '{instance.name}' son fijos y no pueden modificarse manualmente."
        )


@receiver(m2m_changed, sender=get_user_model().groups.through)
def sync_permissions_on_group_change(sender, instance, action, pk_set, **kwargs):
    """
    @brief Sincroniza permisos cuando un usuario es asignado a un grupo
    @param sender Clase del modelo que emite la senal
    @param instance Instancia del usuario al que se le asigna el grupo
    @param action Tipo de accion M2M (post_add)
    @param pk_set Conjunto de PKs de grupos asignados
    @return None
    """
    if action != "post_add":
        return
    for group in Group.objects.filter(pk__in=pk_set):
        sync_group_permissions(group)
