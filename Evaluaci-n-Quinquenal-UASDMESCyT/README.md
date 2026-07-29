# Sistema de Gestión de Evidencias para la Evaluación Quinquenal UASD–MESCyT

Plataforma web para centralizar, administrar y dar seguimiento a las evidencias requeridas durante los procesos de evaluación institucional de la Universidad Autónoma de Santo Domingo (UASD) ante el Ministerio de Educación Superior, Ciencia y Tecnología (MESCyT).

## Tech Stack

| Capa       | Tecnología          | Versión  |
|------------|---------------------|----------|
| Backend    | Python + Django     | 6.0.5    |
| API        | Django REST Framework | -       |
| Frontend   | Angular             | 20.3     |
| Lenguaje   | TypeScript          | 5.9      |
| BD (dev)   | SQLite3             | -        |
| Auth       | Token Authentication | -       |

## Estructura del Proyecto

```
monografico/
├── backend/                           # Django project
│   ├── accounts/                      # Autenticación y usuarios
│   ├── auditoria/                     # Bitácora de auditoría
│   ├── evaluacionQuinquenal/          # Config del proyecto Django
│   ├── evaluation/                    # Períodos, criterios, indicadores, asignaciones
│   ├── evidencias/                    # Gestión de evidencias (core)
│   ├── notificaciones/                # Notificaciones internas
│   ├── organization/                  # Facultades, departamentos, perfiles
│   ├── media/                         # Archivos subidos (evidencias)
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   └── evaluacion-quinquenal-front/   # Angular standalone project
│       └── src/app/
│           ├── core/                  # Modelos, servicios, guards, interceptors
│           ├── features/              # Páginas por módulo
│           │   ├── auth/              # Login, registro
│           │   ├── dashboard/         # Tablero principal
│           │   ├── usuarios/          # CRUD usuarios
│           │   ├── facultades/        # CRUD facultades y departamentos
│           │   ├── periodos/          # CRUD períodos
│           │   ├── criterios/         # CRUD criterios
│           │   ├── indicadores/       # CRUD indicadores
│           │   ├── asignaciones/      # CRUD asignaciones
│           │   ├── evidencias/        # Subida/descarga/lista de evidencias
│           │   └── auditoria/         # Bitácora de auditoría
│           ├── layouts/               # AdminLayout y AuthLayout
│           └── shared/                # Sidebar y Navbar
│
├── plan.md                            # Documento de planificación del proyecto
└── README.md
```

## Funcionalidades

### Módulos del Sistema

1. **Autenticación y Usuarios**
   - Login/registro con token
   - Perfil de usuario, cambio de contraseña
   - Roles y permisos (basado en grupos de Django)

2. **Organización**
   - CRUD de facultades
   - CRUD de departamentos (por facultad)
   - Perfiles de usuario por departamento

3. **Evaluación**
   - Períodos de evaluación
   - Criterios por período
   - Indicadores por criterio
   - Asignaciones (indicador + departamento + período) con flujo de estados: pendiente → en_progreso → completado → aprobado/rechazado

4. **Gestión de Evidencias** (core)
   - Subida de archivos (PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF, TXT, ZIP, RAR; máx. 50MB)
   - Versionado automático por asignación
   - Descarga de documentos
   - Filtro por asignación

5. **Auditoría**
   - Registro automático de todas las operaciones CRUD
   - Consulta de bitácora con fecha, usuario, acción y descripción

6. **Notificaciones**
   - Notificaciones automáticas al asignar indicadores
   - Notificaciones al cambiar estado de asignaciones

7. **Dashboard**
   - Estadísticas generales del sistema
   - Conteo de usuarios, facultades, departamentos, períodos, criterios, indicadores, asignaciones, evidencias

## Instalación y Ejecución

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend/evaluacion-quinquenal-front
npm install --legacy-peer-deps
npm start
```

El backend corre en `http://127.0.0.1:8000` y el frontend en `http://localhost:4200`.

### Superusuario por defecto

```
Username: mrPopoMaster
Email: popomrMaster001@gmail.com
Password: 12345678
```

## API Endpoints

| Método | Endpoint                     | Descripción                     |
|--------|------------------------------|---------------------------------|
| POST   | `/api/login`                 | Iniciar sesión                  |
| POST   | `/api/register`              | Registrarse                     |
| GET    | `/api/me`                    | Usuario actual                  |
| PUT    | `/api/profile`               | Actualizar perfil               |
| POST   | `/api/change_password`       | Cambiar contraseña              |
| GET/POST/PUT/DELETE | `/api/usuarios/` | CRUD usuarios       |
| GET/POST/PUT/DELETE | `/api/roles/`     | CRUD roles          |
| GET    | `/api/permisos/`             | Listar permisos                 |
| GET/POST/PUT/DELETE | `/api/facultades/` | CRUD facultades     |
| GET/POST/PUT/DELETE | `/api/departamentos/` | CRUD departamentos |
| GET/POST/PUT/DELETE | `/api/perfiles/`  | CRUD perfiles       |
| GET/POST/PUT/DELETE | `/api/periodos/`  | CRUD períodos       |
| GET/POST/PUT/DELETE | `/api/criterios/` | CRUD criterios      |
| GET/POST/PUT/DELETE | `/api/indicadores/` | CRUD indicadores  |
| GET/POST/PUT/DELETE | `/api/asignaciones/` | CRUD asignaciones |
| GET/POST/DELETE     | `/api/evidencias/` | CRUD evidencias     |
| GET    | `/api/evidencias/{id}/descargar/` | Descargar archivo |
| GET    | `/api/auditoria/` | Listar bitácora                     |
| GET/PATCH | `/api/notificaciones/` | Listar/leer notificaciones    |
