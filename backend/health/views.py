from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def _check_database():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return "error"
    else:
        return "ok"


def _check_cache():
    try:
        from django.core.cache import caches

        backend = caches["default"]
        backend.set("health_check", "1", 5)
        return "ok" if backend.get("health_check") == "1" else "error"
    except Exception:
        return "error"


def _check_media():
    try:
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if media_root is None:
            return "error"
        Path(media_root).mkdir(parents=True, exist_ok=True)
        return "ok" if Path(media_root).is_dir() else "error"
    except Exception:
        return "error"


def health_check(request):
    database = _check_database()
    cache_status = _check_cache()
    media = _check_media()

    components = {
        "database": database,
        "cache": cache_status,
        "media": media,
    }

    status = "healthy" if all(value == "ok" for value in components.values()) else "degraded"
    status_code = 200 if status == "healthy" else 503

    return JsonResponse(
        {
            "status": status,
            "components": components,
        },
        status=status_code,
    )
