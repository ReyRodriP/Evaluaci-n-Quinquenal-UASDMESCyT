# TODO Seguridad — Camino a Producción

Proyecto: Sistema de Evaluación Quinquenal UASD-MESCyT
Stack: Django 6 + DRF (backend) / Angular 20 (frontend)

> Estado actual (hallazgos al auditar el repo):
> - `SECRET_KEY` comiteada y `DEBUG=True` + `ALLOWED_HOSTS=['*']` en `backend/evaluacionQuinquenal/settings.py:26-31`
> - Base de datos SQLite en `settings.py:95-100`
> - Tokens `rest_framework.authtoken` sin expiración; guardados en `localStorage` (`auth-service.ts:37`)
> - Sin rate limiting en login/registro/recuperación de contraseña
> - `apiUrl` hardcodeada en el frontend (`http://localhost:8000/api`)
> - `/api/register` público (AllowAny)
> - Superusuario `omori` con contraseña débil documentada en el Readme
> - ✅ Hecho: reportes restringidos por rol (`PuedeVerReportes`), paginación en reportes y CRUDs

---

## FASE 1 — Crítico (bloquea cualquier despliegue)

- [ ] **Separar settings por entorno**
  `backend/evaluacionQuinquenal/settings.py` → `settings/base.py`, `settings/development.py`, `settings/production.py`. En producción: `DEBUG=False`, `ALLOWED_HOSTS` con el dominio real (hoy `['*']` línea 31).
- [ ] **Rotar la `SECRET_KEY` comiteada** (`settings.py:26`) y leerla desde variable de entorno vía el `load_env_file` ya existente; fallar al arrancar si no existe en prod.
- [ ] **Migrar de SQLite a PostgreSQL** (`settings.py:95-100`) con credenciales desde `.env`. SQLite no soporta concurrencia de producción ni backup online.
- [ ] **Tokens con expiración**: migrar de `rest_framework.authtoken` a `djangorestframework-simplejwt` (access ~30 min + refresh). Hoy los tokens no expiran nunca.
- [ ] **Rate limiting** en `/api/login`, `/api/register`, `/api/forgot_password`, `/api/reset_password` (ej. `django-ratelimit` o throttling de DRF). Mitiga fuerza bruta y email-bombing.
- [ ] **HTTPS obligatorio** (a nivel de servidor web o Django): `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` + `SECURE_HSTS_PRELOAD`.

## FASE 2 — Alto

- [ ] **Headers de seguridad**: verificar `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS=DENY` (middleware ya presente), `SECURE_REFERRER_POLICY`, y CSP para el frontend.
- [ ] **Token fuera de `localStorage`** (`auth-service.ts:37`): migrar a cookie `HttpOnly` + `SameSite` (o `sessionStorage` mínimo). `localStorage` es legible por cualquier XSS → robo de sesión.
- [ ] **Validación de archivos de evidencias** (`evidence/views.py`): validar extensión + MIME real + límite de tamaño en `VersionEvidencia.archivo` (revisar si ya existe validación).
- [ ] **CORS en producción**: reemplazar `http://localhost:4200` por el dominio real en `settings.py` (aparece **duplicado** en líneas 120-122 y 164-166 — limpiar) y ajustar `CORS_ALLOW_CREDENTIALS`.
- [ ] **Proteger/deshabilitar `/admin/`** de Django en producción (restringir por IP o quitar de URLs). Cambiar el superusuario `omori`/`12345678` por uno con contraseña fuerte.
- [ ] **Registrar intentos de login fallidos** en la app `auditoria` (ya existe `Auditoria` — agregar evento de login fallido).
- [ ] **Logout real en servidor**: invalidar el token en `/api/logout` (hoy `accounts/views.py:175` — verificar que no solo se borra en el cliente).

## FASE 3 — Medio

- [ ] **Logging de seguridad** en `settings.py` (`LOGGING`): errores 4xx/5xx, fallos de autenticación, acciones sensibles, con rotación de archivos.
- [ ] **Endurecer contraseñas**: `MinimumLengthValidator(10)` y verificar que `/api/register` y `/api/change_password` apliquen los validators.
- [ ] **Decidir sobre `/api/register` público** (`accounts/views.py:153`): desactivarlo en prod o restringirlo a código de invitación.
- [ ] **Frontend con `environment.ts`** de Angular (`apiUrl` por entorno). Hoy hay 2 servicios con URL hardcodeada: `core/services/auth.service.ts:9` y `features/auth/services/auth-service.ts`.
- [ ] **Backups cifrados** de BD + `media/` fuera del servidor, con plan de restauración probado.
- [ ] **`manage.py check --deploy`** sin advertencias e incluirlo en CI.
- [ ] **Revocar tokens al cambiar contraseña** (invalidar el token del usuario en `change_password`).
- [ ] **Registro público sin `group_ids`** (ya testeado) — verificar también que el registro no permita escalar permisos vía otros campos.

## FASE 4 — Bajo / Endurecimiento

- [ ] **`npm audit` + `pip-audit`** en CI (o al menos revisión mensual).
- [ ] **Pines de dependencias**: `requirements.txt` con versiones exactas (`==`) y `package-lock.json` commiteado.
- [ ] **`.env.example`** documentado con todas las variables de producción (sin valores reales). Verificar que `.env` y `db.sqlite3` permanezcan ignorados.
- [ ] **Pruebas manuales OWASP Top 10** (XSS, CSRF, IDOR, inyección SQL, exposicion de datos) antes del despliegue final.
- [ ] **Control de acceso por objeto** (IDOR): revisar endpoints `detail` (`/api/evidencias/{id}/`, `/api/versiones/{id}/descargar/`) para que un usuario no pueda leer archivos/registros de otros departamentos — `filtrar_por_rol` ya filtra querysets; verificar que aplique a todos los actions.

---

## Comandos de verificación

```bash
# Backend
python manage.py check --deploy
python manage.py check
python manage.py test

# Frontend
npm audit
ng build --configuration production
```
