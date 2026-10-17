"""Permisos de la API de vinculación.

Matriz efectiva (sin asignar permisos a grupos; eso es una fase independiente):
- Lectura: IsAuthenticated + view_correspondencia (CustomModelPermissions) y
  alcance del origen operativo aplicado en el queryset (ocultación → 404).
- Escritura (crear/confirmar/rechazar/desconfirmar): superuser o grupos de
  ROLES_SIN_RESTRICCION (Administrador General, Coordinador Quinquenal) además
  del permiso de modelo correspondiente (add para crear, change para transiciones).
- Evaluador Externo: solo métodos seguros (heredado de CustomModelPermissions).
- Anónimo: 401 (IsAuthenticated).
"""

from rest_framework.permissions import SAFE_METHODS

from accounts.permissions import CustomModelPermissions, ROLES_SIN_RESTRICCION, _grupos_usuario

ACCIONES_TRANSICION = {"confirmar", "rechazar", "desconfirmar"}


class PermisosCorrespondencia(CustomModelPermissions):
    """Permisos de modelo acoplados a la acción del ViewSet de Correspondencia.

    A diferencia de CustomModelPermissions (que permite métodos seguros al
    Evaluador Externo sin view_correspondencia), aquí GET/HEAD/OPTIONS exigen
    el permiso de vista del modelo de forma explícita para todos los roles,
    incluido el Evaluador Externo. Tener view_correspondencia no autoriza a
    consultar cualquier correspondencia: el alcance por unidad, período y
    ámbito del origen se aplica después en las vistas.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            model_cls = self._queryset(view).model
            return user.has_perm(f"{model_cls._meta.app_label}.view_{model_cls._meta.model_name}")
        if user.is_superuser:
            return True
        if not (ROLES_SIN_RESTRICCION & _grupos_usuario(user)):
            return False
        model_cls = self._queryset(view).model
        codename = "change" if getattr(view, "action", None) in ACCIONES_TRANSICION else "add"
        return user.has_perm(f"{model_cls._meta.app_label}.{codename}_{model_cls._meta.model_name}")
