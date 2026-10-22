"""Resultados operativos del marco por dimensión/estándar y período autorizado."""

import csv
import io
from xml.sax.saxutils import escape

from django.db.models import Count, Exists, OuterRef, Q
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import PuedeVerReportes, filtrar_por_rol
from evaluation.filtros import filtrar_por_marco
from evaluation.models import Asignacion
from evaluation.services import relaciones_indicador
from evidence.models import VersionDocumento, VersionEvidencia
from evidencias.models import Evidencia as EvidenciaHeredada

from .views import _build_pdf, _paginar, _periodo_para_reporte

CONTADORES = (
    'asignaciones', 'con_archivos', 'aprobadas_globalmente', 'pendientes_cierre',
    'documentos_solicitados', 'documentos_entregados', 'documentos_aprobados',
    'documentos_en_revision', 'documentos_observados',
)


def _resumen():
    return dict.fromkeys(CONTADORES, 0)


def _porcentaje(resumen):
    total = resumen['asignaciones']
    return round(resumen['aprobadas_globalmente'] * 100 / total, 1) if total else 0


def _datos(request):
    agrupar = request.query_params.get('agrupar', 'dimension')
    if agrupar not in ('dimension', 'estandar'):
        raise ValidationError({'agrupar': 'Seleccione dimension o estandar.'})
    for nombre in ('periodo', 'unidad'):
        valor = request.query_params.get(nombre)
        if valor and (not str(valor).isdigit() or int(valor) < 1):
            raise ValidationError({nombre: 'Debe ser un identificador entero positivo.'})
    periodo = _periodo_para_reporte(request)
    base = filtrar_por_rol(Asignacion.objects.filter(indicador_marco__isnull=False), request,
        dept_field='unidad_responsable')
    base = base.filter(periodo=periodo) if periodo else base.none()
    unidad = request.query_params.get('unidad')
    if unidad:
        base = base.filter(unidad_responsable_id=unidad)

    # Opciones derivadas exclusivamente de asignaciones autorizadas, antes de filtrar el marco.
    dimensiones, estandares = {}, {}
    for asignacion in base.select_related(*relaciones_indicador()).order_by('pk'):
        estandar = asignacion.indicador_marco.estandar
        dimension = estandar.criterio_marco.componente.dimension
        dimensiones[dimension.pk] = {'id': dimension.pk, 'codigo': dimension.codigo, 'nombre': dimension.nombre, 'orden': dimension.orden}
        estandares[estandar.pk] = {'id': estandar.pk, 'codigo': estandar.codigo_completo,
            'nombre': estandar.redaccion, 'dimension_id': dimension.pk}

    qs = filtrar_por_marco(base, request.query_params).select_related(*relaciones_indicador()).annotate(
        _con_archivos=Exists(VersionDocumento.objects.filter(solicitud__asignacion_id=OuterRef('pk')).exclude(archivo=''))
            | Exists(VersionEvidencia.objects.filter(evidencia__asignacion_id=OuterRef('pk')).exclude(archivo=''))
            | Exists(EvidenciaHeredada.objects.filter(asignacion_id=OuterRef('pk')).exclude(archivo='')),
        _solicitados=Count('solicitudes_documentales', distinct=True),
        _entregados=Count('solicitudes_documentales', filter=Q(solicitudes_documentales__versiones__isnull=False), distinct=True),
        _aprobados=Count('solicitudes_documentales', filter=Q(solicitudes_documentales__estado='aprobada'), distinct=True),
        _en_revision=Count('solicitudes_documentales', filter=Q(solicitudes_documentales__estado='en_revision'), distinct=True),
        _observados=Count('solicitudes_documentales', filter=Q(solicitudes_documentales__estado='observada'), distinct=True),
    ).order_by('indicador_marco__estandar__criterio_marco__componente__dimension__orden',
        'indicador_marco__estandar__codigo_completo', 'pk')
    grupos = {}
    totales = _resumen()
    for asignacion in qs:
        indicador = asignacion.indicador_marco
        estandar = indicador.estandar
        dimension = estandar.criterio_marco.componente.dimension
        clave = (indicador.version_marco_id, dimension.pk, estandar.pk if agrupar == 'estandar' else None)
        if clave not in grupos:
            grupos[clave] = {
                'version': {'id': indicador.version_marco_id, 'nombre': indicador.version_marco.nombre},
                'dimension': dimensiones[dimension.pk],
                'estandar': estandares[estandar.pk] if agrupar == 'estandar' else None,
                **_resumen(),
            }
        fila = grupos[clave]
        valores = {
            'asignaciones': 1, 'con_archivos': int(asignacion._con_archivos),
            'aprobadas_globalmente': int(asignacion.estado == 'aprobado'),
            'pendientes_cierre': int(asignacion.gestion_documental and asignacion._solicitados > 0
                and asignacion._solicitados == asignacion._aprobados and asignacion.estado not in ('aprobado', 'completado')),
            'documentos_solicitados': asignacion._solicitados, 'documentos_entregados': asignacion._entregados,
            'documentos_aprobados': asignacion._aprobados, 'documentos_en_revision': asignacion._en_revision,
            'documentos_observados': asignacion._observados,
        }
        for campo, valor in valores.items():
            fila[campo] += valor
            totales[campo] += valor
    filas = list(grupos.values())
    for fila in [*filas, totales]:
        fila['aprobacion_global_porcentaje'] = _porcentaje(fila)
    return {
        'periodo': {'id': periodo.pk, 'nombre': periodo.nombre} if periodo else None,
        'version_periodo': {'id': periodo.version_marco_id, 'nombre': periodo.version_marco.nombre}
            if periodo and periodo.version_marco_id else None,
        'agrupar': agrupar, 'resumen': totales, 'rows': filas,
        'opciones': {'dimensiones': sorted(dimensiones.values(), key=lambda d: (d['orden'], d['id'])),
            'estandares': sorted(estandares.values(), key=lambda e: e['codigo'])},
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated, PuedeVerReportes])
def marco(request):
    datos = _datos(request)
    filas, total, page, page_size, total_pages = _paginar(request, datos['rows'])
    return Response({**datos, 'rows': filas, 'total': total, 'page': page, 'page_size': page_size, 'total_pages': total_pages})


@api_view(['GET'])
@permission_classes([IsAuthenticated, PuedeVerReportes])
def marco_exportar(request):
    formato = request.query_params.get('formato', 'xlsx').lower()
    if formato not in ('csv', 'xlsx', 'pdf'):
        raise ValidationError({'formato': 'Seleccione csv, xlsx o pdf.'})
    datos = _datos(request)
    columnas = ['Período', 'Versión del marco', 'Dimensión', 'Estándar', 'Asignaciones', 'Con archivos',
        'Aprobadas globalmente', 'Pendientes de cierre', 'Docs. solicitados', 'Docs. entregados',
        'Docs. aprobados', 'Docs. en revisión', 'Docs. observados', 'Aprobación global (%)']
    filas = [[datos['periodo']['nombre'], fila['version']['nombre'], fila['dimension']['codigo'],
        fila['estandar']['codigo'] if fila['estandar'] else '', *[fila[c] for c in CONTADORES],
        fila['aprobacion_global_porcentaje']] for fila in datos['rows']]
    # CONTADORES y columnas describen las mismas nueve métricas y su porcentaje.
    if formato == 'csv':
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer)
        writer.writerow(columnas)
        for fila in filas:
            writer.writerow([f"'{v}" if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v for v in fila])
        contenido, tipo = '\ufeff' + buffer.getvalue(), 'text/csv; charset=utf-8'
    elif formato == 'xlsx':
        libro = Workbook()
        hoja = libro.active
        hoja.title = 'Resultados del marco'
        hoja.append(columnas)
        for celda in hoja[1]:
            celda.font = Font(bold=True, color='FFFFFF')
            celda.fill = PatternFill('solid', fgColor='1F4E79')
        for fila in filas:
            hoja.append(fila)
            for celda in hoja[hoja.max_row]:
                if isinstance(celda.value, str):
                    celda.data_type = 's'
                celda.alignment = Alignment(wrap_text=True, vertical='top')
        for columna in hoja.columns:
            hoja.column_dimensions[columna[0].column_letter].width = 24
        hoja.freeze_panes = 'A2'
        buffer = io.BytesIO()
        libro.save(buffer)
        contenido, tipo = buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        # El período y la versión van en el título para mantener legibles las columnas numéricas.
        periodo = datos['periodo']['nombre'] if datos['periodo'] else 'Sin período activo'
        titulo = escape(f'Resultados operativos del marco — {periodo}')
        pdf_filas = [[escape(str(valor)) for valor in fila[2:]] for fila in filas]
        contenido, tipo = _build_pdf(titulo, columnas[2:], pdf_filas), 'application/pdf'
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta['Content-Disposition'] = f'attachment; filename="resultados_marco_{datos["periodo"]["id"] if datos["periodo"] else "sin_periodo"}_{datos["agrupar"]}.{formato}"'
    return respuesta
