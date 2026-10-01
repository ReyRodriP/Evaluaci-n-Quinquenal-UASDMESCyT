"""@file views.py
@brief Vistas API para la gestión de evidencias, versiones y observaciones
@details Implementa los ViewSets de Django REST Framework para el CRUD
completo de evidencias, subida de versiones, observaciones y descarga
de archivos, con control de permisos y auditoría integrada."""

import csv
import os
import re
import shutil
import tempfile
import unicodedata
import zipfile
from io import StringIO
from pathlib import PurePosixPath

from django.db.models import Max, OuterRef, Subquery
from django.http import FileResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import (
    CustomModelPermissions,
    PuedeDescargarEvidencias,
    es_evaluador_externo,
    filtrar_por_rol,
)
from auditoria.utils import registrar_auditoria
from evaluation.models import Asignacion, EstadoAsignacion, HistorialEstado
from evaluation.services import finalizar_periodos_vencidos
from notificaciones.utils import crear_notificacion

from .models import Evidencia, Observacion, VersionEvidencia
from .serializers import EditarVersionSerializer, EvidenciaSerializer, ObservacionSerializer, VersionEvidenciaSerializer

MAX_DESCARGA_EVIDENCIAS = 100
MAX_TAMANO_DESCARGA = 250 * 1024 * 1024
ZIP_SPOOL_MEMORIA = 8 * 1024 * 1024


class _DescargaMasivaExcedida(Exception):
    pass


def _nombre_zip_seguro(valor):
    ascii_valor = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode("ascii")
    seguro = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_valor).strip("._")
    return seguro or "sin_nombre"


# CRUD de Evidencias
class EvidenciaViewSet(viewsets.ModelViewSet):
    """@class EvidenciaViewSet
    @brief ViewSet para el CRUD completo de evidencias
    @details Proporciona operaciones de crear, listar, actualizar y eliminar evidencias,
    así como acciones personalizadas para subir versiones, obtener detalles
    con información de asignación, historial de versiones y edición de versiones."""

    permission_classes = [IsAuthenticated, CustomModelPermissions]
    queryset = Evidencia.objects.all()
    serializer_class = EvidenciaSerializer

    def get_queryset(self):
        """@brief Filtra el queryset según el rol del usuario autenticado
        @return QuerySet filtrado por departamento de la asignación"""

        finalizar_periodos_vencidos()
        qs = Evidencia.objects.all()
        periodo_id = self.request.query_params.get("periodo")
        if periodo_id:
            qs = qs.filter(asignacion__periodo_id=periodo_id)
        elif self.request.method in ("GET", "HEAD", "OPTIONS") and not es_evaluador_externo(self.request):
            qs = qs.filter(asignacion__periodo__activo=True)
        return filtrar_por_rol(qs, self.request, dept_field="asignacion__unidad_responsable")

    @action(
        detail=False,
        methods=["post"],
        url_path="descargas-masivas",
        permission_classes=[IsAuthenticated, PuedeDescargarEvidencias],
    )
    def descargas_masivas(self, request):
        raw_ids = request.data.get("evidencias")
        if not isinstance(raw_ids, list) or not raw_ids:
            return Response({"detail": "Seleccione al menos una evidencia."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            evidencia_ids = list(dict.fromkeys(int(value) for value in raw_ids))
        except (TypeError, ValueError):
            return Response({"detail": "La selección contiene identificadores inválidos."}, status=status.HTTP_400_BAD_REQUEST)

        if len(evidencia_ids) > MAX_DESCARGA_EVIDENCIAS:
            return Response(
                {"detail": f"El límite por descarga es {MAX_DESCARGA_EVIDENCIAS} evidencias."},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        evidencias = list(
            self.get_queryset()
            .filter(pk__in=evidencia_ids)
            .select_related(
                "asignacion__periodo",
                "asignacion__unidad_responsable",
                "asignacion__indicador__criterio",
            )
            .prefetch_related("versiones")
        )
        if len(evidencias) != len(evidencia_ids):
            return Response(
                {"detail": "Una o más evidencias no existen o no están autorizadas."},
                status=status.HTTP_404_NOT_FOUND,
            )

        evidencias_por_id = {evidencia.pk: evidencia for evidencia in evidencias}
        evidencias = [evidencias_por_id[evidencia_id] for evidencia_id in evidencia_ids]
        versiones = {}
        tamano_estimado = 0
        for evidencia in evidencias:
            version = evidencia.versiones.order_by("-version", "-pk").first()
            versiones[evidencia.pk] = version
            if version is None or not version.archivo:
                continue
            try:
                tamano_estimado += version.archivo.size
            except (OSError, ValueError):
                continue
            if tamano_estimado > MAX_TAMANO_DESCARGA:
                return Response(
                    {"detail": "La selección supera el límite de 250 MB sin comprimir."},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )

        zip_buffer = tempfile.SpooledTemporaryFile(max_size=ZIP_SPOOL_MEMORIA, mode="w+b")
        manifest = StringIO(newline="")
        manifest_writer = csv.writer(manifest)
        manifest_writer.writerow(
            ["evidencia_id", "asignacion_id", "periodo", "unidad", "criterio", "indicador", "version", "archivo", "bytes", "resultado"]
        )
        errores = StringIO(newline="")
        errores_writer = csv.writer(errores)
        errores_writer.writerow(["evidencia_id", "archivo", "error"])
        errores_count = 0
        archivos_incluidos = 0
        bytes_incluidos = 0

        try:
            with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                for evidencia in evidencias:
                    asignacion = evidencia.asignacion
                    indicador = asignacion.indicador
                    version = versiones[evidencia.pk]
                    nombre_original = PurePosixPath(version.archivo.name).name if version and version.archivo else ""
                    if version is None or not version.archivo:
                        mensaje = "La evidencia no tiene una versión con archivo."
                        errores_writer.writerow([evidencia.pk, nombre_original, mensaje])
                        errores_count += 1
                        manifest_writer.writerow(
                            [evidencia.pk, asignacion.pk, asignacion.periodo.nombre, asignacion.unidad_responsable.nombre,
                             indicador.criterio.nombre, indicador.nombre, "", "", 0, "SIN_ARCHIVO"]
                        )
                        continue

                    carpeta = "/".join(
                        _nombre_zip_seguro(segmento)
                        for segmento in (
                            asignacion.periodo.nombre,
                            indicador.criterio.nombre,
                            asignacion.unidad_responsable.nombre,
                            indicador.nombre,
                        )
                    )
                    nombre_archivo = _nombre_zip_seguro(nombre_original)
                    destino = (
                        f"{carpeta}/EVID-{evidencia.pk}_IND-{_nombre_zip_seguro(indicador.nombre)}_"
                        f"v{version.version}_{nombre_archivo}"
                    )

                    staging = tempfile.SpooledTemporaryFile(max_size=ZIP_SPOOL_MEMORIA, mode="w+b")
                    tamano_archivo = 0
                    try:
                        with version.archivo.open("rb") as source:
                            while chunk := source.read(1024 * 1024):
                                tamano_archivo += len(chunk)
                                if bytes_incluidos + tamano_archivo > MAX_TAMANO_DESCARGA:
                                    raise _DescargaMasivaExcedida
                                staging.write(chunk)
                        staging.seek(0)
                        with zip_file.open(destino, mode="w") as target:
                            shutil.copyfileobj(staging, target, length=1024 * 1024)
                    except (OSError, ValueError) as exc:
                        mensaje = "No se pudo leer el archivo almacenado."
                        errores_writer.writerow([evidencia.pk, nombre_original, mensaje])
                        errores_count += 1
                        manifest_writer.writerow(
                            [evidencia.pk, asignacion.pk, asignacion.periodo.nombre, asignacion.unidad_responsable.nombre,
                             indicador.criterio.nombre, indicador.nombre, version.version, nombre_original,
                             tamano_archivo, "ERROR_ARCHIVO"]
                        )
                        continue
                    finally:
                        staging.close()

                    archivos_incluidos += 1
                    bytes_incluidos += tamano_archivo
                    manifest_writer.writerow(
                        [evidencia.pk, asignacion.pk, asignacion.periodo.nombre, asignacion.unidad_responsable.nombre,
                         indicador.criterio.nombre, indicador.nombre, version.version, destino, tamano_archivo, "INCLUIDO"]
                    )

                zip_file.writestr("manifest.csv", manifest.getvalue().encode("utf-8-sig"))
                if errores_count:
                    zip_file.writestr("errors.csv", errores.getvalue().encode("utf-8-sig"))

            zip_buffer.seek(0)
            periodos = sorted({evidencia.asignacion.periodo.nombre for evidencia in evidencias})
            periodos_texto = ", ".join(periodos)
            registrar_auditoria(
                usuario=request.user,
                accion="Descarga masiva",
                modelo="Evidencia",
                descripcion=(
                    f"Se solicitó un ZIP de {len(evidencias)} evidencias; archivos incluidos: {archivos_incluidos}; "
                    f"tamaño sin comprimir: {bytes_incluidos} bytes; períodos: {periodos_texto}; "
                    f"IDs: {','.join(str(pk) for pk in evidencia_ids)}."
                ),
            )
            nombre_periodo = _nombre_zip_seguro(periodos[0]) if len(periodos) == 1 else "varios_periodos"
            filename = f"Evidencias_{nombre_periodo}_{timezone.localdate().isoformat()}.zip"
            return FileResponse(zip_buffer, as_attachment=True, filename=filename, content_type="application/zip")
        except _DescargaMasivaExcedida:
            zip_buffer.close()
            return Response(
                {"detail": "La selección supera el límite de 250 MB sin comprimir."},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        except Exception:
            zip_buffer.close()
            raise

    def get_object(self):
        evidencia = super().get_object()
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            finalizar_periodos_vencidos()
            evidencia.asignacion.periodo.refresh_from_db(fields=["activo"])
            if not evidencia.asignacion.periodo.activo:
                raise ValidationError({"periodo": "El período finalizó; la evidencia solo permite consulta."})
        return evidencia

    def create(self, request, *args, **kwargs):
        """@brief Crea una nueva evidencia o reactiva una existente
        @details Si ya existe una evidencia para la asignación indicada y está
        cancelada, la reactiva y retorna la existente. De lo contrario crea una nueva.
        @param request Solicitud HTTP con los datos de la evidencia
        @return Response con los datos de la evidencia creada o reactivada"""

        asignacion_id = request.data.get("asignacion")
        if asignacion_id:
            finalizar_periodos_vencidos()
            asignacion = Asignacion.objects.filter(pk=asignacion_id).select_related("periodo").first()
            if asignacion is not None and not asignacion.periodo.activo:
                return Response(
                    {"asignacion": "Solo se pueden gestionar evidencias del período activo."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            existing = Evidencia.objects.filter(asignacion_id=asignacion_id).first()
            if existing:
                if existing.estado == "cancelada":
                    existing.estado = "activa"
                    existing.save()
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def subir_version(self, request, pk=None):
        """@brief Sube una nueva versión de archivo para una evidencia
        @details Valida que la evidencia no esté aprobada, crea una nueva versión
        incremental con el archivo adjunto y actualiza el estado de la asignación
        a EN_PROGRESO si estaba en PENDIENTE, OBSERVADA o RECHAZADO.
        @param request Solicitud HTTP con el archivo y comentario opcional
        @param pk Identificador de la evidencia
        @return Response con los datos de la versión creada
        @raises Response Error 400 si la evidencia está aprobada o no se adjunta archivo"""

        evidencia = self.get_object()

        if evidencia.asignacion.estado == EstadoAsignacion.APROBADO:
            return Response(
                {"error": "No se puede modificar una evidencia ya aprobada"}, status=status.HTTP_400_BAD_REQUEST
            )

        archivo = request.FILES.get("archivo")
        if not archivo:
            return Response({"error": "Debe adjuntar un archivo"}, status=status.HTTP_400_BAD_REQUEST)

        comentario = request.data.get("comentario", "")

        if evidencia.estado == "cancelada":
            evidencia.estado = "activa"
            evidencia.save()

        ultima_version = evidencia.versiones.aggregate(max_version=Max("version"))["max_version"] or 0
        nueva_version_num = ultima_version + 1

        version = VersionEvidencia.objects.create(
            evidencia=evidencia, archivo=archivo, version=nueva_version_num, comentario=comentario
        )

        asignacion = evidencia.asignacion
        if asignacion.estado in [EstadoAsignacion.PENDIENTE, EstadoAsignacion.OBSERVADA, EstadoAsignacion.RECHAZADO]:
            estado_anterior = asignacion.estado
            asignacion.estado = EstadoAsignacion.EN_PROGRESO
            asignacion.save()
            HistorialEstado.objects.create(
                asignacion=asignacion,
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoAsignacion.EN_PROGRESO,
                usuario=request.user,
                comentario=f"Nueva versión subida: {comentario or 'Sin comentario'}",
            )

        return Response(VersionEvidenciaSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def detalle(self, request, pk=None):
        """@brief Obtiene el detalle completo de una evidencia
        @details Incluye información de la asignación, historial de estados,
        permisos del usuario para observar, subir versiones, cambiar estado
        y editar información.
        @param request Solicitud HTTP del usuario autenticado
        @param pk Identificador de la evidencia
        @return Response con los datos detallados de la evidencia"""

        evidencia = self.get_object()
        try:
            asignacion = evidencia.asignacion
        except Exception:
            asignacion = None

        data = EvidenciaSerializer(evidencia, context={"request": request}).data
        if asignacion:
            from evaluation.serializers import AsignacionSerializer, HistorialEstadoSerializer

            asignacion.periodo.refresh_from_db(fields=["activo"])
            data["asignacion_info"] = AsignacionSerializer(asignacion).data
            if es_evaluador_externo(request):
                data["historial_estados"] = []
            else:
                historial = asignacion.historial_estados.all().order_by("-fecha")[:20]
                data["historial_estados"] = HistorialEstadoSerializer(historial, many=True).data

        periodo_activo = bool(asignacion and asignacion.periodo.activo)
        data["puede_observar"] = request.user.has_perm("evidence.add_observacion") and periodo_activo
        es_aprobado = asignacion and asignacion.estado == EstadoAsignacion.APROBADO
        puede_subir = request.user.has_perm("evidence.add_versionevidencia") or request.user.has_perm(
            "evidence.add_evidencia"
        )

        puede_cambiar = request.user.has_perm("evidence.change_evidencia")

        puede_modificar = not es_evaluador_externo(request)
        data["puede_observar"] = data["puede_observar"] and puede_modificar
        data["puede_subir_version"] = puede_modificar and puede_subir and not es_aprobado and periodo_activo
        data["puede_cambiar_estado"] = (
            puede_modificar
            and request.user.has_perm("evaluation.change_asignacion")
            and not es_aprobado
            and periodo_activo
        )
        data["puede_editar_info"] = puede_modificar and puede_cambiar and not es_aprobado and periodo_activo

        return Response(data)

    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        """@brief Obtiene el historial de versiones de una evidencia
        @details Retorna todas las versiones ordenadas de la más reciente a la más antigua.
        @param request Solicitud HTTP del usuario autenticado
        @param pk Identificador de la evidencia
        @return Response con la lista serializada de versiones"""

        evidencia = self.get_object()
        versiones = evidencia.versiones.order_by("-version", "-pk")
        if es_evaluador_externo(request):
            versiones = versiones[:1]

        return Response(VersionEvidenciaSerializer(versiones, many=True, context={"request": request}).data)

    @action(detail=True, methods=["patch"])
    def editar_version(self, request, pk=None):
        """@brief Edita la última versión de una evidencia
        @details Permite modificar el archivo y/o comentario de la versión más
        reciente. Registra la edición en el sistema de auditoría.
        @param request Solicitud HTTP con los campos a actualizar
        @param pk Identificador de la evidencia
        @return Response con los datos de la versión actualizada
        @raises Response Error 400 si la evidencia está aprobada o no hay versiones"""

        evidencia = self.get_object()

        if evidencia.asignacion.estado == EstadoAsignacion.APROBADO:
            return Response(
                {"error": "No se puede modificar una evidencia ya aprobada"}, status=status.HTTP_400_BAD_REQUEST
            )

        ultima = evidencia.versiones.order_by("-version").first()
        if not ultima:
            return Response({"error": "No hay versiones para editar"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = EditarVersionSerializer(ultima, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        version = serializer.save()

        registrar_auditoria(
            usuario=request.user,
            accion="Editar versión",
            modelo="VersionEvidencia",
            registro_id=version.pk,
            descripcion=(f"Se editó la versión {version.version} de la evidencia '{evidencia.titulo}'"),
        )

        return Response(VersionEvidenciaSerializer(version).data)


# CRUD de Versiones
class VersionEvidenciaViewSet(viewsets.ReadOnlyModelViewSet):
    """@class VersionEvidenciaViewSet
    @brief ViewSet de solo lectura para versiones de evidencia
    @details Permite listar, consultar detalles, descargar archivos,
    obtener previsualización y listar observaciones de cada versión."""

    permission_classes = [IsAuthenticated, CustomModelPermissions]
    queryset = VersionEvidencia.objects.all()
    serializer_class = VersionEvidenciaSerializer

    def get_queryset(self):
        """@brief Filtra el queryset según el rol del usuario autenticado
        @return QuerySet filtrado por departamento de la evidencia"""

        finalizar_periodos_vencidos()
        qs = VersionEvidencia.objects.all()
        periodo_id = self.request.query_params.get("periodo")
        if periodo_id:
            qs = qs.filter(evidencia__asignacion__periodo_id=periodo_id)
        elif self.request.method in ("GET", "HEAD", "OPTIONS") and not es_evaluador_externo(self.request):
            qs = qs.filter(evidencia__asignacion__periodo__activo=True)
        if es_evaluador_externo(self.request):
            ultima_version = VersionEvidencia.objects.filter(evidencia_id=OuterRef("evidencia_id")).order_by(
                "-version", "-pk"
            )
            qs = qs.filter(pk=Subquery(ultima_version.values("pk")[:1]))
        return filtrar_por_rol(qs, self.request, dept_field="evidencia__asignacion__unidad_responsable")

    @action(detail=True, methods=["get"])
    def descargar(self, request, pk=None):
        """@brief Descarga el archivo de una versión de evidencia
        @details Retorna el archivo como respuesta con attachment para descarga directa.
        @param request Solicitud HTTP del usuario autenticado
        @param pk Identificador de la versión
        @return FileResponse con el archivo adjunto"""

        version = self.get_object()

        return FileResponse(version.archivo.open(), as_attachment=True, filename=version.archivo.name.split("/")[-1])

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """@brief Previsualiza el archivo de una versión de evidencia
        @details Retorna el archivo con el content-type apropiado para visualización
        inline en el navegador. Soporta múltiples formatos de imagen, documentos
        y archivos de texto.
        @param request Solicitud HTTP del usuario autenticado
        @param pk Identificador de la versión
        @return FileResponse con el archivo para previsualización"""

        version = self.get_object()
        archivo = version.archivo

        content_type_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".xml": "application/xml",
            ".html": "text/html",
            ".htm": "text/html",
            ".md": "text/markdown",
            ".log": "text/plain",
            ".py": "text/plain",
            ".js": "text/plain",
            ".ts": "text/plain",
            ".java": "text/plain",
            ".c": "text/plain",
            ".cpp": "text/plain",
            ".css": "text/plain",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".bmp": "image/bmp",
        }

        ext = os.path.splitext(archivo.name)[1].lower()
        content_type = content_type_map.get(ext, "application/octet-stream")

        response = FileResponse(archivo.open("rb"), content_type=content_type)
        response["Content-Disposition"] = f'inline; filename="{os.path.basename(archivo.name)}"'
        return response

    @action(detail=True, methods=["get"])
    def observaciones(self, request, pk=None):
        """@brief Lista todas las observaciones de una versión de evidencia
        @param request Solicitud HTTP del usuario autenticado
        @param pk Identificador de la versión
        @return Response con la lista serializada de observaciones"""

        version = self.get_object()

        if es_evaluador_externo(request):
            return Response([])

        return Response(ObservacionSerializer(version.observaciones.all(), many=True).data)


# CRUD de Observaciones
class ObservacionViewSet(viewsets.ModelViewSet):
    """@class ObservacionViewSet
    @brief ViewSet para el CRUD completo de observaciones
    @details Permite crear, listar, actualizar y eliminar (soft delete) observaciones.
    Al crear una observación se registra en auditoría, se notifica al autor
    de la evidencia y se cambia el estado de la asignación a OBSERVADA."""

    queryset = Observacion.objects.filter(activo=True)
    serializer_class = ObservacionSerializer

    permission_classes = [IsAuthenticated, CustomModelPermissions]

    def get_queryset(self):
        """@brief Filtra el queryset de observaciones activas según el rol del usuario
        @return QuerySet filtrado por departamento de la evidencia asociada"""

        finalizar_periodos_vencidos()
        qs = Observacion.objects.filter(activo=True)
        periodo_id = self.request.query_params.get("periodo")
        if periodo_id:
            qs = qs.filter(version__evidencia__asignacion__periodo_id=periodo_id)
        elif self.request.method in ("GET", "HEAD", "OPTIONS"):
            qs = qs.filter(version__evidencia__asignacion__periodo__activo=True)
        return filtrar_por_rol(qs, self.request, dept_field="version__evidencia__asignacion__unidad_responsable")

    def get_object(self):
        observacion = super().get_object()
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            finalizar_periodos_vencidos()
            periodo = observacion.version.evidencia.asignacion.periodo
            periodo.refresh_from_db(fields=["activo"])
            if not periodo.activo:
                raise ValidationError({"periodo": "El período finalizó; la observación solo permite consulta."})
        return observacion

    def perform_create(self, serializer):
        """@brief Crea una observación y ejecuta acciones secundarias
        @details Asigna el usuario actual como autor, registra la acción en auditoría,
        envía notificación al propietario de la evidencia y cambia el estado
        de la asignación a OBSERVADA.
        @param serializer Serializer con los datos validados de la observación"""

        finalizar_periodos_vencidos()
        periodo = serializer.validated_data["version"].evidencia.asignacion.periodo
        periodo.refresh_from_db(fields=["activo"])
        if not periodo.activo:
            raise ValidationError({"version": "Solo se pueden gestionar evidencias del período activo."})
        observacion = serializer.save(usuario=self.request.user)

        evidencia = observacion.version.evidencia
        asignacion = evidencia.asignacion

        registrar_auditoria(
            usuario=self.request.user,
            accion="Crear observación",
            modelo="Observacion",
            registro_id=observacion.pk,
            descripcion=(
                f"Se creó una observación sobre la evidencia '{evidencia.titulo}' "
                f"(versión {observacion.version.version}): {observacion.comentario}"
            ),
        )

        if hasattr(evidencia, "subido_por") and evidencia.subido_por:
            crear_notificacion(
                usuario=evidencia.subido_por,
                titulo="Evidencia observada",
                mensaje=(f"Tu evidencia '{evidencia.titulo}' ha recibido una observación: {observacion.comentario}"),
            )

        estado_anterior = asignacion.estado
        asignacion.estado = EstadoAsignacion.OBSERVADA
        asignacion.save()

        HistorialEstado.objects.create(
            asignacion=asignacion,
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoAsignacion.OBSERVADA,
            usuario=self.request.user,
            comentario=f"Observación creada: {observacion.comentario}",
        )

    def perform_destroy(self, instance):
        """@brief Realiza un soft delete de una observación
        @details Marca la observación como inactiva en lugar de eliminarla físicamente.
        @param instance Instancia de la observación a desactivar"""

        instance.activo = False
        instance.save()
