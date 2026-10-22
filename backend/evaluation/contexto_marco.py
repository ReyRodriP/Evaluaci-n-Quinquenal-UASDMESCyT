"""Opciones de alta del marco reutilizando las validaciones de asignación existentes."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.permissions import ROLES_SIN_RESTRICCION, _grupos_usuario
from catalogo.models import IndicadorMarco
from organization.models import UnidadOrganizacional

from .models import Asignacion, Periodo
from .services import finalizar_periodos_vencidos, validar_encargado, validar_referencia_marco


def opciones_alta_marco(request):
    usuario = request.user
    if not (usuario.is_superuser or _grupos_usuario(usuario) & ROLES_SIN_RESTRICCION):
        raise PermissionDenied('La preparación de asignaciones del marco corresponde a Administración y Coordinación.')
    if not usuario.has_perms(['evaluation.view_asignacion', 'evaluation.add_asignacion']):
        raise PermissionDenied()
    periodo_id = request.query_params.get('periodo')
    unidad_id = request.query_params.get('unidad')
    for nombre, valor in (('periodo', periodo_id), ('unidad', unidad_id)):
        if (nombre == 'periodo' or valor is not None) and (not str(valor).isdigit() or int(valor) < 1):
            raise ValidationError({nombre: 'Debe ser un identificador entero positivo.'})
    finalizar_periodos_vencidos()
    periodo = get_object_or_404(Periodo.objects.select_related('version_marco'), pk=periodo_id)
    if not periodo.activo:
        raise ValidationError({'periodo': 'El período finalizó; solo permite consulta.'})
    if not periodo.version_marco_id:
        raise ValidationError({'version_marco': 'Seleccione explícitamente la versión del marco en Períodos antes de asignar indicadores.'})

    unidades_todas = list(UnidadOrganizacional.objects.select_related('tipo').order_by('nombre', 'pk'))
    por_id = {unidad.pk: unidad for unidad in unidades_todas}

    def ruta_unidad(unidad):
        nombres, vistos = [], set()
        while unidad is not None and unidad.pk not in vistos:
            vistos.add(unidad.pk)
            nombres.append(unidad.nombre)
            unidad = por_id.get(unidad.unidad_padre_id)
        return ' / '.join(reversed(nombres))

    unidad = get_object_or_404(UnidadOrganizacional, pk=unidad_id, activa=True) if unidad_id else None
    encargados = []
    if unidad:
        candidatos = get_user_model().objects.filter(is_active=True, perfilusuario__unidad_organizacional=unidad).distinct().order_by('username', 'pk')
        for candidato in candidatos:
            try:
                validar_encargado(candidato, unidad)
            except ModelValidationError:
                continue
            encargados.append({'id': candidato.pk, 'username': candidato.username, 'nombre': candidato.get_full_name() or candidato.username})

    indicadores = []
    queryset = IndicadorMarco.objects.filter(version_marco_id=periodo.version_marco_id, activo=True).select_related(
        'version_marco', 'estandar__criterio_marco__componente__dimension',
    ).order_by('estandar__criterio_marco__componente__dimension__orden', 'estandar__codigo_completo', 'orden', 'pk')
    for indicador in queryset:
        try:
            validar_referencia_marco(indicador, periodo)
        except ModelValidationError:
            continue
        indicadores.append({'id': indicador.pk, 'ruta': Asignacion(indicador_marco=indicador).ruta_marco})

    return {
        'periodo': {'id': periodo.pk, 'nombre': periodo.nombre},
        'version': {'id': periodo.version_marco_id, 'nombre': periodo.version_marco.nombre, 'activo': periodo.version_marco.activo},
        'unidades': [{'id': u.pk, 'nombre': u.nombre, 'ruta': ruta_unidad(u), 'tipo': u.tipo.nombre} for u in unidades_todas if u.activa],
        'indicadores': indicadores, 'encargados': encargados,
        'asignaciones_existentes': list(Asignacion.objects.filter(periodo=periodo, unidad_responsable=unidad,
            indicador_marco__isnull=False).values('id', 'indicador_marco')) if unidad else [],
    }
