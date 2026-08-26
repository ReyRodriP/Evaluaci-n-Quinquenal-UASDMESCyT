"""
@file utils.py
@brief Utilidades de la app de notificaciones.
@details Funciones auxiliares para la creación de notificaciones
en el sistema.
"""

from .models import Notificacion


def crear_notificacion(usuario, titulo, mensaje):
    """@brief Crea una nueva notificación para un usuario.
    @param usuario El usuario destinatario de la notificación.
    @param titulo Título de la notificación.
    @param mensaje Mensaje detallado de la notificación.
    @return None
    """
    Notificacion.objects.create(
        usuario=usuario,
        titulo=titulo,
        mensaje=mensaje
    )
