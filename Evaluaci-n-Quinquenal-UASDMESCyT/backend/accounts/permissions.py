from rest_framework.permissions import DjangoModelPermissions, BasePermission, SAFE_METHODS
from organization.models import PerfilUsuario

ROLES_SIN_RESTRICCION = {'Administrador General', 'Coordinador Quinquenal'}


def _grupos_usuario(user):
    return set(user.groups.values_list('name', flat=True))


def filtrar_por_rol(queryset, request, dept_field='departamento'):
    """
    Filtra un queryset según el rol y departamento del usuario.

    - Administrador General / Coordinador Quinquenal: sin filtro.
    - Responsable Departamental: solo su departamento.
    - Revisor Institucional: su facultad completa.
    - Otros (Consulta, Evaluador Externo): su departamento.
    """
    user = request.user
    if user.is_superuser:
        return queryset

    grupos = _grupos_usuario(user)
    if ROLES_SIN_RESTRICCION & grupos:
        return queryset

    try:
        perfil = user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        return queryset.none()

    if not perfil.departamento:
        return queryset.none()

    if 'Revisor Institucional' in grupos:
        facultad_id = perfil.departamento.facultad_id
        return queryset.filter(**{f'{dept_field}__facultad_id': facultad_id})

    return queryset.filter(**{f'{dept_field}_id': perfil.departamento_id})


def departamentos_permitidos(request):
    """Devuelve una lista de IDs de departamento que el usuario puede ver."""
    user = request.user
    if user.is_superuser:
        return None

    grupos = _grupos_usuario(user)
    if ROLES_SIN_RESTRICCION & grupos:
        return None

    try:
        perfil = user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        return []

    if not perfil.departamento:
        return []

    if 'Revisor Institucional' in grupos:
        from organization.models import Departamento
        return list(Departamento.objects.filter(
            facultad_id=perfil.departamento.facultad_id
        ).values_list('pk', flat=True))

    return [perfil.departamento_id]


class CustomModelPermissions(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class IsAdminGroup(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name='Administrador General').exists()


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        return request.user.groups.filter(name='Administrador General').exists()
