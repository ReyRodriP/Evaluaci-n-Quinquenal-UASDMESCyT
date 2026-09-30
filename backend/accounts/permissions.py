"""
@file permissions.py
@brief Permisos personalizados para el control de acceso basado en roles
@details Define permisos por rol, funciones de filtrado por departamento y facultad,
y clases de permisos personalizados para el sistema de evaluacion quinquenal.
"""

from django.db.models import Q
from rest_framework.permissions import SAFE_METHODS, BasePermission, DjangoModelPermissions

from organization.models import AmbitoEvaluacion, Facultad, PerfilUsuario, UnidadOrganizacional

ROLES_SIN_RESTRICCION = {"Administrador General", "Coordinador Quinquenal"}

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


def es_evaluador_externo(request):
    return "Evaluador Externo" in _grupos_usuario(request.user)


def ambitos_activos(usuario):
    return AmbitoEvaluacion.objects.filter(usuario=usuario, activo=True).select_related(
        "unidad_organizacional", "periodo"
    )


def periodos_autorizados(request):
    return list(ambitos_activos(request.user).values_list("periodo_id", flat=True).distinct())


def _unidades_del_ambito(unidad_id):
    unidades = {unidad_id}
    padres = {unidad_id}
    while padres:
        hijos = set(
            UnidadOrganizacional.objects.filter(unidad_padre_id__in=padres).values_list("pk", flat=True)
        )
        hijos -= unidades
        unidades.update(hijos)
        padres = hijos
    return unidades


def _filtrar_evaluador_externo(queryset, request):
    ambitos = list(ambitos_activos(request.user))
    if not ambitos:
        return queryset.none()

    model_label = queryset.model._meta.label
    scope = {
        "evaluation.Asignacion": ("periodo_id", "unidad_responsable_id", "estado"),
        "evaluation.Criterio": (
            "periodo_id",
            "indicadores__asignaciones__unidad_responsable_id",
            "indicadores__asignaciones__estado",
        ),
        "evaluation.Indicador": (
            "criterio__periodo_id",
            "asignaciones__unidad_responsable_id",
            "asignaciones__estado",
        ),
        "evaluation.HistorialEstado": (
            "asignacion__periodo_id",
            "asignacion__unidad_responsable_id",
            "asignacion__estado",
        ),
        "evidence.Evidencia": ("asignacion__periodo_id", "asignacion__unidad_responsable_id", "asignacion__estado"),
        "evidencias.Evidencia": ("asignacion__periodo_id", "asignacion__unidad_responsable_id", "asignacion__estado"),
        "evidence.VersionEvidencia": (
            "evidencia__asignacion__periodo_id",
            "evidencia__asignacion__unidad_responsable_id",
            "evidencia__asignacion__estado",
        ),
        "evidence.Observacion": None,
    }
    if model_label not in scope:
        return queryset.none()
    if scope[model_label] is None:
        return queryset.none()

    period_lookup, unit_lookup, state_lookup = scope[model_label]
    allowed_scopes = Q(pk__in=[])  # Empty disjunction before adding each authorized unit-period pair.
    for ambito in ambitos:
        allowed_scopes |= Q(
            **{
                period_lookup: ambito.periodo_id,
                f"{unit_lookup}__in": _unidades_del_ambito(ambito.unidad_organizacional_id),
            }
        )
    return queryset.filter(allowed_scopes, **{state_lookup: "aprobado"}).distinct()


def filtrar_por_rol(queryset, request, dept_field="departamento"):
    """
    @brief Filtra un queryset segun el rol y departamento del usuario
    @param queryset Queryset a filtrar
    @param request Request HTTP con el usuario autenticado
    @param dept_field Nombre del campo de departamento en el queryset
    @return Queryset filtrado segun las reglas de negocio del rol
    @details Administrador General y Coordinador Quinquenal ven todo.
    Evaluador Externo solo ve registros aprobados de su unidad y períodos asignados.
    Responsable Departamental solo ve su departamento.
    Revisor Institucional y Consulta ven toda su facultad.
    """
    user = request.user
    if user.is_superuser:
        return queryset

    grupos = _grupos_usuario(user)
    if ROLES_SIN_RESTRICCION & grupos:
        return queryset
    if "Evaluador Externo" in grupos:
        return _filtrar_evaluador_externo(queryset, request)

    if "unidad_responsable" in dept_field:
        permitidas = unidades_organizacionales_permitidas(request)
        if permitidas is None:
            return queryset
        return queryset.filter(**{f"{dept_field}_id__in": permitidas})

    departamentos = departamentos_permitidos(request)
    if departamentos is None:
        return queryset
    if queryset.model._meta.label == "organization.Departamento" and dept_field == "departamento":
        return queryset.filter(pk__in=departamentos)
    return queryset.filter(**{f"{dept_field}_id__in": departamentos})


def unidades_organizacionales_permitidas(request):
    user = request.user
    if user.is_superuser:
        return None

    grupos = _grupos_usuario(user)
    if ROLES_SIN_RESTRICCION & grupos:
        return None

    if "Evaluador Externo" in grupos:
        unidades = set()
        for ambito in ambitos_activos(user).only("unidad_organizacional_id"):
            unidades.update(_unidades_del_ambito(ambito.unidad_organizacional_id))
        return sorted(unidades)

    try:
        perfil = user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        return []

    from organization.models import UnidadOrganizacional

    unidad = perfil.unidad_organizacional
    if unidad is None:
        return []

    if "Revisor Institucional" in grupos or "Consulta" in grupos:
        raiz = unidad
        ancestro = unidad
        while ancestro:
            if ancestro.tipo.nombre.casefold() == "facultad":
                raiz = ancestro
                break
            ancestro = ancestro.unidad_padre

        permitidas = [raiz.pk]
        padres = [raiz.pk]
        while padres:
            padres = list(
                UnidadOrganizacional.objects.filter(unidad_padre_id__in=padres).values_list("pk", flat=True)
            )
            permitidas.extend(padres)
        return permitidas

    return [unidad.pk]


def departamentos_permitidos(request):
    """
    @brief Devuelve una lista de IDs de departamento que el usuario puede ver
    @param request Request HTTP con el usuario autenticado
    @return Lista de IDs de departamento o None si tiene acceso total
    @details Retorna None para superuser y roles sin restriccion,
    lista de IDs filtrada por facultad para revisores y consulta,
    o lista vacia si no tiene perfil o departamento asignado.
    """
    from organization.models import UnidadOrganizacional

    unidades = unidades_organizacionales_permitidas(request)
    if unidades is None:
        return None
    return list(
        UnidadOrganizacional.objects.filter(pk__in=unidades)
        .exclude(departamento_legacy_id__isnull=True)
        .values_list("departamento_legacy_id", flat=True)
    )


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

    if "Evaluador Externo" in grupos:
        unidades_ids = unidades_organizacionales_permitidas(request)
        if not unidades_ids:
            return []
        unidades = UnidadOrganizacional.objects.filter(pk__in=unidades_ids).select_related(
            "tipo", "unidad_padre"
        )
        nombres_facultades = set()
        for unidad in unidades:
            ancestro = unidad
            while ancestro:
                if ancestro.tipo.nombre.casefold() == "facultad":
                    nombres_facultades.add(ancestro.nombre)
                    break
                ancestro = ancestro.unidad_padre
        return list(Facultad.objects.filter(nombre__in=nombres_facultades).values_list("pk", flat=True))

    try:
        unidad = user.perfilusuario.unidad_organizacional
    except PerfilUsuario.DoesNotExist:
        return []

    while unidad:
        if unidad.tipo.nombre.casefold() == "facultad":
            return list(Facultad.objects.filter(nombre=unidad.nombre).values_list("pk", flat=True)[:1])
        unidad = unidad.unidad_padre
    return []


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

    def has_permission(self, request, view):
        if (
            request.user
            and request.user.is_authenticated
            and not request.user.is_superuser
            and es_evaluador_externo(request)
            and not (ROLES_SIN_RESTRICCION & _grupos_usuario(request.user))
        ):
            return request.method in SAFE_METHODS
        return super().has_permission(request, view)


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
