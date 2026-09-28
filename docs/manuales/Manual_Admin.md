# MANUAL DE ADMINISTRACIÓN

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
2. [Acceso como Administrador](#2-acceso-como-administrador)
3. [Roles y Permisos](#3-roles-y-permisos)
4. [Gestión de Usuarios y Roles](#4-gestión-de-usuarios-y-roles)
5. [Administración de los Módulos](#5-administración-de-los-módulos)
6. [Seguridad y Variables de Entorno](#6-seguridad-y-variables-de-entorno)
7. [Despliegue del Sistema](#7-despliegue-del-sistema)
8. [Mantenimiento](#8-mantenimiento)
9. [Respaldo y Restauración](#9-respaldo-y-restauración)
10. [Solución de Problemas](#10-solución-de-problemas)

---

## 1. Introducción

El presente manual está dirigido al **administrador** del Sistema de Gestión de Evidencias para la Evaluación Quinquenal UASD–MESCyT. Describe las tareas de gestión de usuarios, roles, módulos de evaluación, seguridad, despliegue, mantenimiento y respaldo de la plataforma.

El administrador es responsable de:

- Crear y administrar los usuarios y sus roles.
- Configurar los períodos de evaluación, criterios e indicadores.
- Asignar las responsabilidades de presentación de evidencias a los departamentos.
- Vigilar la integridad de la información mediante la bitácora de auditoría.
- Garantizar la disponibilidad del sistema (despliegue, respaldo y recuperación).

---

## 2. Acceso como Administrador

### 2.1 URLs del Sistema

| Recurso | URL |
|---------|-----|
| Frontend (usuarios) | `http://localhost` |
| API REST | `http://localhost:8000/api/` |
| Documentación de la API (Swagger) | `http://localhost:8000/api/docs/` |
| Panel de administración de Django | `http://localhost:8000/admin/` |
| Verificación de salud | `http://localhost:8000/health/` |

### 2.2 Superusuario

El sistema **no** tiene contraseñas por defecto. Al desplegar, el administrador crea o actualiza el superusuario con su propia contraseña:

```powershell
.\crear_superusuario.ps1 -Username admin -Email admin@uasd.edu.do -Password ClaveSegura123
```

Si no se indica `-Password`, el script lo pregunta de forma oculta. El superusuario tiene acceso total a todos los módulos sin importar el grupo al que pertenezca. **No deben publicarse estas credenciales en la documentación ni en el repositorio.**

### 2.3 Primeros Pasos

1. Ejecutar el despliegue del sistema (sección 7).
2. Crear el superusuario con `.\crear_superusuario.ps1`.
3. Registrar en el panel los períodos, criterios, indicadores y asignaciones necesarios.
4. Crear los usuarios de los departamentos y asignar sus roles.
5. Cambiar la contraseña por defecto del superusuario.

---

## 3. Roles y Permisos

El sistema gestiona los roles mediante **grupos de Django**. Los roles predefinidos son:

| Rol | Alcance |
|-----|---------|
| **Administrador General** | Acceso total a todos los módulos (equivalente al superusuario). |
| **Coordinador Quinquenal** | Coordina la evaluación: reportes completos, auditoría y revisión. |
| **Revisor Institucional** | Revisión y validación de evidencias; acceso a reportes. |
| **Evaluador Externo** | Revisión de evidencias sin restricciones adicionales. |
| **Responsable Departamental** | Gestiona las asignaciones y evidencias de su departamento. |
| **Consulta** | Acceso de solo lectura a la información del sistema. |

Los permisos de cada rol están definidos en `backend/accounts/role_permissions.py` y se aplican a la API y al menú del frontend.

### 3.1 Sincronizar Permisos de Roles

Si se modifican los permisos asociados a los roles, ejecutar:

```bash
cd backend
python manage.py sync_roles
```

En Docker:

```powershell
docker compose exec backend python manage.py sync_roles
```

---

## 4. Gestión de Usuarios y Roles

### 4.1 Crear o Actualizar el Superusuario

Desde la raíz del proyecto (requiere el stack levantado):

```powershell
.\crear_superusuario.ps1 -Username admin -Email admin@uasd.edu.do -Password ClaveSegura123   # sin -Password pregunta de forma oculta
.\crear_superusuario.ps1 -Mode k8s -Username admin -Password ClaveSegura123                   # si el despliegue fue con Kubernetes
```

El script es **idempotente**: crea el usuario si no existe o actualiza su contraseña, correo y estado si ya existe.

Equivalente manual en el contenedor:

```powershell
docker compose exec backend python manage.py crear_superusuario --username admin --email admin@uasd.edu.do --password ClaveSegura123
```

### 4.2 Crear un Usuario Regular

Por la interfaz (panel frontend → módulo **Usuarios** → botón **"+ crear"**) o por Django admin (`/admin/`). Se recomienda además **semillar el sistema** para obtener datos de demostración completos:

```powershell
docker compose exec backend python manage.py seed
```

### 4.3 Diagnosticar un Usuario

```powershell
docker compose exec backend python manage.py check_usuario <username>
```

Muestra el estado del superusuario, sus grupos, permisos y departamento asignado.

### 4.4 Cambiar Contraseña de un Usuario

```powershell
docker compose exec backend python manage.py changepassword <username>
```

---

## 5. Administración de los Módulos

Todas las operaciones se realizan desde la interfaz web con permisos de Administrador General.

### 5.1 Facultades y Departamentos

1. Menú **Facultades** → **"+ Nueva Facultad"**: registrar nombre, descripción y estado.
2. Dentro de cada facultad, **"+ Depto"** para registrar los departamentos.
3. Cada departamento podrá recibir asignaciones de indicadores.

### 5.2 Períodos de Evaluación

1. Menú **Períodos** → **"+ Nuevo Período"**.
2. Definir nombre, **fecha de inicio** y **fecha de fin**.
3. Marcar como **activo** el período que esté en curso.

### 5.3 Criterios

1. Menú **Criterios** → **"+ Nuevo Criterio"**.
2. Vincular el criterio al **período** correspondiente.

### 5.4 Indicadores

1. Menú **Indicadores** → **"+ Nuevo Indicador"**.
2. Vincular el indicador al **criterio**; marcar si es **obligatorio**.

### 5.5 Asignaciones

1. Menú **Asignaciones** → **"+ Nueva Asignación"**.
2. Seleccionar **indicador + departamento + período**. Estados posibles: pendiente → en_progreso → completado → aprobado/rechazado.
3. Al asignar, el sistema genera una **notificación** al responsable departamental.

### 5.6 Evidencias

1. Menú **Evidencias**. Subir archivos de hasta **50 MB** en formatos PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF, TXT, ZIP, RAR.
2. El sistema versiona automáticamente cada documento por asignación.
3. Se permite descargar y eliminar evidencias con los permisos adecuados.

### 5.7 Auditoría

Menú **Auditoría**: bitácora de solo lectura con registro automático de inicios de sesión y todas las operaciones CRUD (fecha, usuario, acción, modelo, descripción). No puede ser modificada ni eliminada desde la interfaz.

### 5.8 Notificaciones y Reportes

- **Notificaciones:** el sistema las genera al asignar indicadores o cambiar estados y puede enviarlas por correo si se configura SMTP.
- **Reportes:** los roles con `ROLES_REPORTES` pueden exportar reportes de usuarios, auditoría y evidencias desde la API `/api/reportes/`.

---

## 6. Seguridad y Variables de Entorno

La configuración se maneja mediante el archivo `.env` en la raíz del proyecto (no se sube al repositorio; existe `.env.example` como plantilla).

| Variable | Descripción | Recomendación |
|----------|-------------|---------------|
| `DEBUG` | Modo desarrollo/producción | `False` en producción |
| `SECRET_KEY` | Clave secreta de Django | Generar con `get_random_secret_key()`, ≥ 50 caracteres |
| `ALLOWED_HOSTS` | Dominios permitidos | Solo los dominios reales, separados por coma |
| `DB_PASSWORD` | Contraseña de PostgreSQL | Clave fuerte |
| `SECURE_SSL_REDIRECT` | Forzar HTTPS | `True` si hay certificado SSL |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | Cookies seguras | `True` con HTTPS, `False` en HTTP |
| `SECURE_HSTS_SECONDS` | HSTS | `31536000` con HTTPS |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP para recuperación de contraseña | Cuenta de correo real con contraseña de aplicación |
| `SENTRY_DSN` | Monitoreo de errores | DSN de sentry.io |
| `NOTIFICACIONES_EMAIL_ENABLED` | Enviar correos al crear notificaciones | `True` si hay SMTP |

> **Regla de oro:** nunca subir `.env` ni secretos al repositorio. En Kubernetes los secretos se inyectan desde `k8s/01-secrets.yaml`.

---

## 7. Despliegue del Sistema

### 7.1 Despliegue Local con Docker (recomendado)

Requisitos: Docker Desktop ejecutándose.

```powershell
.\up.ps1                 # modo docker: levanta Postgres, Redis, Backend y Frontend
.\crear_superusuario.ps1 # crea el superusuario
```

El script construye las imágenes, espera a que el backend esté sano (`/health/`), aplica migraciones y recopila estáticos.

### 7.2 Despliegue Local con Kubernetes (Docker Desktop)

1. Activar Kubernetes en Docker Desktop (Settings → Kubernetes → Enable cluster).
2. Ejecutar:

```powershell
.\up.ps1 -mode k8s
.\crear_superusuario.ps1 -Mode k8s
```

El script construye las imágenes locales, las inyecta en los manifests y despliega el namespace `evaluacion-quinquenal`.

### 7.3 Despliegue Automático (CI/CD con GitHub Actions)

El flujo `.github/workflows/deploy.yml` despliega automáticamente Docker + Kubernetes al hacer `push` a `main`, o manualmente desde GitHub (pestaña **Actions → Deploy a Kubernetes → Run workflow**). Esto permite desplegar desde cualquier dispositivo.

Requisitos previos:

1. Un clúster accesible desde internet (por ejemplo **k3s** en una VPS).
2. Secret de GitHub `KUBECONFIG` con el kubeconfig del clúster en base64.
3. Variable de GitHub `DOMAIN` (opcional) con el dominio o IP del ingress (p. ej. `123.45.67.89.nip.io`).

El flujo construye las imágenes, las publica en GHCR (`ghcr.io/<repo>/backend` y `frontend`), aplica los manifests en orden, espera los rollouts y ejecuta migraciones y estáticos.

### 7.4 Detener el Sistema

```powershell
docker compose down        # detiene los contenedores
docker compose down -v     # además elimina los volúmenes (¡pierde datos!)
kubectl delete ns evaluacion-quinquenal   # elimina el despliegue k8s y sus datos
```

---

## 8. Mantenimiento

### 8.1 Verificar Salud del Servicio

`http://localhost:8000/health/` responde `200` con estado de **base de datos**, **caché (Redis)** y **media**. Si algún componente falla responde `503` (`degraded`).

### 8.2 Migraciones y Estáticos

```powershell
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py collectstatic --noinput
```

### 8.3 Logs

```powershell
docker compose logs -f backend
docker compose logs -f frontend
kubectl logs -n evaluacion-quinquenal -l app=backend -f   # k8s
```

### 8.4 Verificación Periódica

- Revisar la bitácora de auditoría en busca de operaciones sospechosas.
- Comprobar el estado de los backups (sección 9).
- Probar el inicio de sesión, la carga de evidencias y la recuperación de contraseña.

---

## 9. Respaldo y Restauración

### 9.1 Respaldo Manual

El script `backup.sh` crea un respaldo **cifrado AES-256-CBC** de la base de datos (PostgreSQL) y de la carpeta de evidencias (media), lo guarda en `/backups/evaluacion-quinquenal` y rota archivos con más de 30 días.

```bash
export BACKUP_PASSPHRASE='frase-de-cifrado-segura'
./backup.sh
```

En Kubernetes existe además un **CronJob** (`k8s/07-backup.yaml`) que ejecuta este respaldo diariamente a las 02:00.

### 9.2 Restaurar la Base de Datos

```bash
export BACKUP_PASSPHRASE='frase-de-cifrado-segura'
openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_PASSPHRASE \
  -in /backups/evaluacion-quinquenal/db_YYYYMMDD_HHMMSS.sql.gz.enc \
  | gunzip | psql -U evaluacion_user -h localhost evaluacion_quinquenal
```

### 9.3 Restaurar las Evidencias (media)

```bash
export BACKUP_PASSPHRASE='frase-de-cifrado-segura'
openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_PASSPHRASE \
  -in /backups/evaluacion-quinquenal/media_YYYYMMDD_HHMMSS.tar.gz.enc \
  | tar -xz -C backend/
```

> Guarde la `BACKUP_PASSPHRASE` en un lugar seguro: sin ella es imposible descifrar los respaldos.

---

## 10. Solución de Problemas

| Problema | Posible Causa | Solución |
|----------|---------------|----------|
| `up.ps1` dice que el backend no responde en /health/ | HTTP redirige a HTTPS o el servicio no arrancó | Verificar `SECURE_SSL_REDIRECT=False` en `.env` (despliegue HTTP) y revisar `docker compose logs backend` |
| No inicia sesión | Credenciales incorrectas o cuenta inactiva | Usar `crear_superusuario.ps1` o `chagepassword`; verificar `is_active` |
| No ve los módulos del menú | Rol sin permisos | Asignar el grupo correcto al usuario y ejecutar `sync_roles` |
| Error al subir evidencia | Archivo > 50 MB o formato no permitido | Verificar tamaño y formato del archivo |
| No llegan correos de recuperación | SMTP no configurado o en spam | Configurar `EMAIL_*` en `.env`; revisar bandeja de spam |
| El despliegue k8s de GitHub falla | `KUBECONFIG` inválido o caducado | Regenerar el kubeconfig y actualizar el secret en GitHub |
| Los pods de k8s no quedan `Ready` | Imagen no disponible o recursos insuficientes | Revisar `kubectl describe pod -n evaluacion-quinquenal` |
| No se descifra un backup | Frase de cifrado incorrecta | Verificar `BACKUP_PASSPHRASE` |

---

**Documento elaborado por el equipo de desarrollo:**

- Reynaldo Rodríguez Polanco
- Ramón Paulino Gil
- José Manuel Otaño Hernández

**Universidad Autónoma de Santo Domingo (UASD)**

**Julio 2026**