# Pendientes de Producción — Evaluación Quinquenal UASD–MESCyT

> Estado: auditoría completada (sept. 2026). Los pendientes listados aquí requieren
> decisión o coordinación del equipo; no se aplicaron directamente para no romper el
> sistema en funcionamiento. Cada sección incluye motivo, riesgo y cómo resolverlo.

---

## 🔴 Críticos (requieren acción del equipo)

### 1. Rotar credenciales expuestas en el historial de git
- **Qué:** `SECRET_KEY`, `DB_PASSWORD` y `SUPERUSER_PASSWORD` estuvieron commiteados en `.env` y `k8s/01-secrets.yaml`. Ya se sacaron del seguimiento y se rotó el `SECRET_KEY` local, pero **el historial de git sigue conteniendo los valores**.
- **Riesgo:** si el repositorio es público/compartido, cualquiera puede forjar JWTs y acceder a la BD con la contraseña filtrada.
- **Acción:**
  - Rotar `DB_PASSWORD` (ALTER USER + actualizar `.env`).
  - Rotar `SUPERUSER_PASSWORD` y comunicar la nueva credencial al equipo.
  - Para limpiar el historial: `git filter-repo` / BFG (o, en repositorios GitHub, contactar soporte).
  - Proteger `.env` con una regla de push (Server-Side Hook / GitHub secret scanning rules).

### 2. Kubernetes: secretos y TLS
- **Qué:** en k8s los secretos se aplican desde `k8s/01-secrets.yaml` (fuera del repo ahora, solo plantilla). El `Service` del frontend es `type: LoadBalancer`, que **salta el Ingress**, y el Ingress no tiene bloque `tls`.
- **Acción:**
  - Usar **SealedSecrets** o **External Secrets** (Vault) en lugar de archivos de Secret.
  - Cambiar el Service frontend a `ClusterIP` y añadir `tls` + certificado al Ingress (cert-manager o secret TLS).
  - Definir `securityContext` (`runAsNonRoot`) en los Deployments.

### 3. Activar tests de frontend en CI (bloqueados por specs rotos)
- **Qué:** la suite `ng test` falla hoy (22/29 specs porque no proveen `HttpClient`/`ToastrService` al crear los componentes). Este fallo es **preexistente**; CI solo hace `ng build`.
- **Acción:** corregir los ~22 specs (añadir `provideHttpClientTesting()` + `ToastrModule.forRoot()` + Router según componente) y luego habilitar `npm test -- --watch=false --browsers=ChromeHeadless` en `.github/workflows/ci.yml`.

---

## 🟠 Altas (mejoras de seguridad/robustez recomendadas)

### 4. Conectar las señales de `accounts/signals.py`
- **Qué:** `prevent_manual_permission_change` y `sync_permissions_on_group_change` están definidas pero **nunca se importan** (código muerto), por lo que los permisos de rol no se protegen ni se sincronizan automáticamente.
- **Por qué no se aplicó:** al conectarlas, cualquier `Group.permissions.set()` fuera del flujo de sincronización lanza `PermissionError`, lo que rompe tests y el seed (hacen `permissions.set()` directo).
- **Acción:** conectar en `accounts/apps.py` (`ready()` → `import accounts.signals`) y reescribir los tests/seed para usar `sync_group_permissions`.

### 5. Búsqueda global expone emails de todos los usuarios
- **Qué:** `search/views.py` busca sobre `username/email/first_name/last_name` de **todos** los usuarios y devuelve `email`, sin filtrar por departamento/perfil. Como el registro es abierto, cualquier autenticado puede enumerar correos.
- **Acción:** filtrar por `departamentos_permitidos(request)` (como en `DepartamentoViewSet`) y/o no exponer `email` en los resultados.

### 6. Consolidar las apps duplicadas de evidencia (`evidence` vs `evidencias`)
- **Qué:** ambas apps registran el prefijo `api/evidencias/`; gana `evidence` y la app `evidencias` es inalcanzable. `dashboard/views.py` lee `evidencias.models.Evidencia` mientras la API usa `evidence.models.Evidencia` → dos fuentes de datos divergentes.
- **Acción:** fusionar en una sola app (recomendado: `evidence`) con una migración de datos, o eliminar la sombreada tras confirmar que nadie la usa.

### 7. Pip-audit y escaneo de imágenes en CI
- **Qué:** dependencias sueltas (`>=`) en `requirements.txt` y push directo a GHCR sin escaneo.
- **Acción:** fijar versiones exactas; añadir `pip-audit` al job backend y un paso Trivy/Grype antes del push de imágenes.

---

## 🟡 Medias

### 8. Logout envían `refresh` en el body de login/register
- **Qué:** la respuesta de login/register incluye el `refresh` en JSON además de la cookie HttpOnly. Los tests lo usan; si el front lo guardara en `localStorage`, un XSS lo robaría.
- **Acción:** evaluar dejar solo la cookie; implica ajustar los tests (`accounts/tests.py` línea ~319/329).

### 9. `ALLOWED_HOSTS=*` en despliegue por túnel
- **Qué:** el `.env` local usa `localhost,127.0.0.1,*` para que el túnel temporal (host aleatorio `.trycloudflare.com`) funcione.
- **Acción:** si se adopta un dominio/URL fijo (túnel nombrado), restringir `ALLOWED_HOSTS` a dominios exactos.

### 10. Recuperación de contraseña sin SMTP real
- **Qué:** `EMAIL_BACKEND=console` en `.env` → el enlace de recuperación se imprime en logs y no llega al usuario.
- **Acción:** configurar SMTP real en producción (`.env.example` ya lo documenta) y evitar loguear el enlace completo en modo consola.

### 11. `frontend` con CDN de boxicons sin SRI
- **Qué:** los CSS de iconos se cargan desde `cdn.boxicons.com` sin `integrity`.
- **Acción:** servir los CSS de iconos localmente (build) o añadir `integrity` + `crossorigin`.

---

## ✅ Referencia de lo ya corregido (sept. 2026)

- Secretos fuera del repo: `.env`, `k8s/01-secrets.yaml`, media extraída; plantilla `k8s/01-secrets.sample.yaml`; `SECRET_KEY` rotado.
- Credenciales de superusuario eliminadas de `backend/Readme.md`.
- Compose: Postgres/Redis ya no publicados al host; Redis requiere contraseña.
- Backend: validadores de contraseña de Django en register/change/reset; `DEBUG=False` por defecto; guard de `SECRET_KEY`; `/api/token/` con throttle; rutas sensibles corregidas; docs API autenticadas; CSP aplicado; límite de body unificado a 50 MB; `logout` revoca la cookie.
- Frontend: eliminados `console.log` de credenciales; manejo de errores en reportes/dashboard/navbar/app; descarga real en preview; código muerto eliminado; `lang="es"`; `AuthService` dividido en servicios por dominio (organizacion, evaluacion, evidencias, notificaciones, reportes, dashboard, sistema).
- Ops: nginx con headers de seguridad + gzip + no-root; `backend/.dockerignore`; `backup.sh` con `pipefail`/verificación; `deploy.sh` con imágenes GHCR parametrizables; `.env.example` con clave de Redis; CI con env seguro.
- **Verificación:** 119/119 tests backend OK, ruff limpio, build de producción OK, túnel funcionando.