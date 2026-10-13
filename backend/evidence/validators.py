"""Validadores comunes para archivos de evidencia."""
from __future__ import annotations

from rest_framework import serializers


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".txt",
    ".zip",
    ".rar",
}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
    "image/gif",
    "text/plain",
    "application/zip",
    "application/x-rar-compressed",
    "application/vnd.rar",
}

MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_evidence_file(file) -> None:
    """Valida tipo, extensión y tamaño máximo (50 MB) del archivo."""
    if file is None:
        raise serializers.ValidationError("Debe adjuntar un archivo.")

    filename = getattr(file, "name", "") or ""
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    content_type = getattr(file, "content_type", "") or ""

    if ext and ext not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            f"Extensión de archivo '{ext}' no permitida. Extensiones permitidas: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF, TXT, ZIP, RAR"
        )

    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise serializers.ValidationError(
            f"Tipo de archivo '{content_type}' no permitido. Tipos permitidos: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF, TXT, ZIP, RAR"
        )

    try:
        size = file.size
    except Exception:
        size = getattr(file, "file", None)
        try:
            if hasattr(size, "size"):
                size = size.size
            else:
                size = None
        except Exception:
            size = None

    if size is not None and size > MAX_FILE_SIZE_BYTES:
        raise serializers.ValidationError("El archivo no puede superar los 50 MB.")

    # Validación de contenido básica: detectar truncamiento/archivo vacío si es posible
    try:
        pos = file.tell()
    except Exception:
        pos = None
    try:
        file.seek(0, 2)
        total = file.tell()
        if total == 0:
            raise serializers.ValidationError("El archivo está vacío.")
        file.seek(pos if pos is not None else 0)
    except serializers.ValidationError:
        raise
    except Exception:
        try:
            if pos is not None:
                file.seek(pos)
        except Exception:
            pass
