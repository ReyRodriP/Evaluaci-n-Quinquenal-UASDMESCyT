"""
@file role_permissions.py
@brief Definicion de permisos por rol y utilidades de sincronizacion
@details Contiene el diccionario ROLE_PERMISSIONS que mapea cada rol a sus permisos
asignados, junto con funciones para sincronizar y comparar permisos de grupos.
"""
ROLE_PERMISSIONS = {
    'Administrador General': None,
    'Coordinador Quinquenal': None,

    'Responsable Departamental': {
        'evaluation': [
            'view_periodo', 'view_criterio', 'view_indicador',
            'view_asignacion', 'view_historialestado',
        ],
        'evidence': [
            'add_evidencia', 'change_evidencia', 'view_evidencia',
            'add_versionevidencia', 'view_versionevidencia',
            'view_observacion',
        ],
        'evidencias': [
            'add_evidencia', 'change_evidencia', 'view_evidencia',
        ],
        'organization': [
            'view_facultad', 'view_departamento', 'view_perfilusuario',
        ],
        'notificaciones': [
            'view_notificacion', 'change_notificacion',
        ],
    },

    'Revisor Institucional': {
        'evaluation': [
            'view_periodo', 'view_criterio', 'view_indicador',
            'view_asignacion', 'change_asignacion', 'add_asignacion',
            'view_historialestado',
        ],
        'evidence': [
            'view_evidencia', 'view_versionevidencia',
            'add_observacion', 'change_observacion', 'view_observacion',
        ],
        'evidencias': [
            'view_evidencia',
        ],
        'organization': [
            'view_facultad', 'view_departamento', 'view_perfilusuario',
        ],
        'notificaciones': [
            'view_notificacion',
        ],
        'auditoria': [
            'view_auditoria',
        ],
    },

    'Consulta': {
        'evaluation': [
            'view_periodo', 'view_criterio', 'view_indicador',
            'view_asignacion', 'view_historialestado',
        ],
        'evidence': [
            'view_evidencia', 'view_versionevidencia', 'view_observacion',
        ],
        'evidencias': [
            'view_evidencia',
        ],
        'organization': [
            'view_facultad', 'view_departamento', 'view_perfilusuario',
        ],
        'notificaciones': [
            'view_notificacion',
        ],
    },

    'Evaluador Externo': {
        'evaluation': [
            'view_periodo', 'view_criterio', 'view_indicador',
            'view_asignacion', 'view_historialestado',
        ],
        'evidence': [
            'view_evidencia', 'view_versionevidencia',
            'add_observacion', 'view_observacion',
        ],
        'evidencias': [
            'view_evidencia',
        ],
        'organization': [
            'view_facultad', 'view_departamento', 'view_perfilusuario',
        ],
        'notificaciones': [
            'view_notificacion',
        ],
    },
}


_re_syncing = set()

OUR_APP_LABELS = [
    'accounts', 'auditoria', 'evaluation', 'evidence',
    'evidencias', 'notificaciones', 'organization',
]


def sync_group_permissions(group):
    """
    @brief Sincroniza los permisos de un grupo segun ROLE_PERMISSIONS
    @param group Instancia del modelo Group cuyos permisos se sincronizan
    @return None
    @details Asigna al grupo los permisos definidos en ROLE_PERMISSIONS.
    Si el rol tiene None, asigna todos los permisos de las apps del sistema.
    """
    if group.name not in ROLE_PERMISSIONS:
        return

    if group.pk in _re_syncing:
        return

    from django.contrib.auth.models import Permission

    _re_syncing.add(group.pk)
    try:
        role_perms = ROLE_PERMISSIONS[group.name]

        if role_perms is None:
            group.permissions.set(
                Permission.objects.filter(
                    content_type__app_label__in=OUR_APP_LABELS
                )
            )
            return

        perm_ids = []
        for app_label, codenames in role_perms.items():
            perm_ids.extend(
                Permission.objects.filter(
                    content_type__app_label=app_label,
                    codename__in=codenames
                ).values_list('id', flat=True)
            )

        group.permissions.set(perm_ids)
    finally:
        _re_syncing.discard(group.pk)


def get_role_permissions_diff(group):
    """
    @brief Obtiene la diferencia entre los permisos actuales y esperados de un grupo
    @param group Instancia del modelo Group a comparar
    @return Tupla (permisos_extra, permisos_faltantes) como listas de objetos Permission
    @details Compara los permisos actuales del grupo con los definidos en ROLE_PERMISSIONS
    y retorna los que sobran y los que faltan.
    """
    if group.name not in ROLE_PERMISSIONS:
        return [], []

    from django.contrib.auth.models import Permission

    role_perms = ROLE_PERMISSIONS[group.name]

    if role_perms is None:
        expected = set(
            Permission.objects.filter(
                content_type__app_label__in=OUR_APP_LABELS
            )
        )
    else:
        perm_ids = []
        for app_label, codenames in role_perms.items():
            perm_ids.extend(
                Permission.objects.filter(
                    content_type__app_label=app_label,
                    codename__in=codenames
                ).values_list('id', flat=True)
            )
        expected = set(Permission.objects.filter(id__in=perm_ids))

    current = set(group.permissions.all())
    extra = current - expected
    missing = expected - current
    return list(extra), list(missing)
