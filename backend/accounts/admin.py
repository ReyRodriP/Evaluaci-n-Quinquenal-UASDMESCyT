from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .models import Usuario
from .role_permissions import ROLE_PERMISSIONS, get_role_permissions_diff


admin.site.register(Usuario, UserAdmin)


class FixedPermissionsGroupAdmin(BaseGroupAdmin):
    list_display = ('name', 'permissions_status')

    def permissions_status(self, obj):
        if obj.name not in ROLE_PERMISSIONS:
            return format_html(
                '<span style="color:orange;">Rol libre</span>'
            )
        extra, missing = get_role_permissions_diff(obj)
        if not extra and not missing:
            return format_html(
                '<span style="color:green;">✓ Sincronizado</span>'
            )
        parts = []
        if extra:
            parts.append(
                f'<span style="color:red;">{len(extra)} extra</span>'
            )
        if missing:
            parts.append(
                f'<span style="color:orange;">{len(missing)} faltante</span>'
            )
        return format_html(" &nbsp;|&nbsp; ".join(parts))
    permissions_status.short_description = "Permisos"

    def get_fieldsets(self, request, obj=None):
        if obj and obj.name in ROLE_PERMISSIONS:
            return (
                (None, {
                    'fields': ('name',),
                }),
                ('Permisos fijos del rol', {
                    'fields': (),
                    'description': (
                        'Los permisos de este grupo están determinados '
                        'por el rol definido en '
                        '<code>accounts/role_permissions.py</code> '
                        'y se sincronizan automáticamente. '
                        'No pueden editarse manualmente.'
                    ),
                }),
            )
        return super().get_fieldsets(request, obj)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from .role_permissions import sync_group_permissions
        sync_group_permissions(obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.name in ROLE_PERMISSIONS:
            return True
        return super().has_change_permission(request, obj)


admin.site.unregister(Group)
admin.site.register(Group, FixedPermissionsGroupAdmin)