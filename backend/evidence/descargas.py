"""ZIP de últimas versiones de evidencias y documentos con selección y alcance explícitos."""

import csv
import re
import shutil
import tempfile
import unicodedata
import zipfile
from collections.abc import Mapping
from io import StringIO
from pathlib import PurePosixPath

from django.http import FileResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from auditoria.utils import registrar_auditoria
from evaluation.filtros import filtrar_por_marco
from evaluation.services import relaciones_indicador

from .documentos import asignaciones_visibles
from .models import SolicitudDocumental


class _LimiteDescargaExcedido(Exception):
    pass


def _nombre_seguro(valor):
    ascii_valor = unicodedata.normalize('NFKD', str(valor)).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^A-Za-z0-9._-]+', '_', ascii_valor).strip('._') or 'sin_nombre'


def _ids(valor):
    if not isinstance(valor, list) or any(isinstance(v, bool) or not isinstance(v, (int, str)) or not str(v).isdigit() for v in valor):
        raise ValidationError({'detail': 'La selección contiene identificadores inválidos.'})
    try:
        valores = [int(v) for v in valor]
    except ValueError as exc:
        raise ValidationError({'detail': 'La selección contiene identificadores inválidos.'}) from exc
    if any(v < 1 or v > 9223372036854775807 for v in valores):
        raise ValidationError({'detail': 'La selección contiene identificadores inválidos.'})
    return list(dict.fromkeys(valores))


def _verificar_limite(tamano, limite):
    if tamano > limite:
        raise _LimiteDescargaExcedido


def _celda_csv(valor):
    return f"'{valor}" if isinstance(valor, str) and valor.lstrip().startswith(('=', '+', '-', '@')) else valor


def descargar_lote(request, obtener_evidencias, limite_elementos, limite_bytes, spool_memoria):
    if not isinstance(request.data, Mapping):
        raise ValidationError({'detail': 'La selección debe indicar listas de evidencias y documentos.'})
    evidencias_ids = _ids(request.data.get('evidencias', []))
    solicitudes_ids = _ids(request.data.get('solicitudes', []))
    if not evidencias_ids and not solicitudes_ids:
        raise ValidationError({'detail': 'Seleccione al menos una evidencia o documento.'})
    if len(evidencias_ids) + len(solicitudes_ids) > limite_elementos:
        return Response({'detail': f'El límite por descarga es {limite_elementos} evidencias y documentos en conjunto.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    periodo = request.query_params.get('periodo')
    if periodo is not None and (not periodo.isdigit() or int(periodo) < 1):
        raise ValidationError({'periodo': 'Debe ser un identificador entero positivo.'})
    if solicitudes_ids and not request.user.has_perms(['evaluation.view_asignacion', 'evidence.view_evidencia']):
        raise PermissionDenied()

    evidencias = list(obtener_evidencias().filter(pk__in=evidencias_ids).select_related(
        'asignacion__periodo', 'asignacion__unidad_responsable', *relaciones_indicador('asignacion__'),
    ))
    solicitudes_qs = SolicitudDocumental.objects.filter(asignacion__in=asignaciones_visibles(request), pk__in=solicitudes_ids)
    if periodo:
        solicitudes_qs = solicitudes_qs.filter(asignacion__periodo_id=periodo)
    solicitudes_qs = filtrar_por_marco(solicitudes_qs, request.query_params, 'asignacion__')
    solicitudes = list(solicitudes_qs.select_related('asignacion__periodo', 'asignacion__unidad_responsable', *relaciones_indicador('asignacion__')))
    if len(evidencias) != len(evidencias_ids) or len(solicitudes) != len(solicitudes_ids):
        return Response({'detail': 'Una o más evidencias o documentos no existen o no están autorizados.'}, status=status.HTTP_404_NOT_FOUND)
    por_id = {e.pk: e for e in evidencias}
    solicitudes_por_id = {s.pk: s for s in solicitudes}
    elementos = [('evidencia', por_id[pk]) for pk in evidencias_ids] + [('documento', solicitudes_por_id[pk]) for pk in solicitudes_ids]
    versiones, estimado = {}, 0
    for tipo, elemento in elementos:
        version = elemento.versiones.order_by('-numero', '-pk').first() if tipo == 'documento' else elemento.versiones.order_by('-version', '-pk').first()
        versiones[(tipo, elemento.pk)] = version
        if version is not None and version.archivo:
            try:
                estimado += version.archivo.size
            except (OSError, ValueError):
                continue
            if estimado > limite_bytes:
                return Response({'detail': 'La selección supera el límite de 250 MB sin comprimir.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    incluye_documentos = bool(solicitudes_ids)
    columnas = ['evidencia_id', 'asignacion_id', 'periodo', 'unidad', 'criterio', 'indicador', 'version', 'archivo', 'bytes', 'resultado']
    columnas_error = ['evidencia_id', 'archivo', 'error']
    if incluye_documentos:
        columnas += ['tipo_recurso', 'solicitud_id', 'titulo_documento', 'version_id']
        columnas_error += ['tipo_recurso', 'solicitud_id']
    manifest, errores = StringIO(newline=''), StringIO(newline='')
    manifest_writer, errores_writer = csv.writer(manifest), csv.writer(errores)
    manifest_writer.writerow(columnas)
    errores_writer.writerow(columnas_error)
    errores_count, archivos_incluidos, bytes_incluidos = 0, 0, 0
    zip_buffer = tempfile.SpooledTemporaryFile(max_size=spool_memoria, mode='w+b')  # noqa: SIM115 - FileResponse asume el cierre al terminar la descarga.

    def registrar_manifest(tipo, elemento, version, archivo, tamano, resultado):
        asignacion = elemento.asignacion
        numero = (version.numero if tipo == 'documento' else version.version) if version else ''
        fila = [elemento.pk if tipo == 'evidencia' else '', asignacion.pk, asignacion.periodo.nombre,
            asignacion.unidad_responsable.nombre, asignacion.criterio_nombre, asignacion.indicador_nombre,
            numero, archivo, tamano, resultado]
        if incluye_documentos:
            fila += [tipo, elemento.pk if tipo == 'documento' else '', elemento.titulo if tipo == 'documento' else '', version.pk if version else '']
        manifest_writer.writerow([_celda_csv(celda) for celda in fila])

    def registrar_error(tipo, elemento, archivo, mensaje):
        fila = [elemento.pk if tipo == 'evidencia' else '', archivo, mensaje]
        if incluye_documentos:
            fila += [tipo, elemento.pk if tipo == 'documento' else '']
        errores_writer.writerow([_celda_csv(celda) for celda in fila])

    try:
        with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
            for tipo, elemento in elementos:
                asignacion = elemento.asignacion
                version = versiones[(tipo, elemento.pk)]
                nombre_original = PurePosixPath(version.archivo.name).name if version and version.archivo else ''
                if version is None or not version.archivo:
                    registrar_error(tipo, elemento, nombre_original, 'La evidencia o documento no tiene una versión con archivo.')
                    registrar_manifest(tipo, elemento, version, '', 0, 'SIN_ARCHIVO')
                    errores_count += 1
                    continue
                indicador_archivo = asignacion.indicador_marco.codigo_completo if asignacion.indicador_marco_id else asignacion.indicador_nombre
                criterio_archivo = asignacion.indicador_marco.estandar.criterio_marco.codigo_completo if asignacion.indicador_marco_id else asignacion.criterio_nombre
                carpeta = '/'.join(_nombre_seguro(segmento) for segmento in (
                    asignacion.periodo.nombre, criterio_archivo, asignacion.unidad_responsable.nombre, indicador_archivo,
                ))
                if tipo == 'documento':
                    destino = f'{carpeta}/DOC-{elemento.pk}/DOC-{elemento.pk}_v{version.numero}_{_nombre_seguro(nombre_original)}'
                else:
                    destino = f'{carpeta}/EVID-{elemento.pk}_IND-{_nombre_seguro(indicador_archivo)}_v{version.version}_{_nombre_seguro(nombre_original)}'
                with tempfile.SpooledTemporaryFile(max_size=spool_memoria, mode='w+b') as staging:
                    tamano = 0
                    try:
                        with version.archivo.open('rb') as source:
                            while chunk := source.read(1024 * 1024):
                                tamano += len(chunk)
                                _verificar_limite(bytes_incluidos + tamano, limite_bytes)
                                staging.write(chunk)
                        staging.seek(0)
                        with zip_file.open(destino, mode='w') as target:
                            shutil.copyfileobj(staging, target, length=1024 * 1024)
                    except (OSError, ValueError):
                        registrar_error(tipo, elemento, nombre_original, 'No se pudo leer el archivo almacenado.')
                        registrar_manifest(tipo, elemento, version, nombre_original, tamano, 'ERROR_ARCHIVO')
                        errores_count += 1
                        continue
                archivos_incluidos += 1
                bytes_incluidos += tamano
                registrar_manifest(tipo, elemento, version, destino, tamano, 'INCLUIDO')
            zip_file.writestr('manifest.csv', manifest.getvalue().encode('utf-8-sig'))
            if errores_count:
                zip_file.writestr('errors.csv', errores.getvalue().encode('utf-8-sig'))
        zip_buffer.seek(0)
        periodos = sorted({elemento.asignacion.periodo.nombre for _, elemento in elementos})
        registrar_auditoria(request.user, 'Descarga masiva', 'Evidencia', descripcion=(
            f'Se solicitó un ZIP de {len(evidencias_ids)} evidencias y {len(solicitudes_ids)} documentos; '
            f'archivos incluidos: {archivos_incluidos}; tamaño sin comprimir: {bytes_incluidos} bytes; '
            f'períodos: {", ".join(periodos)}; IDs: {",".join(map(str, evidencias_ids))}; solicitudes: {",".join(map(str, solicitudes_ids))}.'
        ))
        nombre_periodo = _nombre_seguro(periodos[0]) if len(periodos) == 1 else 'varios_periodos'
        filename = f'Evidencias_{nombre_periodo}_{timezone.localdate().isoformat()}.zip'
        return FileResponse(zip_buffer, as_attachment=True, filename=filename, content_type='application/zip')
    except _LimiteDescargaExcedido:
        zip_buffer.close()
        return Response({'detail': 'La selección supera el límite de 250 MB sin comprimir.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    except Exception:
        zip_buffer.close()
        raise
