"""@file views.py
@brief Vistas API para la gestión de evidencias, versiones y observaciones
@details Implementa los ViewSets de Django REST Framework para el CRUD
completo de evidencias, subida de versiones, observaciones y descarga
de archivos, con control de permisos y auditoría integrada."""

import os

from django.db.models import Max
from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import CustomModelPermissions, filtrar_por_rol
from auditoria.utils import registrar_auditoria
from evaluation.models import EstadoAsignacion, HistorialEstado
from notificaciones.utils import crear_notificacion

from .models import Evidencia, Observacion, VersionEvidencia
from .serializers import EditarVersionSerializer, EvidenciaSerializer, ObservacionSerializer, VersionEvidenciaSerializer


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

        qs = Evidencia.objects.all()
        return filtrar_por_rol(qs, self.request, dept_field="asignacion__departamento")

    def create(self, request, *args, **kwargs):
        """@brief Crea una nueva evidencia o reactiva una existente
        @details Si ya existe una evidencia para la asignación indicada y está
        cancelada, la reactiva y retorna la existente. De lo contrario crea una nueva.
        @param request Solicitud HTTP con los datos de la evidencia
        @return Response con los datos de la evidencia creada o reactivada"""

        asignacion_id = request.data.get("asignacion")
        if asignacion_id:
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

            data["asignacion_info"] = AsignacionSerializer(asignacion).data
            historial = asignacion.historial_estados.all().order_by("-fecha")[:20]
            data["historial_estados"] = HistorialEstadoSerializer(historial, many=True).data

        data["puede_observar"] = request.user.has_perm("evidence.add_observacion")
        es_aprobado = asignacion and asignacion.estado == EstadoAsignacion.APROBADO
        puede_subir = request.user.has_perm("evidence.add_versionevidencia") or request.user.has_perm(
            "evidence.add_evidencia"
        )

        puede_cambiar = request.user.has_perm("evidence.change_evidencia")

        data["puede_subir_version"] = puede_subir and not es_aprobado
        data["puede_cambiar_estado"] = request.user.has_perm("evaluation.change_asignacion") and not es_aprobado
        data["puede_editar_info"] = puede_cambiar and not es_aprobado

        return Response(data)

    @action(detail=True, methods=["get"])
    def historial(self, request, pk=None):
        """@brief Obtiene el historial de versiones de una evidencia
        @details Retorna todas las versiones ordenadas de la más reciente a la más antigua.
        @param request Solicitud HTTP del usuario autenticado
        @param pk Identificador de la evidencia
        @return Response con la lista serializada de versiones"""

        evidencia = self.get_object()
        versiones = evidencia.versiones.order_by("-version")

        return Response(VersionEvidenciaSerializer(versiones, many=True).data)

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

        qs = VersionEvidencia.objects.all()
        return filtrar_por_rol(qs, self.request, dept_field="evidencia__asignacion__departamento")

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

        qs = Observacion.objects.filter(activo=True)
        return filtrar_por_rol(qs, self.request, dept_field="version__evidencia__asignacion__departamento")

    def perform_create(self, serializer):
        """@brief Crea una observación y ejecuta acciones secundarias
        @details Asigna el usuario actual como autor, registra la acción en auditoría,
        envía notificación al propietario de la evidencia y cambia el estado
        de la asignación a OBSERVADA.
        @param serializer Serializer con los datos validados de la observación"""

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
