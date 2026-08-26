"""
@file settings.py
@brief Configuracion del proyecto Evaluacion Quinquenal.
@details Define la configuracion de Django para el proyecto,
incluyendo bases de datos, aplicaciones instaladas,
middleware, autenticacion, CORS, seguridad y otras
configuraciones del sistema.
"""

import os
from datetime import timedelta
from pathlib import Path


def load_env_file(path: Path) -> None:
    """
    @brief Carga variables de entorno desde un archivo .env
    @param path Ruta al archivo .env
    @details Lee el archivo linea por linea, ignorando comentarios
    y lineas vacias, y establece las variables de entorno.
    """
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_env_file(BASE_DIR / ".env")


# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# 1. Ocultar claves API - SECRET_KEY desde variable de entorno
SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-insecure-cambiar-en-produccion-w@ii_-rppf_7)*7u10w!cfz!u*lu^$g$0souiqh6!oy42m(73z"
)

# 19. Forzar HTTPS en produccion
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes", "on")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "organization",
    "corsheaders",
    "evaluation",
    "evidence",
    "auditoria",
    "notificaciones",
    "evidencias",
    "dashboard",
    "search",
    "reportes",
    "drf_spectacular",
]


# =============================================================================
# MIDDLEWARE - 18. Cabeceras de seguridad
# =============================================================================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "evaluacionQuinquenal.security.SecurityHeadersMiddleware",
    "evaluacionQuinquenal.security.BotProtectionMiddleware",
    "evaluacionQuinquenal.security.RateLimitMiddleware",
    "evaluacionQuinquenal.security.LoginRateLimitMiddleware",
    "evaluacionQuinquenal.security.RequestSizeLimitMiddleware",
    "evaluacionQuinquenal.security.QueryParameterLimitMiddleware",
    "evaluacionQuinquenal.security.SQLInjectionProtectionMiddleware",
    "evaluacionQuinquenal.security.FileUploadSecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if not DEBUG:
    pass

ROOT_URLCONF = "evaluacionQuinquenal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "evaluacionQuinquenal.wsgi.application"


# =============================================================================
# DATABASE - 3. Clave publica DB
# =============================================================================

AUTH_USER_MODEL = "accounts.Usuario"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
        "OPTIONS": {},
    }
}


# =============================================================================
# PASSWORD VALIDATION - 10. Hashear contrasenas
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]


# =============================================================================
# CORS - 6. Forzar autenticacion
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:4200,http://localhost,http://frontend,http://frontend:4200"
    ).split(",")
    if origin.strip()
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")


# =============================================================================
# EMAIL
# =============================================================================

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("1", "true", "yes", "on")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@uasd.edu.do")


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# =============================================================================
# REST FRAMEWORK - 11. Limitar login, 12. Proteccion bots, 17. Limitar API
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "100/minute",
        "login": "5/minute",
        "register": "3/minute",
        "change_password": "3/hour",
        "password_reset": "3/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "MAX_PAGE_SIZE": 200,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Evaluacion Quinquenal UASD-MESCyT API",
    "DESCRIPTION": "API para la gestion de evidencias de evaluacion quinquenal",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# =============================================================================
# SIMPLE JWT - Tokens con expiracion
# =============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
}


# =============================================================================
# MEDIA FILES - 16. Restringir archivos
# =============================================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024


# =============================================================================
# 9. Proteger cookies
# =============================================================================

SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = False

CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"


# =============================================================================
# 19. Forzar HTTPS
# =============================================================================

SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if not DEBUG else None
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"


# =============================================================================
# 14. Validar entradas
# =============================================================================

DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
DATA_UPLOAD_MAX_NUMBER_FILES = 10


# =============================================================================
# 15. Escapar contenido del usuario
# =============================================================================

SECURE_CSP = {
    "default-src": "'self'",
    "script-src": "'self'",
    "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src": "'self' https://fonts.gstatic.com",
    "img-src": "'self' data:",
    "connect-src": "'self'",
}


# =============================================================================
# AUDITORIA
# =============================================================================

LOGIN_REDIRECT_URL = "/api/"
LOGOUT_REDIRECT_URL = "/api-auth/login/"


# =============================================================================
# LOGGING - Rotacion de archivos, seguridad y auditoria
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "security.log",
            "maxBytes": 5 * 1024 * 1024,  # 5MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.security": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": True,
        },
        "auditoria": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}


# =============================================================================
# CACHE
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}
if os.getenv("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.redis.cache.RedisCache",
            "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        }
    }


# =============================================================================
# SENTRY
# =============================================================================

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=True,
        )
    except ImportError:
        pass
