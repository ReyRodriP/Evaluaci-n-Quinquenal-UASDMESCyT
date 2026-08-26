# Auditoria del Proyecto — Evaluacion Quinquenal UASD-MESCyT

**Fecha de auditoria:** 2026-08-26
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
| Tests | 92 tests en 10 apps |
| Linter/Formatter | Ruff (0 errores) |
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

- [x] **Pines de dependencias** — requirements.txt con versiones exactas (==)
- [x] **.env.example** — Documentado con todas las variables
- [x] **Ruff** — Linter y formatter configurado, 0 errores

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
- [ ] **Migrar tokens a JWT** — `rest_framework.authtoken` no tiene expiracion. Migrar a `djangorestframework-simplejwt` (access 30min + refresh)
- [ ] **Token fuera de localStorage** — Migrar a cookie HttpOnly + SameSite para prevenir robo por XSS
- [ ] **Backups cifrados** — Configurar backups automaticos de BD + media con cifrado AES-256
- [ ] **CI/CD** — Pipeline automatizado con tests, lint, build y deploy

### Alto
- [ ] **Monitoreo** — Integrar Sentry o similar para errores en produccion
- [ ] **Health checks** — Endpoint `/health/` para monitoreo de disponibilidad
- [ ] **Rate limiting por usuario** — Throttling basado en usuario autenticado, no solo IP
- [ ] **Rotacion de tokens** — Invalidar tokens antiguos despues de cierto tiempo

### Medio
- [ ] **Reportes PDF/Excel** — Verificar que reportlab y openpyxl generan archivos correctos
- [ ] **Notificaciones por email** — Configurar SMTP real en produccion
- [ ] **Exportar datos** — Funcionalidad de exportar CSV/Excel desde el frontend
- [ ] **Perfomance** — Agregar caching (Redis) para consultas frecuentes

### Bajo
- [ ] **Documentacion API** — Swagger/OpenAPI para documentar endpoints
- [ ] **Internacionalizacion** — i18n para espanol/ingles
- [ ] **Accesibilidad** — WCAG 2.1 compliance
- [ ] **Tests de carga** — Pruebas con 100+ usuarios concurrentes

---

## Comandos de Verificacion

```bash
# Backend
python manage.py check
python manage.py check --deploy
python manage.py test
ruff check backend/
ruff format backend/ --check

# Frontend
ng build --configuration production
npm audit
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
| `k8s/` | Manifiestos Kubernetes |
| `frontend/src/environments/` | Variables de entorno Angular |
