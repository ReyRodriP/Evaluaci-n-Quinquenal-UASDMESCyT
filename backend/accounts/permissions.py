"""
@file permissions.py
@brief Permisos personalizados para el control de acceso basado en roles
@details Define permisos por rol, funciones de filtrado por departamento y facultad,
y clases de permisos personalizados para el sistema de evaluacion quinquenal.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission, DjangoModelPermissions

from organization.models import PerfilUsuario

ROLES_SIN_RESTRICCION = {"Administrador General", "Coordinador Quinquenal", "Evaluador Externo"}

ROLES_REPORTES = {"Administrador General", "Coordinador Quinquenal", "Revisor Institucional"}

ROLES_REPORTES_COMPLETOS = {"Administrador General", "Coordinador Quinquenal"}

ROLES_AUDITORIA = {"Administrador General", "Coordinador Quinquenal"}


def _grupos_usuario(user):
    """
    @brief Obtiene el conjunto de nombres de grupos de un usuario
    @param user Instancia del modelo User
    @return Conjunto de strings con los nombres de los grupos del usuario
    """
    return set(user.groups.values_list("name", flat=True))


def filtrar_por_rol(queryset, request, dept_field="departamento"):
    """
    @brief Filtra un queryset segun el rol y departamento del usuario
    @param queryset Queryset a filtrar
    @param request Request HTTP con el usuario autenticado
    @param dept_field Nombre del campo de departamento en el queryset
    @return Queryset filtrado segun las reglas de negocio del rol
    @details Administrador General, Coordinador Quinquenal y Evaluador Externo
    ven todo. Responsable Departamental solo ve su departamento.
    Revisor Institucional y Consulta ven toda su facultad.
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

    if "Revisor Institucional" in grupos or "Consulta" in grupos:
        facultad_id = perfil.departamento.facultad_id
        return queryset.filter(**{f"{dept_field}__facultad_id": facultad_id})

    return queryset.filter(**{f"{dept_field}_id": perfil.departamento_id})


def departamentos_permitidos(request):
    """
    @brief Devuelve una lista de IDs de departamento que el usuario puede ver
    @param request Request HTTP con el usuario autenticado
    @return Lista de IDs de departamento o None si tiene acceso total
    @details Retorna None para superuser y roles sin restriccion,
    lista de IDs filtrada por facultad para revisores y consulta,
    o lista vacia si no tiene perfil o departamento asignado.
    """
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

    if "Revisor Institucional" in grupos or "Consulta" in grupos:
        from organization.models import Departamento

        return list(
            Departamento.objects.filter(facultad_id=perfil.departamento.facultad_id).values_list("pk", flat=True)
        )

    return [perfil.departamento_id]


def facultades_permitidas(request):
    """
    @brief Devuelve una lista de IDs de facultad que el usuario puede ver
    @param request Request HTTP con el usuario autenticado
    @return Lista de IDs de facultad o None si tiene acceso total
    @details Retorna None para superuser y roles sin restriccion,
    o una lista con el ID de la facultad del departamento del usuario.
    """
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

    return [perfil.departamento.facultad_id]


class CustomModelPermissions(DjangoModelPermissions):
    """
    @class CustomModelPermissions
    @brief Permisos de modelo personalizados que incluyen permisos de vista
    @details Extiende DjangoModelPermissions para agregar permisos de lectura
    (GET, OPTIONS, HEAD) al mapa de permisos por metodo HTTP.
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class IsAdminGroup(BasePermission):
    """
    @class IsAdminGroup
    @brief Permiso que permite acceso solo a administradores generales
    @details Verifica que el usuario este autenticado y pertenezca al grupo
    'Administrador General' o sea superuser.
    """

    def has_permission(self, request, view):
        """
        @brief Verifica si el usuario tiene permiso de administrador
        @param request Request HTTP del cliente
        @param view Vista actual
        @return True si es superuser o pertenece al grupo Administrador General
        """
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="Administrador General").exists()


class IsAdminOrReadOnly(BasePermission):
    """
    @class IsAdminOrReadOnly
    @brief Permiso que permite lectura a todos y escritura solo a administradores
    @details Los usuarios autenticados pueden leer (GET, HEAD, OPTIONS).
    Solo los administradores pueden crear, modificar o eliminar.
    """

    def has_permission(self, request, view):
        """
        @brief Verifica si el usuario tiene permiso para la accion solicitada
        @param request Request HTTP del cliente
        @param view Vista actual
        @return True si es metodo seguro o el usuario es administrador
        """
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.user.is_superuser:
            return True

        return request.user.groups.filter(name="Administrador General").exists()


class PuedeVerReportes(BasePermission):
    """
    @class PuedeVerReportes
    @brief Permiso para acceder a reportes del sistema
    @details Permite acceso a usuarios con roles de Administrador General,
    Coordinador Quinquenal o Revisor Institucional.
    """

    def has_permission(self, request, view):
        """
        @brief Verifica si el usuario puede ver reportes
        @param request Request HTTP del cliente
        @param view Vista actual
        @return True si es superuser o tiene un rol de reportes
        """
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return bool(_grupos_usuario(request.user) & ROLES_REPORTES)


class PuedeVerReportesCompletos(BasePermission):
    """
    @class PuedeVerReportesCompletos
    @brief Permiso para acceder a reportes completos del sistema
    @details Permite acceso solo a Administrador General y Coordinador Quinquenal.
    """

    def has_permission(self, request, view):
        """
        @brief Verifica si el usuario puede ver reportes completos
        @param request Request HTTP del cliente
        @param view Vista actual
        @return True si es superuser o tiene rol de reportes completos
        """
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return bool(_grupos_usuario(request.user) & ROLES_REPORTES_COMPLETOS)


class PuedeVerAuditoria(BasePermission):
    """
    @class PuedeVerAuditoria
    @brief Permiso para acceder al registro de auditoria
    @details Permite acceso solo a Administrador General y Coordinador Quinquenal.
    """

    def has_permission(self, request, view):
        """
        @brief Verifica si el usuario puede ver registros de auditoria
        @param request Request HTTP del cliente
        @param view Vista actual
        @return True si es superuser o tiene rol de auditoria
        """
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return bool(_grupos_usuario(request.user) & ROLES_AUDITORIA)
