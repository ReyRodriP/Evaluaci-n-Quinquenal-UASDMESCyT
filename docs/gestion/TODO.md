# Auditoria del Proyecto — Evaluacion Quinquenal UASD-MESCyT

**Fecha de auditoria:** 2026-08-26
**Actualizado:** 2026-09-14
**Auditor:** opencode (automatizado)

---

## Estado Actual del Proyecto

| Componente | Estado |
|------------|--------|
| Backend (Django 6 + DRF) | Funcional |
| Frontend (Angular 20) | Funcional |
| Base de datos | SQLite (dev) / PostgreSQL (prod) |
| Docker | Configurado |
| Kubernetes | Configurado |
| Tests | 114 tests en 11 apps (incl. health) |
| Linter/Formatter | Ruff (0 errores, formato aplicado) |
| Autenticacion | JWT simplejwt + blacklist |
| Seguridad | 19 medidas implementadas |

---

## FASE 1 — Completado

- [x] **Separar settings por entorno** — Variables de entorno via `load_env_file`, `DEBUG` y `SECRET_KEY` configurables
- [x] **Rotar SECRET_KEY** — Desde variable de entorno, fallback solo en desarrollo
- [x] **Migrar a PostgreSQL** — Soporte via `DB_ENGINE`, `DB_NAME`, etc.
- [x] **Rate limiting** — Login (5/min), register (3/min), change_password (3/hour), general (120/min)
- [x] **HTTPS forzado** — `SECURE_SSL_REDIRECT`, `HSTS`, `Secure cookies` en produccion

---

## FASE 2 — Completado

- [x] **Headers de seguridad** — `SecurityHeadersMiddleware` (X-Frame, XSS, HSTS, CSP)
- [x] **Validacion de archivos** — `FileUploadSecurityMiddleware` (MIME, extension, 50MB)
- [x] **CORS configurable** — Via `CORS_ALLOWED_ORIGINS` env var
- [x] **Logout real** — Token eliminado en servidor
- [x] **Proteger /admin/** — Comentario en urls.py, proteger con VPN/IP en produccion
- [x] **Log login fallidos** — Registrados en modelo Auditoria con IP del cliente
- [x] **Token fuera de localStorage** — NOT DONE (requiere cambio en frontend auth flow)

---

## FASE 3 — Completado

- [x] **Logging de seguridad** — `LOGGING` configurado con RotatingFileHandler (5MB, 5 backups)
- [x] **Endurecer contrasenas** — Minimo 10 caracteres + validadores de Django
- [x] **Frontend environment.ts** — `environment.ts` (dev) y `environment.prod.ts` (prod)
- [x] **manage.py check --deploy** — Sin errores
- [x] **Revocar tokens al cambiar contrasena** — Token eliminado en `change_password`
- [x] **Register publico controlado** — Rate limiting (3/min) + validacion de entrada

---

## FASE 4 — Completado

- [x] **Pines de dependencias** — requirements.txt con versiones (== o >= para evitar conflictos)
- [x] **.env.example** — Documentado con todas las variables
- [x] **Ruff** — Linter y formatter configurado, 0 errores, formato aplicado
- [x] **Ruff en CI** — `ruff check` + `ruff format --check` en el pipeline

---

## Seguridad Implementada (19 medidas)

| # | Medida | Estado |
|---|--------|--------|
| 1 | Ocultar claves API | ✅ SECRET_KEY desde env var |
| 2 | Eliminar secretos de git | ✅ .gitignore completo |
| 3 | Clave publica DB | ✅ Parametrizada via env vars |
| 4 | Seguridad row-level | ✅ filtrar_por_rol() |
| 5 | Cifrado de datos | ✅ Argon2 password hasher |
| 6 | Forzar autenticacion | ✅ IsAuthenticated default |
| 7 | Restringir registros | ✅ Filtrado por departamento |
| 8 | Bloquear manipulacion | ✅ read_only_fields |
| 9 | Proteger cookies | ✅ httponly, secure, samesite |
| 10 | Hashear contrasenas | ✅ Argon2 + PBKDF2 |
| 11 | Limitar login | ✅ 5 intentos / 15 min lockout |
| 12 | Proteccion bots | ✅ Throttling + User-Agent blocking |
| 13 | Parametrizar consultas | ✅ Django ORM |
| 14 | Validar entradas | ✅ Serializers con validaciones |
| 15 | Escapar contenido | ✅ CSP headers |
| 16 | Restringir archivos | ✅ MIME, extension, tamanio |
| 17 | Limitar API | ✅ Throttling global |
| 18 | Cabeceras seguridad | ✅ SecurityHeadersMiddleware |
| 19 | Forzar HTTPS | ✅ SSL redirect + HSTS |

---

## Pendiente para Produccion

### Critico
- [x] **Migrar tokens a JWT** — simplejwt completo: `token_blacklist` instalado, authtoken eliminado, vistas con Bearer, endpoints `/api/token/`, rotacion con blacklist, revocacion de tokens JWT al cambiar contrasena
- [x] **Token fuera de localStorage** — Access de 30min en cookie JS + header `Bearer`; **refresh de 7 dias en cookie HttpOnly** (no legible por JS) con endpoint `/api/token/refresh/cookie/` (rotacion + blacklist) y `withCredentials` en el frontend; logout elimina la cookie
- [x] **Backups cifrados** — `backup.sh` con cifrado AES-256-CBC (openssl + pbkdf2), passphrase via `BACKUP_PASSPHRASE`, rotacion de 30 dias
- [x] **CI/CD** — Pipeline con lint (ruff check+format), tests, `manage.py check` y build/push de imagenes Docker a GHCR en main

### Alto
- [~] **Monitoreo** — Sentry configurado en settings; falta definir `SENTRY_DSN` real en produccion
- [x] **Health checks** — Endpoint `/health/` con DB, cache (Redis/locmem) y media; probes k8s corregidos a `/health/`; manifiesto Redis agregado
- [x] **Rate limiting por usuario** — Throttle global por usuario + `ScopedRateThrottle` por usuario en `change_password` (3/hora)
- [x] **Rotacion de tokens** — `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`, refresh y access blacklistables (OutstandingToken en login/register)

### Medio
- [x] **Reportes PDF/Excel** — reportlab y openpyxl generan PDF/XLSX con endpoints de exportacion
- [x] **Notificaciones por email** — copia por email al crear notificaciones si hay SMTP configurado (`NOTIFICACIONES_EMAIL_ENABLED`), fallos no rompen la BD. SMTP real queda configurable por env (`.env.example`)
- [x] **Exportar datos** — CSV/Excel accesibles desde el frontend (botones en reportes)
- [x] **Performance** — Redis configurado (`REDIS_URL`); caching de 60s en consultas frecuentes del dashboard (resumen, avance)

### Bajo
- [x] **Documentacion API** — Swagger/OpenAPI en `/api/docs/` con `@extend_schema` (tags/params/tipos) en reportes, search, logs; type hints en serializers; `check --deploy` sin W001/W002 (0 avisos drf-spectacular)
- [~] **Internacionalizacion** — Backend: `LANGUAGE_CODE=es`, `America/Santo_Domingo`, `LANGUAGES` es/en. Pendiente: traducciones gettext + `@angular/localize` en frontend
- [~] **Accesibilidad** — `alt`, `role`, `aria-*`, `for`/`id`, teclado, foco visible + skip-link. Pendiente: auditoria WCAG formal
- [x] **Tests de carga** — `loadtests/locustfile.py` (locust) con 100+ usuarios concurrentes

---

## TODO Abierto (no bloqueante / requiere credenciales externas)

- [ ] **Sentry DSN real** — infra lista: `SENTRY_DSN` ya se inyecta desde el Secret de k8s; solo falta pegar el DSN real
- [ ] **SMTP real** — infra lista (`EMAIL_HOST*` en `.env`); solo falta poner credenciales reales
- [ ] **Dominio + certificado HTTPS** — `SECURE_SSL_REDIRECT=True` y HSTS listos; el 05-ingress.yaml necesita hostname real y cert
- [ ] **Rotar los secretos de k8s** — `01-secrets.yaml` trae valores fuertes pero de DEMO; rotarlos en prod (SealedSecrets/External-Secrets)
- [ ] **Token GHCR en el CI** — el job `docker` del pipeline push necesita ese token
- [ ] **Traducciones gettext** (backend) y `@angular/localize` (frontend) — i18n completa
- [ ] **Auditoria WCAG** formal (lighthouse/axe)
- [ ] **Tests de carga** contra el entorno desplegado (locust)

---

## Produccion (resuelto)

- [x] **`check --deploy` en 0 avisos** con `DEBUG=False` + `SECRET_KEY` real + HTTPS
- [x] **Guarda de SECRET_KEY** — el backend aborta en produccion si la clave es la de dev
- [x] **`SECURE_SSL_REDIRECT`** por defecto `True` en produccion (sobreescribible)
- [x] **Secretos k8s** — valores fuertes + `BACKUP_PASSPHRASE` + `SENTRY_DSN` (inyectado al backend)
- [x] **Backup automatizado** — CronJob diario (02:00) con cifrado AES-256-CBC y retencion de 30 dias
- [x] **deploy.sh** — incluye Redis, backups, migraciones y collectstatic

---

## Comandos de Verificacion

```bash
# Backend (usar ./backend/.venv)
cd backend
.venv/Scripts/ruff check .
.venv/Scripts/ruff format .
.venv/Scripts/ruff format . --check
.venv/Scripts/python manage.py check
.venv/Scripts/python manage.py check --deploy
.venv/Scripts/python manage.py test

# Frontend
cd frontend/evaluacion-quinquenal-front
ng build --configuration production
npm audit

# Tests de carga
pip install locust
locust -f loadtests/locustfile.py --host http://localhost:8000 -u 100 -r 10 -t 5m
```

---

## Archivos Clave

| Archivo | Descripcion |
|---------|-------------|
| `backend/evaluacionQuinquenal/settings.py` | Configuracion principal |
| `backend/evaluacionQuinquenal/security.py` | Middleware de seguridad |
| `backend/accounts/views.py` | Vistas de autenticacion |
| `backend/accounts/serializers.py` | Validaciones de entrada |
| `backend/accounts/permissions.py` | Permisos por rol |
| `pyproject.toml` | Configuracion de Ruff |
| `docker-compose.yml` | Servicios Docker |
| `k8s/` | Manifiestos Kubernetes (incluye `06-redis.yaml`) |
| `backup.sh` | Backup cifrado AES-256 (DB + media) |
| `.github/workflows/ci.yml` | Pipeline CI/CD (lint, tests, Docker) |
| `frontend/src/environments/` | Variables de entorno Angular |
