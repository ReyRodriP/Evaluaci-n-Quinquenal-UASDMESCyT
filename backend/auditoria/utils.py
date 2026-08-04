from .models import Auditoria


def registrar_auditoria(usuario, accion, modelo, registro_id=None, descripcion=""):
    Auditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        accion=accion,
        modelo=modelo,
        registro_id=registro_id,
        descripcion=descripcion
    )
