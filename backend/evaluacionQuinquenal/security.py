"""
@file security.py
@brief Middleware y configuraciones de seguridad para el sistema
@details Implementa cabeceras de seguridad HTTP, proteccion contra XSS,
clickjacking, MIME sniffing, rate limiting avanzado, bloqueo de IPs
y otras medidas de seguridad para proteger la aplicacion.
"""

import logging
import re

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    """
    @brief Obtiene la IP real del cliente desde el request
    @param request Request HTTP de Django
    @return String con la IP del cliente
    @details Soporta X-Forwarded-For para proxies y load balancers.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


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
            ip = _get_client_ip(request)
            cache_key = f"login_attempts_{ip}"
            attempts = cache.get(cache_key, 0)

            if attempts >= self.MAX_ATTEMPTS:
                logger.warning(f"Login bloqueado para IP {ip}: {attempts} intentos fallidos")
                return JsonResponse(
                    {"error": "Demasiados intentos. Intente de nuevo en 15 minutos."},
                    status=403,
                )

        response = self.get_response(request)

        if request.path.endswith("/login") and request.method == "POST":
            ip = _get_client_ip(request)
            cache_key = f"login_attempts_{ip}"

            if response.status_code == 400:
                attempts = cache.get(cache_key, 0) + 1
                cache.set(cache_key, attempts, self.LOCKOUT_SECONDS)
            else:
                cache.delete(cache_key)

        return response


class RateLimitMiddleware:
    """
    @class RateLimitMiddleware
    @brief Middleware de rate limiting general por IP
    @details Limita el numero de requests por IP en un periodo de tiempo.
    Bloquea temporalmente IPs que excedan el limite maximo.
    Implementa rate limiting escalado: 60/min general, 20/min para endpoints sensibles.
    """

    GENERAL_LIMIT = 120
    SENSITIVE_LIMIT = 20
    BLOCK_DURATION = 600

    SENSITIVE_PATHS = {"/login", "/register", "/forgot_password", "/reset_password", "/change_password"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = _get_client_ip(request)

        block_key = f"ip_blocked_{ip}"
        if cache.get(block_key):
            logger.warning(f"IP bloqueada: {ip}")
            return JsonResponse(
                {"error": "Su IP ha sido bloqueada temporalmente por exceso de solicitudes."},
                status=429,
            )

        is_sensitive = request.path in self.SENSITIVE_PATHS
        limit = self.SENSITIVE_LIMIT if is_sensitive else self.GENERAL_LIMIT
        cache_key = f"rate_limit_{ip}_{request.path}"

        request_count = cache.get(cache_key, 0)
        if request_count >= limit:
            cache.set(block_key, True, self.BLOCK_DURATION)
            logger.warning(f"Rate limit excedido para IP {ip} en {request.path}: {request_count} requests")
            return JsonResponse(
                {"error": "Demasiadas solicitudes. Su IP ha sido bloqueada temporalmente."},
                status=429,
            )

        cache.set(cache_key, request_count + 1, 60)

        return self.get_response(request)


class RequestSizeLimitMiddleware:
    """
    @class RequestSizeLimitMiddleware
    @brief Middleware para limitar el tamanio del body de requests
    @details Rechaza requests con body excesivamente grande para prevenir
    ataques de denegacion de servicio (DoS) por payload grande.
    """

    MAX_BODY_SIZE = 10 * 1024 * 1024

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.META.get("CONTENT_LENGTH", "")
            if content_length and content_length.isdigit():
                if int(content_length) > self.MAX_BODY_SIZE:
                    logger.warning(
                        f"Request rechazado: body excesivamente grande "
                        f"({content_length} bytes) desde {_get_client_ip(request)}"
                    )
                    return JsonResponse(
                        {"error": "El tamanio del request excede el limite permitido."},
                        status=413,
                    )

        return self.get_response(request)


class QueryParameterLimitMiddleware:
    """
    @class QueryParameterLimitMiddleware
    @brief Middleware para limitar la cantidad de query parameters
    @details Previene ataques de denegacion de servicio mediante
    URLs con excesivos parametros de consulta.
    """

    MAX_QUERY_PARAMS = 20

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if len(request.GET) > self.MAX_QUERY_PARAMS:
            logger.warning(
                f"Request rechazado: exceso de query params ({len(request.GET)}) desde {_get_client_ip(request)}"
            )
            return JsonResponse(
                {"error": f"Exceso de parametros de consulta (maximo {self.MAX_QUERY_PARAMS})."},
                status=400,
            )

        return self.get_response(request)


class SQLInjectionProtectionMiddleware:
    """
    @class SQLInjectionProtectionMiddleware
    @brief Middleware basico para detectar patrones de SQL injection
    @details Analiza los query parameters y el body en busca de patrones
    sospechosos de inyeccion SQL y bloquea el request si detecta alguno.
    """

    SQL_PATTERNS = [
        r"(?i)(\bunion\b.*\bselect\b)",
        r"(?i)(\bselect\b.*\bfrom\b.*\bwhere\b)",
        r"(?i)(\binsert\b.*\binto\b)",
        r"(?i)(\bdelete\b.*\bfrom\b)",
        r"(?i)(\bdrop\b.*\btable\b)",
        r"(?i)(\bupdate\b.*\bset\b)",
        r"(?i)(\bor\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?)",
        r"(?i)(\band\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?)",
        r"(?i)(;?\s*--)",
        r"(?i)(;?\s*\/\*.*\*\/)",
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self._compiled = [re.compile(p) for p in self.SQL_PATTERNS]

    def __call__(self, request):
        for param_value in request.GET.values():
            if self._detect_injection(param_value):
                logger.warning(
                    f"Posible SQL injection detectada desde {_get_client_ip(request)}: param={param_value[:100]}"
                )
                return JsonResponse(
                    {"error": "Parametros de solicitud invalidos."},
                    status=400,
                )

        if request.method in ("POST", "PUT", "PATCH") and hasattr(request, "body"):
            try:
                body = request.body.decode("utf-8", errors="ignore")[:2000]
                if self._detect_injection(body):
                    logger.warning(f"Posible SQL injection en body desde {_get_client_ip(request)}")
                    return JsonResponse(
                        {"error": "Contenido de solicitud invalido."},
                        status=400,
                    )
            except Exception:
                pass

        return self.get_response(request)

    def _detect_injection(self, value):
        if not isinstance(value, str):
            return False
        return any(p.search(value) for p in self._compiled)


class BotProtectionMiddleware:
    """
    @class BotProtectionMiddleware
    @brief Middleware para detectar y bloquear bots maliciosos
    @details Analiza el User-Agent para detectar bots conocidos
    y bloquear sus requests.
    """

    BLOCKED_USER_AGENTS = [
        r"(?i)sqlmap",
        r"(?i)nikto",
        r"(?i)nmap",
        r"(?i)masscan",
        r"(?i)zgrab",
        r"(?i)gobuster",
        r"(?i)dirbuster",
        r"(?i)wfuzz",
        r"(?i)havij",
        r"(?i)acunetix",
        r"(?i)netsparker",
        r"(?i)openvas",
        r"(?i)nessus",
        r"(?i)burpsuite",
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self._compiled = [re.compile(p) for p in self.BLOCKED_USER_AGENTS]

    def __call__(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if user_agent:
            for pattern in self._compiled:
                if pattern.search(user_agent):
                    logger.warning(f"Bot bloqueado: {user_agent[:100]} desde {_get_client_ip(request)}")
                    return JsonResponse(
                        {"error": "Solicitud no permitida."},
                        status=403,
                    )

        return self.get_response(request)


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
                            return JsonResponse(
                                {"error": "Tipo de archivo no permitido"},
                                status=403,
                            )

                        if uploaded_file.content_type not in self.ALLOWED_MIME_TYPES:
                            logger.warning(
                                f"Archivo rechazado: {uploaded_file.name} "
                                f"(MIME type no permitido: {uploaded_file.content_type})"
                            )
                            return JsonResponse(
                                {"error": "Tipo de archivo no permitido"},
                                status=403,
                            )

                        if uploaded_file.size > self.MAX_FILE_SIZE:
                            logger.warning(
                                f"Archivo rechazado: {uploaded_file.name} "
                                f"(tamanio {uploaded_file.size} excede maximo {self.MAX_FILE_SIZE})"
                            )
                            return JsonResponse(
                                {"error": "Archivo excede el tamanio maximo de 50MB"},
                                status=403,
                            )

        return self.get_response(request)
