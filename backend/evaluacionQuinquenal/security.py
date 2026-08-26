"""
@file security.py
@brief Middleware y configuraciones de seguridad para el sistema
@details Implementa cabeceras de seguridad HTTP, proteccion contra XSS,
clickjacking, MIME sniffing, y otras medidas de seguridad para
proteger la aplicacion de ataques comunes.
"""

import logging

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    @class SecurityHeadersMiddleware
    @brief Middleware que agrega cabeceras de seguridad HTTP
    @details Agrega X-Content-Type-Options, X-Frame-Options,
    X-XSS-Protection, Strict-Transport-Security y otras cabeceras
    de seguridad a todas las respuestas HTTP.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response["X-Permitted-Cross-Domain-Policies"] = "none"

        if hasattr(settings, "SECURE_SSL_REDIRECT") and settings.SECURE_SSL_REDIRECT:
            response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response


class LoginRateLimitMiddleware:
    """
    @class LoginRateLimitMiddleware
    @brief Middleware para limitar intentos de login por IP
    @details Bloquea temporalmente IPs que excedan el limite de intentos
    de login en un periodo de tiempo determinado.
    """

    MAX_ATTEMPTS = 5
    LOCKOUT_SECONDS = 900

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.endswith("/login") and request.method == "POST":
            ip = self._get_client_ip(request)
            cache_key = f"login_attempts_{ip}"
            attempts = cache.get(cache_key, 0)

            if attempts >= self.MAX_ATTEMPTS:
                logger.warning(f"Login bloqueado para IP {ip}: {attempts} intentos fallidos")
                return HttpResponseForbidden(
                    '{"error": "Demasiados intentos. Intente de nuevo en 15 minutos."}', content_type="application/json"
                )

        response = self.get_response(request)

        if request.path.endswith("/login") and request.method == "POST":
            ip = self._get_client_ip(request)
            cache_key = f"login_attempts_{ip}"

            if response.status_code == 400:
                attempts = cache.get(cache_key, 0) + 1
                cache.set(cache_key, attempts, self.LOCKOUT_SECONDS)
            else:
                cache.delete(cache_key)

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")


class FileUploadSecurityMiddleware:
    """
    @class FileUploadSecurityMiddleware
    @brief Middleware para validar archivos subidos
    @details Verifica tipos MIME, extensiones y tamanos de archivos
    antes de permitir su carga al servidor.
    """

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".txt",
        ".csv",
        ".json",
        ".xml",
        ".zip",
        ".rar",
    }

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp",
        "text/plain",
        "text/csv",
        "application/json",
        "application/xml",
        "application/zip",
        "application/x-rar-compressed",
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ("POST", "PUT", "PATCH") and request.content_type:
            if "multipart/form-data" in request.content_type:
                if hasattr(request, "FILES"):
                    for field_name, uploaded_file in request.FILES.items():
                        ext = "." + uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""

                        if ext not in self.ALLOWED_EXTENSIONS:
                            logger.warning(f"Archivo rechazado: {uploaded_file.name} (extension no permitida: {ext})")
                            return HttpResponseForbidden(
                                '{"error": "Tipo de archivo no permitido"}', content_type="application/json"
                            )

                        if uploaded_file.content_type not in self.ALLOWED_MIME_TYPES:
                            logger.warning(
                                f"Archivo rechazado: {uploaded_file.name} "
                                f"(MIME type no permitido: {uploaded_file.content_type})"
                            )
                            return HttpResponseForbidden(
                                '{"error": "Tipo de archivo no permitido"}', content_type="application/json"
                            )

                        if uploaded_file.size > self.MAX_FILE_SIZE:
                            logger.warning(
                                f"Archivo rechazado: {uploaded_file.name} "
                                f"(tamanio {uploaded_file.size} excede maximo {self.MAX_FILE_SIZE})"
                            )
                            return HttpResponseForbidden(
                                '{"error": "Archivo excede el tamanio maximo de 50MB"}', content_type="application/json"
                            )

        return self.get_response(request)
