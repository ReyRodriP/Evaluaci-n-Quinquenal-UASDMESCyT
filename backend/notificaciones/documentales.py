"""Avisos documentales con destinatarios actuales, destinos internos y correo tras commit."""

from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.permissions import ROLES_SIN_RESTRICCION, _grupos_usuario, filtrar_por_rol
from evaluation.models import Asignacion

from .models import DestinoNotificacionDocumental, Notificacion
from .utils import enviar_correo_notificacion


def asignaciones_notificables(request):
    usuario = request.user
    if not usuario.is_active or not usuario.has_perms(['evaluation.view_asignacion', 'evidence.view_evidencia']):
        return Asignacion.objects.none()
    grupos = _grupos_usuario(usuario)
    if 'Evaluador Externo' in grupos and not (usuario.is_superuser or grupos & ROLES_SIN_RESTRICCION):
        return Asignacion.objects.none()
    return filtrar_por_rol(Asignacion.objects.all(), request, dept_field='unidad_responsable')


def puede_recibir_documentales(usuario, asignacion, *, revision=False):
    grupos = _grupos_usuario(usuario)
    if revision and ('Revisor Institucional' not in grupos or not usuario.has_perm('evaluation.change_asignacion')):
        return False
    request = SimpleNamespace(user=usuario, query_params={})
    return asignaciones_notificables(request).filter(pk=asignacion.pk).exists()


def _correo_tras_commit(usuario_id, asignacion_id, titulo, mensaje, revision):
    usuario = get_user_model().objects.filter(pk=usuario_id, is_active=True).first()
    asignacion = Asignacion.objects.filter(pk=asignacion_id).first()
    if usuario and asignacion and puede_recibir_documentales(usuario, asignacion, revision=revision):
        enviar_correo_notificacion(usuario, titulo, mensaje)


def _programar_correo(usuario_id, asignacion_id, titulo, mensaje, revision):
    def entregar_correo():
        _correo_tras_commit(usuario_id, asignacion_id, titulo, mensaje, revision)

    transaction.on_commit(entregar_correo, robust=True)


def _avisar(asignacion, actor, destinatarios, titulo, mensaje, *, solicitud=None, version=None, revision=False):
    """El conjunto de IDs evita duplicar el aviso cuando encargado y autor coinciden."""
    ids = set(destinatarios) - {None, actor.pk}
    for usuario in get_user_model().objects.filter(pk__in=ids, is_active=True).order_by('pk'):
        if not puede_recibir_documentales(usuario, asignacion, revision=revision):
            continue
        with transaction.atomic():
            aviso = Notificacion.objects.create(usuario=usuario, titulo=titulo, mensaje=mensaje)
            destino = DestinoNotificacionDocumental(notificacion=aviso, asignacion=asignacion, solicitud=solicitud, version=version)
            destino.full_clean()
            destino.save()
            _programar_correo(usuario.pk, asignacion.pk, titulo, mensaje, revision)


def avisar_solicitud(solicitud, actor, *, accion='creada'):
    asignacion = solicitud.asignacion
    titulos = {'creada': 'Nueva solicitud documental', 'actualizada': 'Solicitud documental actualizada', 'retirada': 'Solicitud documental retirada'}
    mensaje = (f'Solicitud {solicitud.pk}: {solicitud.titulo}. Asignación {asignacion.pk}: {asignacion.indicador_nombre}. '
        f'Unidad: {asignacion.unidad_responsable.nombre}. Período: {asignacion.periodo.nombre}.')
    _avisar(asignacion, actor, [asignacion.encargado_id], titulos[accion], mensaje, solicitud=solicitud)


def avisar_envio(solicitud, version, actor):
    revisores = get_user_model().objects.filter(is_active=True, groups__name='Revisor Institucional').values_list('pk', flat=True).distinct()
    asignacion = solicitud.asignacion
    mensaje = (f'Documento enviado: {solicitud.titulo}, versión {version.numero}. '
        f'Asignación {asignacion.pk}, unidad {asignacion.unidad_responsable.nombre}, período {asignacion.periodo.nombre}.')
    _avisar(asignacion, actor, revisores, 'Documento enviado a revisión', mensaje, solicitud=solicitud, version=version, revision=True)


def avisar_revision(solicitud, version, actor, decision, comentario):
    asignacion = solicitud.asignacion
    etiqueta = 'aprobada' if decision == 'aprobada' else 'con cambios solicitados'
    mensaje = (f'{solicitud.titulo}, versión {version.numero}: {etiqueta}. {comentario} '
        f'Asignación {asignacion.pk}, período {asignacion.periodo.nombre}.')
    _avisar(asignacion, actor, [asignacion.encargado_id, version.subido_por_id], 'Documento revisado', mensaje, solicitud=solicitud, version=version)


def avisar_cierre(asignacion, actor, *, comentario=''):
    _avisar(asignacion, actor, [asignacion.encargado_id], 'Asignación aprobada globalmente',
        f'La asignación {asignacion.pk}: {asignacion.indicador_nombre}, período {asignacion.periodo.nombre}, fue aprobada globalmente. {comentario}')
