"""
@file utils.py
@brief Utilidades de la app de notificaciones.
@details Funciones auxiliares para la creación de notificaciones
en el sistema, incluyendo envío de correo cuando esta habilitado.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Notificacion

logger = logging.getLogger("auditoria")


def crear_notificacion(usuario, titulo, mensaje):
    """@brief Crea una nueva notificación para un usuario.
    @param usuario El usuario destinatario de la notificación.
    @param titulo Título de la notificación.
    @param mensaje Mensaje detallado de la notificación.
    @return None
    @details Si NOTIFICACIONES_EMAIL_ENABLED esta activo y el usuario
    tiene correo, se envia una copia por email. Fallos de email no rompen
    la notificacion en BD.
    """
    Notificacion.objects.create(usuario=usuario, titulo=titulo, mensaje=mensaje)

    if settings.NOTIFICACIONES_EMAIL_ENABLED and usuario and getattr(usuario, "email", None):
        try:
            send_mail(
                subject=f"[Evaluacion Quinquenal] {titulo}",
                message=f"{mensaje}\n\n---\nSistema de Evaluacion Quinquenal UASD-MESCyT",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                fail_silently=False,
            )
        except Exception:
            logger.warning("No se pudo enviar email de notificacion a %s", usuario.email)
