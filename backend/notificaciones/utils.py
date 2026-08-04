from .models import Notificacion


def crear_notificacion(usuario, titulo, mensaje):
    Notificacion.objects.create(
        usuario=usuario,
        titulo=titulo,
        mensaje=mensaje
    )
