# Sistema de Gestión de Evidencias — Backend

## Primeros pasos

`ash
py -m pip install virtualenv
virtualenv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
`

## Superusuario actual

- Username: omori
- Email: suicidaloco@gmail.com
- Password: 12345678

---

## Roles y permisos

### Arquitectura general

El sistema usa el sistema nativo de **Groups** y **Permissions** de Django combinado con reglas de filtrado por departamento (ccounts/permissions.py) y una definición fija de permisos por rol (ccounts/role_permissions.py).

### Roles definidos

| Rol | Descripción |
|-----|-------------|
| Administrador General | Acceso total al sistema |
| Coordinador Quinquenal | Acceso total al sistema |
| Responsable Departamental | Gestiona evidencias de su departamento |
| Revisor Institucional | Revisa, aprueba/rechaza, agrega observaciones |
| Evaluador Externo | Consulta evidencias aprobadas, revisa indicadores |
| Consulta | Solo lectura |

### Archivos clave

#### accounts/role_permissions.py
Define los permisos fijos en ROLE_PERMISSIONS. Cada entrada mapea un grupo a {app_label: [codenames]}. None = todos los permisos.

Funciones:
- sync_group_permissions(group) — Reemplaza permisos del grupo según ROLE_PERMISSIONS.
- get_role_permissions_diff(group) — Devuelve (extras, faltantes).

#### accounts/signals.py
Dos señales m2m_changed:
1. prevent_manual_permission_change — Bloquea modificaciones manuales en Group.permissions.
2. sync_permissions_on_group_change — Al asignar un grupo a un usuario, sincroniza permisos automáticamente.

#### accounts/permissions.py
- CustomModelPermissions — POST→add_, PUT/PATCH→change_, DELETE→delete_, GET→view_.
- filtrar_por_rol(qs, request, dept_field) — Filtra por facultad/departamento según el rol.
- departamentos_permitidos(request) — Lista de IDs de depto accesibles (None = sin restricción).

#### accounts/admin.py
FixedPermissionsGroupAdmin — Admin de grupos con permisos de solo lectura y sincronización automática al guardar.

#### accounts/serializers.py
UsuarioProfileSerializer (usado en login) devuelve: id, username, email, is_superuser, groups, rol, permisos.

### Asignar rol

1. Admin de Django → Usuarios → seleccionar → Groups → guardar.
2. API: PUT /api/profile/ con {"group_ids": [1, 2]}

### Comandos

- python manage.py sync_roles — Sincroniza todos los grupos.
- python manage.py check_usuario <username> — Diagnóstico.

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/login | Login (token + user con grupos/permisos) |
| POST | /api/register | Registro |
| GET | /api/me | Usuario actual |
| PUT/PATCH | /api/profile | Actualizar perfil |
| POST | /api/change_password | Cambiar contraseña |
| GET/POST/PUT/DELETE | /api/usuarios/ | CRUD usuarios |
| GET/POST/PUT/DELETE | /api/roles/ | CRUD roles |
| GET | /api/permisos/ | Listar permisos |
| GET/POST/PUT/DELETE | /api/facultades/ | CRUD facultades |
| GET/POST/PUT/DELETE | /api/departamentos/ | CRUD departamentos |
| GET/POST/PUT/DELETE | /api/perfiles/ | CRUD perfiles |
| GET/POST/PUT/DELETE | /api/periodos/ | CRUD períodos |
| GET/POST/PUT/DELETE | /api/criterios/ | CRUD criterios |
| GET/POST/PUT/DELETE | /api/indicadores/ | CRUD indicadores |
| GET/POST/PUT/DELETE | /api/asignaciones/ | CRUD asignaciones |
| GET/POST/DELETE | /api/evidencias/ | CRUD evidencias |
| GET | /api/evidencias/{id}/descargar/ | Descargar archivo |
| GET | /api/auditoria/ | Listar bitácora |
| GET | /api/search/?q= | Búsqueda global |
| GET | /api/dashboard/resumen/ | KPIs del dashboard |
| GET | /api/dashboard/avance/ | Avance por facultad |
| GET/PATCH | /api/notificaciones/ | Notificaciones |

## Permisos por rol

### Administrador General / Coordinador Quinquenal
Todos los permisos de: accounts, auditoria, evaluation, evidence, evidencias, notificaciones, organization

### Responsable Departamental
evaluation: view_periodo, view_criterio, view_indicador, view_asignacion, view_historialestado
evidence: add_evidencia, change_evidencia, view_evidencia, add_versionevidencia, view_versionevidencia, view_observacion
evidencias: add_evidencia, change_evidencia, view_evidencia
organization: view_facultad, view_departamento, view_perfilusuario
notificaciones: view_notificacion, change_notificacion

### Revisor Institucional
evaluation: view_periodo, view_criterio, view_indicador, view_asignacion, change_asignacion, add_asignacion, view_historialestado
evidence: view_evidencia, view_versionevidencia, add_observacion, change_observacion, view_observacion
evidencias: view_evidencia
organization: view_facultad, view_departamento, view_perfilusuario
notificaciones: view_notificacion
auditoria: view_auditoria

### Consulta
evaluation: view_periodo, view_criterio, view_indicador, view_asignacion, view_historialestado
evidence: view_evidencia, view_versionevidencia, view_observacion
evidencias: view_evidencia
organization: view_facultad, view_departamento, view_perfilusuario
notificaciones: view_notificacion

### Evaluador Externo
evaluation: view_periodo, view_criterio, view_indicador, view_asignacion, view_historialestado
evidence: view_evidencia, view_versionevidencia, add_observacion, view_observacion
evidencias: view_evidencia
organization: view_facultad, view_departamento, view_perfilusuario
notificaciones: view_notificacion
