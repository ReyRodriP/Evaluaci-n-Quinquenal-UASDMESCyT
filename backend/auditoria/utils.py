"""
@file utils.py
@brief Utilidades de la app de auditoría.
@details Funciones auxiliares para el registro de auditoría
en el sistema.
"""

from .models import Auditoria


def registrar_auditoria(usuario, accion, modelo, registro_id=None, descripcion=""):
    """@brief Registra una entrada de auditoría en el sistema.
    @param usuario El usuario que realizó la acción. Puede ser None
    si el usuario no está autenticado.
    @param accion Descripción corta de la acción realizada.
    @param modelo Nombre del modelo afectado por la acción.
    @param registro_id ID del registro afectado. Puede ser None
    si la acción no está vinculada a un registro específico.
    @param descripcion Descripción detallada de la acción realizada.
    @return None
    """
    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        accion=accion,
        modelo=modelo,
        registro_id=registro_id,
        descripcion=descripcion,
    )
