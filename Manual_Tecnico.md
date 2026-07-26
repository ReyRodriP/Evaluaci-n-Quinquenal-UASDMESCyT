# MANUAL TÉCNICO

## Sistema de Gestión de Evidencias para la Evaluación Quinquenal UASD–MESCyT

---

**República Dominicana**

**Universidad Autónoma de Santo Domingo**

**Facultad de Ciencias**

**Escuela de Informática**

---

**Sustentantes:**

- Reynaldo Rodríguez Polanco — 100655341
- Ramón Paulino Gil — 100345706
- José Manuel Otaño Hernández — 100320080

**Coordinador:** Mtro. Erick Minor

**Asesora Metodológica:** Mtra. Jacqueline Tejada Tio

**Asesora de Contenido:** Mtra. Martha Lidia Pérez Medina

---

**Santo Domingo, Distrito Nacional**

**Julio 2026**

---

## Contenido

1. [Introducción](#1-introducción)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Tecnologías Utilizadas](#3-tecnologías-utilizadas)
4. [Estructura del Proyecto](#4-estructura-del-proyecto)
5. [Modelo de Base de Datos](#5-modelo-de-base-de-datos)
6. [Instalación y Configuración](#6-instalación-y-configuración)
7. [API REST — Endpoints](#7-api-rest--endpoints)
8. [Autenticación y Roles](#8-autenticación-y-roles)
9. [Recuperación de Contraseña](#9-recuperación-de-contraseña)
10. [Despliegue a Producción](#10-despliegue-a-producción)
11. [Mantenimiento y Respaldo](#11-mantenimiento-y-respaldo)

---

## 1. Introducción

El presente manual técnico describe la arquitectura, componentes tecnológicos, estructura de datos y procedimientos de instalación y configuración del **Sistema de Gestión de Evidencias para la Evaluación Quinquenal UASD–MESCyT**.

Este documento está dirigido al personal técnico encargado de la implementación, administración y mantenimiento del sistema. Proporciona la información necesaria para comprender el diseño interno de la plataforma, ejecutar su instalación en entornos de desarrollo y producción, y realizar tareas de soporte técnico.

El sistema se ha desarrollado siguiendo una arquitectura cliente-servidor de tres capas, utilizando tecnologías modernas y de código abierto que garantizan escalabilidad, seguridad y facilidad de mantenimiento.

---

## 2. Arquitectura del Sistema

### 2.1 Modelo General

El sistema sigue una **arquitectura cliente-servidor de tres capas**:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   CAPA DE       │       │   CAPA DE       │       │   CAPA DE       │
│   PRESENTACIÓN  │ ◄───► │   LÓGICA        │ ◄───► │   DATOS         │
│   (Frontend)    │       │   (Backend)     │       │   (BD)          │
│                 │       │                 │       │                 │
│ Angular 20     │       │ Django 6 / DRF  │       │ SQLite3 /      │
│ TypeScript     │       │ Python 3.13     │       │ PostgreSQL     │
│ HTML5 / CSS3   │       │ Token Auth      │       │                 │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

- **Capa de Presentación:** Aplicación web desarrollada en Angular 20, consume la API REST y se encarga de la interacción con el usuario.
- **Capa de Lógica de Negocio:** Servidor Django 6 con Django REST Framework que expone una API RESTful, gestiona autenticación, autorización y la lógica de negocio.
- **Capa de Datos:** Base de datos SQLite3 (desarrollo) o PostgreSQL (producción), almacena la información del sistema y los metadatos de los archivos.

### 2.2 Diagrama de Red

```
                    ┌──────────────────┐
                    │    Internet      │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Navegador Web  │
                    │ (Chrome, Edge,   │
                    │  Firefox, Opera) │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Servidor Web   │
                    │  (Python Any-    │
                    │   where /         │
                    │   Hostinger)     │
                    │                  │
                    │  ┌────────────┐  │
                    │  │  Django    │  │
                    │  │  App       │  │
                    │  └─────┬──────┘  │
                    │        │         │
                    │  ┌─────▼──────┐  │
                    │  │  SQLite3 / │  │
                    │  │ PostgreSQL │  │
                    │  └────────────┘  │
                    │                  │
                    │  ┌────────────┐  │
                    │  │ /media/    │  │
                    │  │ (Archivos  │  │
                    │  │  subidos)  │  │
                    │  └────────────┘  │
                    └──────────────────┘
```

### 2.3 Flujo de Comunicación

1. El usuario accede desde su navegador a la URL del frontend (Angular).
2. Angular se comunica con el backend Django a través de peticiones HTTP (API REST).
3. Django procesa las solicitudes, aplica las reglas de negocio y accede a la base de datos cuando es necesario.
4. Las respuestas se devuelven en formato JSON al frontend para su visualización.
5. Los archivos de evidencias se almacenan en el directorio `/media/` del servidor.

---

## 3. Tecnologías Utilizadas

### 3.1 Backend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.13+ | Lenguaje de programación backend |
| Django | 6.0.5 | Framework web backend |
| Django REST Framework | 3.15+ | Construcción de API REST |
| Django CORS Headers | 4.0+ | Gestión de CORS entre frontend y backend |
| Pillow | 10.0+ | Procesamiento de imágenes |
| SQLite3 | — | Base de datos en desarrollo |
| Token Authentication | — | Autenticación mediante tokens |

### 3.2 Frontend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Angular | 20.3 | Framework frontend |
| TypeScript | 5.9 | Lenguaje de programación frontend |
| HTML5 | — | Estructura de interfaces |
| CSS3 | — | Estilos y diseño responsivo |
| ngx-toastr | 20.0.5 | Notificaciones toast |
| RxJS | 7.8 | Programación reactiva |

### 3.3 Herramientas de Desarrollo

| Herramienta | Propósito |
|-------------|-----------|
| Visual Studio Code | Entorno de desarrollo integrado (IDE) |
| Git | Control de versiones |
| GitHub | Repositorio de código fuente |
| Figma | Diseño de prototipos de interfaces |
| Postman | Pruebas de API |

---

## 4. Estructura del Proyecto

```
monografico/
│
├── backend/                              # Proyecto Django
│   ├── accounts/                         # Autenticación y usuarios
│   │   ├── templates/registration/       # Plantillas de correo
│   │   │   └── password_reset_email.html # Plantilla de recuperación de contraseña
│   │   ├── admin.py                      # Registro en administrador Django
│   │   ├── models.py                     # Modelo Usuario (AbstractUser)
│   │   ├── permissions.py                # Permisos personalizados
│   │   ├── serializers.py                # Serializadores de la API
│   │   ├── urls.py                       # Rutas del módulo
│   │   └── views.py                      # Vistas de la API
│   │
│   ├── auditoria/                        # Bitácora de auditoría
│   │   ├── models.py                     # Modelo Auditoria
│   │   ├── serializers.py                # Serializadores
│   │   ├── urls.py                       # Rutas
│   │   ├── utils.py                      # Función registrar_auditoria()
│   │   └── views.py                      # Vistas
│   │
│   ├── evaluacionQuinquenal/             # Configuración del proyecto Django
│   │   ├── settings.py                   # Configuración general
│   │   ├── urls.py                       # Rutas principales
│   │   ├── wsgi.py                       # Configuración WSGI
│   │   └── asgi.py                       # Configuración ASGI
│   │
│   ├── evaluation/                       # Períodos, criterios, indicadores, asignaciones
│   │   ├── admin.py                      # Administración del módulo
│   │   ├── models.py                     # Periodo, Criterio, Indicador, Asignacion
│   │   ├── serializers.py                # Serializadores
│   │   ├── urls.py                       # Rutas
│   │   └── views.py                      # Vistas
│   │
│   ├── evidencias/                       # Gestión de evidencias (core)
│   │   ├── admin.py
│   │   ├── models.py                     # Modelo Evidencia
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── notificaciones/                   # Notificaciones internas
│   │   ├── admin.py
│   │   ├── models.py                     # Modelo Notificacion
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── utils.py                      # Función crear_notificacion()
│   │   └── views.py
│   │
│   ├── organization/                     # Facultades, departamentos, perfiles
│   │   ├── admin.py
│   │   ├── models.py                     # Facultad, Departamento, PerfilUsuario
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   │
│   ├── media/                            # Archivos subidos (evidencias)
│   ├── manage.py                         # Comando de gestión de Django
│   ├── requirements.txt                  # Dependencias Python
│   └── db.sqlite3                        # Base de datos (desarrollo)
│
├── frontend/
│   └── evaluacion-quinquenal-front/      # Proyecto Angular
│       └── src/app/
│           ├── core/                     # Modelos, servicios, guards, interceptors
│           │   ├── guards/               # auth.guard.ts (protección de rutas)
│           │   └── models/               # user.model.ts
│           │
│           ├── features/                 # Páginas por módulo
│           │   ├── asignaciones/         # CRUD asignaciones
│           │   ├── auditoria/            # Bitácora de auditoría
│           │   ├── auth/                 # Login, registro, recuperación de contraseña
│           │   │   ├── pages/
│           │   │   │   ├── login/        # Inicio de sesión
│           │   │   │   ├── register/     # Registro
│           │   │   │   ├── forgot-password/  # Solicitar recuperación
│           │   │   │   └── reset-password/   # Restablecer contraseña
│           │   │   └── services/         # auth-service.ts
│           │   ├── criterios/            # CRUD criterios
│           │   ├── dashboard/            # Tablero principal
│           │   ├── evidencias/           # Subida/descarga de evidencias
│           │   ├── facultades/           # CRUD facultades y departamentos
│           │   ├── indicadores/          # CRUD indicadores
│           │   ├── periodos/             # CRUD períodos
│           │   └── usuarios/             # CRUD usuarios
│           │
│           ├── layouts/                  # AdminLayout y AuthLayout
│           └── shared/                   # Sidebar y Navbar
│
├── plan.md                               # Documento de planificación del proyecto
├── README.md                             # Documentación general del proyecto
└── Manual_Tecnico.md                     # Este documento
```

---

## 5. Modelo de Base de Datos

### 5.1 Diagrama Entidad-Relación

```
┌──────────────┐       ┌──────────────────┐
│   Usuario    │       │    Facultad      │
│──────────────│       │──────────────────│
│ id (PK)      │       │ id (PK)          │
│ username     │       │ nombre (unique)  │
│ email        │       │ descripcion      │
│ password     │       │ activo           │
│ first_name   │       │ fecha_creacion   │
│ last_name    │       └────────┬─────────┘
│ telefono     │                │ 1
│ is_active    │                │
│ fecha_registro│               │
└──────┬───────┘                │
       │ 1                     │
       │                       │
┌──────▼────────┐    ┌─────────▼──────────┐
│ PerfilUsuario │    │    Departamento    │
│───────────────│    │────────────────────│
│ id (PK)       │    │ id (PK)            │
│ usuario_id(FK)│◄──►│ nombre             │
│ departamento  │    │ descripcion        │
│ (FK)          │    │ facultad_id (FK)   │
└───────────────┘    │ activo             │
                     │ fecha_creacion     │
                     └─────────┬──────────┘
                               │ 1
                               │
                     ┌─────────▼──────────┐
                     │     Periodo        │
                     │────────────────────│
                     │ id (PK)            │
                     │ nombre             │
                     │ fecha_inicio       │
                     │ fecha_fin          │
                     │ activo             │
                     └─────────┬──────────┘
                               │ 1
                               │
                     ┌─────────▼──────────┐
                     │     Criterio       │
                     │────────────────────│
                     │ id (PK)            │
                     │ nombre             │
                     │ descripcion        │
                     │ periodo_id (FK)    │
                     │ activo             │
                     └─────────┬──────────┘
                               │ 1
                               │
                     ┌─────────▼──────────┐
                     │    Indicador       │
                     │────────────────────│
                     │ id (PK)            │
                     │ nombre             │
                     │ descripcion        │
                     │ criterio_id (FK)   │
                     │ obligatorio        │
                     │ activo             │
                     └─────────┬──────────┘
                               │ 1
                               │
                     ┌─────────▼──────────┐
                     │    Asignacion      │
                     │────────────────────│
                     │ id (PK)            │
                     │ indicador_id (FK)  │
                     │ departamento_id(FK)│
                     │ periodo_id (FK)    │
                     │ estado             │
                     │ (unique: ind+dep+per)│
                     └─────────┬──────────┘
                               │ 1
                               │
                     ┌─────────▼──────────┐
                     │    Evidencia       │
                     │────────────────────│
                     │ id (PK)            │
                     │ asignacion_id (FK) │
                     │ archivo (FileField)│
                     │ nombre             │
                     │ descripcion        │
                     │ tipo_archivo       │
                     │ tamano             │
                     │ subido_por_id(FK)  │
                     │ fecha_subida       │
                     │ version            │
                     │ observaciones      │
                     └────────────────────┘

┌──────────────────┐    ┌──────────────────┐
│   Auditoria      │    │  Notificacion    │
│──────────────────│    │──────────────────│
│ id (PK)          │    │ id (PK)          │
│ usuario_id (FK)  │    │ usuario_id (FK)  │
│ accion           │    │ titulo           │
│ modelo           │    │ mensaje          │
│ registro_id      │    │ leida            │
│ descripcion      │    │ fecha_creacion   │
│ fecha            │    └──────────────────┘
└──────────────────┘
```

### 5.2 Descripción de Modelos

**accounts.Usuario**
- Hereda de `AbstractUser` de Django (username, email, password, first_name, last_name, is_active, is_superuser, groups, permissions).
- Campos adicionales: `telefono` (CharField, max 20), `fecha_registro` (DateTimeField, auto_now_add).

**organization.Facultad**
- `nombre` (CharField, max 100, unique)
- `descripcion` (TextField, nullable)
- `activo` (BooleanField, default True)
- `fecha_creacion` (DateTimeField, auto_now_add)

**organization.Departamento**
- `nombre` (CharField, max 100)
- `descripcion` (TextField, nullable)
- `facultad` (ForeignKey a Facultad, CASCADE, related_name='departamentos')
- `activo` (BooleanField, default True)
- `fecha_creacion` (DateTimeField, auto_now_add)

**organization.PerfilUsuario**
- `usuario` (OneToOneField a Usuario, CASCADE)
- `departamento` (ForeignKey a Departamento, SET_NULL, nullable)

**evaluation.Periodo**
- `nombre` (CharField, max 100)
- `fecha_inicio` (DateField)
- `fecha_fin` (DateField)
- `activo` (BooleanField, default True)

**evaluation.Criterio**
- `nombre` (CharField, max 100)
- `descripcion` (TextField, nullable)
- `periodo` (ForeignKey a Periodo, CASCADE, related_name='criterios', nullable)
- `activo` (BooleanField, default True)

**evaluation.Indicador**
- `nombre` (CharField, max 100)
- `descripcion` (TextField, nullable)
- `criterio` (ForeignKey a Criterio, CASCADE, related_name='indicadores')
- `obligatorio` (BooleanField, default False)
- `activo` (BooleanField, default True)

**evaluation.Asignacion**
- `indicador` (ForeignKey a Indicador, CASCADE, related_name='asignaciones')
- `departamento` (ForeignKey a Departamento, CASCADE, related_name='asignaciones')
- `periodo` (ForeignKey a Periodo, CASCADE, related_name='asignaciones')
- `estado` (CharField, choices: pendiente, en_progreso, completado, aprobado, rechazado)
- `Meta.unique_together`: ('indicador', 'departamento', 'periodo')

**evidencias.Evidencia**
- `asignacion` (ForeignKey a Asignacion, CASCADE, related_name='evidencias')
- `archivo` (FileField, upload_to='evidencias/{periodo}/{departamento}/{indicador}/')
- `nombre` (CharField, max 255)
- `descripcion` (TextField, nullable)
- `tipo_archivo` (CharField, max 50)
- `tamano` (BigIntegerField)
- `subido_por` (ForeignKey a Usuario, SET_NULL, nullable)
- `fecha_subida` (DateTimeField, auto_now_add)
- `version` (PositiveIntegerField, default 1)
- `observaciones` (TextField, nullable)

**auditoria.Auditoria**
- `usuario` (ForeignKey a Usuario, SET_NULL, nullable)
- `accion` (CharField, max 100)
- `modelo` (CharField, max 100)
- `registro_id` (IntegerField, nullable)
- `descripcion` (TextField)
- `fecha` (DateTimeField, auto_now_add)

**notificaciones.Notificacion**
- `usuario` (ForeignKey a Usuario, CASCADE, related_name='notificaciones')
- `titulo` (CharField, max 255)
- `mensaje` (TextField)
- `leida` (BooleanField, default False)
- `fecha_creacion` (DateTimeField, auto_now_add)

---

## 6. Instalación y Configuración

### 6.1 Requisitos del Sistema

#### Hardware (Servidor)

| Componente | Especificación Mínima | Recomendada |
|------------|----------------------|-------------|
| Procesador | 2 núcleos | 4+ núcleos |
| RAM | 2 GB | 4+ GB |
| Almacenamiento | 20 GB | 50+ GB (dependiendo del volumen de evidencias) |
| Conexión | 10 Mbps | 100+ Mbps |

#### Software

| Componente | Versión Mínima |
|------------|---------------|
| Python | 3.12 |
| Node.js | 18.x |
| npm | 9.x |
| Git | Cualquier versión moderna |

### 6.2 Instalación del Backend

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd Evaluaci-n-Quinquenal-UASDMESCyT/backend

# 2. Crear y activar entorno virtual
python -m venv .venv

# En Windows:
.venv\Scripts\activate

# En Linux/macOS:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Crear superusuario
python manage.py createsuperuser

# 6. Iniciar servidor de desarrollo
python manage.py runserver
```

El backend estará disponible en `http://127.0.0.1:8000/`.

### 6.3 Instalación del Frontend

```bash
# 1. Navegar al directorio del frontend
cd frontend/evaluacion-quinquenal-front

# 2. Instalar dependencias
npm install --legacy-peer-deps

# 3. Iniciar servidor de desarrollo
npm start
```

El frontend estará disponible en `http://localhost:4200/`.

### 6.4 Configuración de Correo Electrónico

Para la funcionalidad de recuperación de contraseña, configurar las siguientes variables en `backend/evaluacionQuinquenal/settings.py`:

```python
# Desarrollo (imprime correos en consola):
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Producción (SMTP - ejemplo con Gmail):
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'tu-correo@gmail.com'
# EMAIL_HOST_PASSWORD = 'contraseña-de-aplicación'
# DEFAULT_FROM_EMAIL = 'tu-correo@gmail.com'

FRONTEND_URL = 'http://localhost:4200'  # Cambiar en producción
```

### 6.5 Archivo requirements.txt

```
django>=5.0,<7.0
djangorestframework>=3.15
django-cors-headers>=4.0
Pillow>=10.0
```

---

## 7. API REST — Endpoints

### 7.1 Autenticación

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| POST | `/api/login/` | Iniciar sesión | No |
| POST | `/api/register/` | Registrarse | No |
| GET | `/api/me/` | Obtener usuario actual | Token |
| PUT | `/api/profile/` | Actualizar perfil | Token |
| POST | `/api/change_password/` | Cambiar contraseña | Token |
| POST | `/api/password-reset/` | Solicitar recuperación de contraseña | No |
| POST | `/api/password-reset/confirm/` | Confirmar recuperación de contraseña | No |

#### POST `/api/login/`

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "token": "string",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "telefono": "string",
    "is_active": true,
    "rol": "string",
    "groups": []
  }
}
```

#### POST `/api/password-reset/`

**Request:**
```json
{
  "email": "usuario@example.com"
}
```

**Response (200):**
```json
{
  "message": "Se ha enviado un correo con las instrucciones para recuperar tu contraseña."
}
```

#### POST `/api/password-reset/confirm/`

**Request:**
```json
{
  "uidb64": "string",
  "token": "string",
  "new_password": "nueva-contraseña"
}
```

**Response (200):**
```json
{
  "message": "Contraseña restablecida correctamente."
}
```

### 7.2 Usuarios

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/api/usuarios/` | Listar usuarios | Token (Admin) |
| GET | `/api/usuarios/{id}/` | Detalle de usuario | Token (Admin) |
| PUT | `/api/usuarios/{id}/` | Actualizar usuario | Token (Admin) |
| PATCH | `/api/usuarios/{id}/` | Actualizar parcialmente | Token (Admin) |
| GET | `/api/usuarios/{id}/permisos/` | Permisos de usuario | Token (Admin) |

### 7.3 Roles y Permisos

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/api/roles/` | Listar roles | Token (Admin) |
| POST | `/api/roles/` | Crear rol | Token (Admin) |
| PUT | `/api/roles/{id}/` | Actualizar rol | Token (Admin) |
| DELETE | `/api/roles/{id}/` | Eliminar rol | Token (Admin) |
| GET | `/api/permisos/` | Listar permisos | Token (Admin) |

### 7.4 Organización

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/api/facultades/` | Listar facultades | Token |
| POST | `/api/facultades/` | Crear facultad | Token |
| PUT | `/api/facultades/{id}/` | Actualizar facultad | Token |
| DELETE | `/api/facultades/{id}/` | Eliminar facultad | Token |
| GET | `/api/departamentos/` | Listar departamentos | Token |
| POST | `/api/departamentos/` | Crear departamento | Token |
| PUT | `/api/departamentos/{id}/` | Actualizar departamento | Token |
| DELETE | `/api/departamentos/{id}/` | Eliminar departamento | Token |
| GET | `/api/perfiles/` | Listar perfiles | Token |
| POST | `/api/perfiles/` | Crear perfil | Token |
| PUT | `/api/perfiles/{id}/` | Actualizar perfil | Token |
| DELETE | `/api/perfiles/{id}/` | Eliminar perfil | Token |

### 7.5 Evaluación

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/api/periodos/` | Listar períodos | Token |
| POST | `/api/periodos/` | Crear período | Token |
| PUT | `/api/periodos/{id}/` | Actualizar período | Token |
| DELETE | `/api/periodos/{id}/` | Eliminar período | Token |
| GET | `/api/criterios/` | Listar criterios | Token |
| POST | `/api/criterios/` | Crear criterio | Token |
| PUT | `/api/criterios/{id}/` | Actualizar criterio | Token |
| DELETE | `/api/criterios/{id}/` | Eliminar criterio | Token |
| GET | `/api/indicadores/` | Listar indicadores | Token |
| POST | `/api/indicadores/` | Crear indicador | Token |
| PUT | `/api/indicadores/{id}/` | Actualizar indicador | Token |
| DELETE | `/api/indicadores/{id}/` | Eliminar indicador | Token |
| GET | `/api/asignaciones/` | Listar asignaciones | Token |
| POST | `/api/asignaciones/` | Crear asignación | Token |
| PUT | `/api/asignaciones/{id}/` | Actualizar asignación | Token |
| DELETE | `/api/asignaciones/{id}/` | Eliminar asignación | Token |

### 7.6 Evidencias

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/api/evidencias/` | Listar evidencias | Token |
| POST | `/api/evidencias/` | Subir evidencia | Token |
| DELETE | `/api/evidencias/{id}/` | Eliminar evidencia | Token |
| GET | `/api/evidencias/{id}/descargar/` | Descargar archivo | Token |

### 7.7 Auditoría

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/api/auditoria/` | Listar bitácora | Token |

### 7.8 Notificaciones

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/api/notificaciones/` | Listar notificaciones | Token |
| PATCH | `/api/notificaciones/{id}/` | Marcar como leída | Token |

---

## 8. Autenticación y Roles

### 8.1 Sistema de Autenticación

El sistema utiliza **Token Authentication** de Django REST Framework. Al iniciar sesión, se genera un token único que debe enviarse en el encabezado `Authorization` de las peticiones autenticadas:

```
Authorization: Token abcdef123456789...
```

### 8.2 Roles del Sistema

Los roles se gestionan mediante **grupos de Django** (`django.contrib.auth.models.Group`). Los roles predefinidos son:

| Rol | Descripción |
|-----|-------------|
| Administrador General | Acceso completo a todos los módulos del sistema |
| Administrador | Gestión de usuarios, facultades, departamentos y configuración |
| Evaluador | Revisión y validación de evidencias |
| Usuario | Carga y gestión de evidencias asignadas |

### 8.3 Permisos Personalizados

El archivo `accounts/permissions.py` define:

- **`IsAdminGroup`**: Verifica que el usuario pertenezca al grupo 'Administrador General'. Los superusuarios también tienen acceso.
- **`CustomModelPermissions`**: Mapea métodos HTTP a permisos de Django (`view_`, `add_`, `change_`, `delete_`).

---

## 9. Recuperación de Contraseña

### 9.1 Flujo de Funcionamiento

1. El usuario solicita la recuperación desde el formulario "¿Olvidaste tu contraseña?".
2. El frontend envía una petición `POST /api/password-reset/` con el correo electrónico.
3. El backend verifica que el correo exista en la base de datos.
4. Django genera un token único mediante `PasswordResetTokenGenerator`.
5. Se envía un correo electrónico con un enlace que contiene `uidb64` y `token`.
6. El usuario abre el enlace y accede al formulario de nueva contraseña.
7. El frontend envía una petición `POST /api/password-reset/confirm/` con `uidb64`, `token` y `new_password`.
8. El backend valida el token, actualiza la contraseña y elimina los tokens de autenticación existentes.

### 9.2 Configuración de Correo

Para entornos de desarrollo, el sistema imprime los correos en la consola. Para producción, debe configurarse un servidor SMTP en `settings.py` (ver sección 6.4).

---

## 10. Despliegue a Producción

### 10.1 Preparación del Backend

```bash
# 1. Configurar DEBUG=False en settings.py
DEBUG = False

# 2. Configurar ALLOWED_HOSTS
ALLOWED_HOSTS = ['tudominio.com', 'www.tudominio.com']

# 3. Configurar base de datos PostgreSQL (recomendado)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nombre_db',
        'USER': 'usuario',
        'PASSWORD': 'contraseña',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# 4. Configurar correo SMTP (ver sección 6.4)
# 5. Configurar FRONTEND_URL con la URL de producción
FRONTEND_URL = 'https://tudominio.com'

# 6. Recopilar archivos estáticos
python manage.py collectstatic

# 7. Ejecutar migraciones
python manage.py migrate
```

### 10.2 Preparación del Frontend

```bash
# 1. Construir el proyecto Angular
npm run build

# 2. Los archivos generados estarán en:
#    dist/evaluacion-quinquenal-front/
```

### 10.3 Opciones de Despliegue

#### Opción 1: PythonAnywhere
- Subir el proyecto a PythonAnywhere
- Configurar la aplicación web Django
- Configurar la base de datos MySQL
- Configurar archivos estáticos y media

#### Opción 2: Hostinger / VPS
- Configurar servidor Linux (Ubuntu 22.04+)
- Instalar Python, Node.js, Nginx
- Configurar Gunicorn como servidor WSGI
- Configurar Nginx como proxy inverso
- Configurar PostgreSQL como base de datos
- Configurar certificado SSL (Let's Encrypt)

### 10.4 Archivos Estáticos y Media

```python
# Configuración recomendada para producción
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Configurar Nginx para servir archivos estáticos y media:

```nginx
location /static/ {
    alias /ruta/a/backend/staticfiles/;
}

location /media/ {
    alias /ruta/a/backend/media/;
}
```

---

## 11. Mantenimiento y Respaldo

### 11.1 Respaldo de Base de Datos

```bash
# SQLite (desarrollo)
cp backend/db.sqlite3 backup/db_$(date +%Y%m%d).sqlite3

# PostgreSQL (producción)
pg_dump -U usuario -h localhost nombre_db > backup/db_$(date +%Y%m%d).sql
```

### 11.2 Respaldo de Archivos (Evidencias)

```bash
# Respaldo del directorio media
tar -czf backup/media_$(date +%Y%m%d).tar.gz backend/media/
```

### 11.3 Actualización del Sistema

```bash
# 1. Respaldar base de datos y archivos
# 2. Actualizar código
git pull origin main

# 3. Actualizar dependencias
pip install -r requirements.txt
npm install --legacy-peer-deps

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Recopilar archivos estáticos
python manage.py collectstatic --noinput

# 6. Reiniciar servidor
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 11.4 Monitoreo

- Revisar logs del servidor: `journalctl -u gunicorn` (Linux)
- Revisar bitácora de auditoría desde el panel de administración de Django (`/admin/auditoria/auditoria/`)
- Realizar pruebas periódicas de funcionalidades críticas (inicio de sesión, carga de evidencias, recuperación de contraseña)

---

**Documento elaborado por el equipo de desarrollo:**

- Reynaldo Rodríguez Polanco
- Ramón Paulino Gil
- José Manuel Otaño Hernández

**Universidad Autónoma de Santo Domingo (UASD)**

**Julio 2026**
