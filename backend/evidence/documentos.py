"""Flujo documental explícito: requisitos obligatorios, versiones y decisiones independientes."""

from contextlib import contextmanager
from pathlib import PurePosixPath

from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import Max
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import ROLES_SIN_RESTRICCION, _grupos_usuario, es_evaluador_externo, filtrar_por_rol
from auditoria.utils import registrar_auditoria
from evaluation.models import Asignacion, EstadoAsignacion, HistorialEstado, Periodo
from evaluation.services import finalizar_periodos_vencidos
from notificaciones.utils import crear_notificacion

from .models import EstadoDocumento, RevisionDocumento, SolicitudDocumental, VersionDocumento
from .validators import validate_evidence_file


def puede_definir(request):
    return (request.user.is_superuser or bool(_grupos_usuario(request.user) & ROLES_SIN_RESTRICCION)) and request.user.has_perm('evaluation.change_asignacion')


def puede_revisar(request):
    return (puede_definir(request) or (
        not es_evaluador_externo(request) and 'Revisor Institucional' in _grupos_usuario(request.user)
    )) and request.user.has_perm('evaluation.change_asignacion')


def puede_aportar(request):
    return not es_evaluador_externo(request) and (
        request.user.has_perm('evidence.add_versionevidencia') or request.user.has_perm('evidence.add_evidencia')
    )


def asignaciones_visibles(request):
    return filtrar_por_rol(Asignacion.objects.all(), request, dept_field='unidad_responsable')


def validar_cierre_documental(asignacion):
    solicitudes = asignacion.solicitudes_documentales.all()
    if not solicitudes.exists() or solicitudes.exclude(estado=EstadoDocumento.APROBADA).exists():
        raise ModelValidationError({'estado': 'Todos los documentos solicitados deben estar aprobados antes del cierre global.'})
    for solicitud in solicitudes:
        ultima = solicitud.versiones.order_by('-numero').first()
        revision = ultima.revisiones.first() if ultima else None
        if revision is None or revision.decision != EstadoDocumento.APROBADA:
            raise ModelValidationError({'estado': 'La última versión de cada documento debe tener una aprobación explícita.'})


def validar_carga(solicitud):
    if solicitud.estado not in ('pendiente', 'borrador', 'observada'):
        raise ValidationError('Solo se admiten versiones antes del envío o al corregir cambios solicitados.')


@contextmanager
def bloquear_evidencia_unica(asignacion):
    with transaction.atomic():
        Periodo.objects.select_for_update().get(pk=asignacion.periodo_id)
        actual = Asignacion.objects.select_for_update().get(pk=asignacion.pk)
        if actual.periodo_id != asignacion.periodo_id:
            raise ValidationError('La asignación cambió de período; vuelva a consultarla.')
        if actual.gestion_documental:
            raise ValidationError({'asignacion': 'Gestione la entrega desde sus solicitudes documentales.'})
        yield


@contextmanager
def bloquear_asignacion(request, pk):
    """Orden común de bloqueos: período, asignación y después solicitud."""
    visible = get_object_or_404(asignaciones_visibles(request), pk=pk)
    with transaction.atomic():
        periodo = Periodo.objects.select_for_update().get(pk=visible.periodo_id)
        asignacion = Asignacion.objects.select_for_update().get(pk=visible.pk)
        if asignacion.periodo_id != periodo.pk:
            raise ValidationError('La asignación cambió de período; vuelva a consultarla.')
        # Reevalúa permisos sobre el estado persistido, sin confiar en campos del cliente.
        get_object_or_404(asignaciones_visibles(request), pk=asignacion.pk)
        if not periodo.activo:
            raise ValidationError({'periodo': 'El período finalizó; solo permite consulta.'})
        if asignacion.estado in (EstadoAsignacion.APROBADO, EstadoAsignacion.COMPLETADO):
            raise ValidationError('La asignación cerrada no permite cambios documentales.')
        yield asignacion


def registrar(request, solicitud, accion, comentario=''):
    registrar_auditoria(request.user, accion, 'SolicitudDocumental', solicitud.pk,
        f'Asignación {solicitud.asignacion_id}; documento {solicitud.pk} ({solicitud.titulo}). {comentario}')


class RevisionDocumentoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', default=None)

    class Meta:
        model = RevisionDocumento
        fields = ['id', 'decision', 'comentario', 'usuario_nombre', 'fecha']


class VersionDocumentoSerializer(serializers.ModelSerializer):
    nombre_archivo = serializers.SerializerMethodField()
    revisiones = serializers.SerializerMethodField()
    subido_por_nombre = serializers.CharField(source='subido_por.username', default=None)

    class Meta:
        model = VersionDocumento
        fields = ['id', 'numero', 'comentario', 'fecha_subida', 'subido_por_nombre', 'nombre_archivo', 'revisiones']

    def get_nombre_archivo(self, obj):
        return PurePosixPath(obj.archivo.name).name

    def get_revisiones(self, obj):
        if es_evaluador_externo(self.context['request']):
            return []
        return RevisionDocumentoSerializer(obj.revisiones.all(), many=True).data


class SolicitudDocumentalSerializer(serializers.ModelSerializer):
    versiones = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = SolicitudDocumental
        fields = ['id', 'asignacion', 'titulo', 'descripcion', 'estado', 'estado_display', 'fecha_creacion', 'versiones']
        read_only_fields = ['estado', 'fecha_creacion']

    def get_versiones(self, obj):
        versiones = obj.versiones.all()
        if es_evaluador_externo(self.context['request']):
            versiones = versiones[:1]
        return VersionDocumentoSerializer(versiones, many=True, context=self.context).data


class SolicitudDocumentalViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SolicitudDocumentalSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not request.user.has_perms(['evaluation.view_asignacion', 'evidence.view_evidencia']):
            raise PermissionDenied()
        finalizar_periodos_vencidos()

    def get_queryset(self):
        qs = SolicitudDocumental.objects.filter(asignacion__in=asignaciones_visibles(self.request))
        periodo = self.request.query_params.get('periodo')
        if periodo is not None:
            if not str(periodo).isdigit() or int(periodo) < 1:
                raise ValidationError({'periodo': 'Debe ser un identificador entero positivo.'})
            qs = qs.filter(asignacion__periodo_id=periodo)
        asignacion = self.request.query_params.get('asignacion')
        if asignacion is not None:
            if not str(asignacion).isdigit():
                raise ValidationError({'asignacion': 'Debe ser un identificador entero.'})
            qs = qs.filter(asignacion_id=asignacion)
        return qs.select_related('asignacion__periodo').prefetch_related('versiones__revisiones', 'versiones__subido_por')

    def list(self, request):
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page if page is not None else self.get_queryset(), many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    def retrieve(self, request, pk=None):
        return Response(self.get_serializer(self.get_object()).data)

    @action(detail=False, methods=['get'])
    def contexto(self, request):
        pk = request.query_params.get('asignacion')
        if not str(pk).isdigit():
            raise ValidationError({'asignacion': 'Indique la asignación.'})
        asignacion = get_object_or_404(asignaciones_visibles(request).select_related('periodo'), pk=pk)
        abierta = asignacion.periodo.activo and asignacion.estado not in ('aprobado', 'completado')
        iniciable = bool(asignacion.indicador_marco_id and asignacion.estado == 'pendiente'
            and not hasattr(asignacion, 'evidencia') and not asignacion.evidencias.exists())
        solicitudes = self.get_queryset().filter(asignacion=asignacion)
        try:
            validar_cierre_documental(asignacion)
            completa = True
        except ModelValidationError:
            completa = False
        return Response({
            'gestion_documental': asignacion.gestion_documental,
            'puede_definir': puede_definir(request) and abierta and (asignacion.gestion_documental or iniciable),
            'puede_aportar': puede_aportar(request) and abierta,
            'puede_revisar': puede_revisar(request) and abierta,
            'puede_aprobar_global': puede_revisar(request) and abierta and asignacion.gestion_documental and completa,
            'total': solicitudes.count(), 'aprobadas': solicitudes.filter(estado='aprobada').count(),
        })

    def create(self, request):
        if not puede_definir(request) or not request.user.has_perm('evaluation.change_asignacion'):
            raise PermissionDenied('Solo Administración y Coordinación pueden definir solicitudes.')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with bloquear_asignacion(request, serializer.validated_data['asignacion'].pk) as asignacion:
            if not asignacion.indicador_marco_id:
                raise ValidationError('La gestión documental requiere una asignación directa al marco.')
            if not asignacion.gestion_documental:
                if asignacion.estado != 'pendiente' or hasattr(asignacion, 'evidencia') or asignacion.evidencias.exists():
                    raise ValidationError('El flujo documental se inicia sobre una asignación pendiente sin evidencias previas.')
                asignacion.gestion_documental = True
                asignacion.save(update_fields=['gestion_documental'])
            solicitud = serializer.save(creada_por=request.user, asignacion=asignacion)
            registrar(request, solicitud, 'Crear solicitud documental')
        return Response(self.get_serializer(solicitud).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        if not puede_definir(request):
            raise PermissionDenied()
        solicitud = self.get_object()
        with bloquear_asignacion(request, solicitud.asignacion_id):
            solicitud = SolicitudDocumental.objects.select_for_update().get(pk=solicitud.pk)
            if solicitud.versiones.exists():
                raise ValidationError('La solicitud con entregas conserva su definición e historial.')
            if 'asignacion' in request.data:
                raise ValidationError('No puede trasladar una solicitud a otra asignación.')
            serializer = self.get_serializer(solicitud, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            registrar(request, solicitud, 'Editar solicitud documental')
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        if not puede_definir(request):
            raise PermissionDenied()
        solicitud = self.get_object()
        with bloquear_asignacion(request, solicitud.asignacion_id):
            solicitud = SolicitudDocumental.objects.select_for_update().get(pk=solicitud.pk)
            if solicitud.versiones.exists():
                raise ValidationError('No puede eliminar una solicitud con entregas.')
            registrar(request, solicitud, 'Eliminar solicitud documental')
            solicitud.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def subir_version(self, request, pk=None):
        if not puede_aportar(request):
            raise PermissionDenied()
        solicitud = self.get_object()
        archivo = request.FILES.get('archivo')
        if archivo is None:
            raise ValidationError({'archivo': 'Adjunte un archivo.'})
        validate_evidence_file(archivo)
        version = None
        try:
            with bloquear_asignacion(request, solicitud.asignacion_id):
                solicitud = SolicitudDocumental.objects.select_for_update().get(pk=solicitud.pk)
                validar_carga(solicitud)
                numero = (solicitud.versiones.aggregate(n=Max('numero'))['n'] or 0) + 1
                version = VersionDocumento(solicitud=solicitud, archivo=archivo, numero=numero,
                    comentario=str(request.data.get('comentario', '')), subido_por=request.user)
                version.save()
                solicitud.estado = EstadoDocumento.BORRADOR
                solicitud.save(update_fields=['estado'])
                registrar(request, solicitud, 'Subir versión documental', f'Versión {numero}, ID {version.pk}.')
        except Exception:
            if version is not None and version.archivo and version.archivo._committed:
                version.archivo.delete(save=False)
            raise
        return Response(VersionDocumentoSerializer(version, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        if not puede_aportar(request):
            raise PermissionDenied()
        solicitud = self.get_object()
        with bloquear_asignacion(request, solicitud.asignacion_id) as asignacion:
            solicitud = SolicitudDocumental.objects.select_for_update().get(pk=solicitud.pk)
            if solicitud.estado != EstadoDocumento.BORRADOR or not solicitud.versiones.exists():
                raise ValidationError('Debe cargar una versión nueva antes de enviarla.')
            solicitud.estado = EstadoDocumento.EN_REVISION
            solicitud.save(update_fields=['estado'])
            if asignacion.estado == EstadoAsignacion.PENDIENTE:
                asignacion.estado = EstadoAsignacion.EN_PROGRESO
                asignacion.save(update_fields=['estado'])
                HistorialEstado.objects.create(asignacion=asignacion, estado_anterior='pendiente',
                    estado_nuevo='en_progreso', usuario=request.user, comentario='Primer documento enviado a revisión.')
            registrar(request, solicitud, 'Enviar documento a revisión')
        return Response(self.get_serializer(solicitud).data)

    def decidir(self, request, decision):
        if not puede_revisar(request):
            raise PermissionDenied()
        solicitud = self.get_object()
        comentario = str(request.data.get('comentario', '')).strip()
        if decision == EstadoDocumento.OBSERVADA and not comentario:
            raise ValidationError({'comentario': 'Explique los cambios solicitados.'})
        with bloquear_asignacion(request, solicitud.asignacion_id) as asignacion:
            solicitud = SolicitudDocumental.objects.select_for_update().get(pk=solicitud.pk)
            ultima = solicitud.versiones.first()
            if solicitud.estado != EstadoDocumento.EN_REVISION or ultima is None:
                raise ValidationError('El documento no está enviado a revisión.')
            if str(request.data.get('version_id')) != str(ultima.pk):
                raise ValidationError({'version_id': 'La decisión debe identificar la última versión enviada.'})
            RevisionDocumento.objects.create(version=ultima, decision=decision, comentario=comentario, usuario=request.user)
            solicitud.estado = decision
            solicitud.save(update_fields=['estado'])
            registrar(request, solicitud, 'Revisar documento', f'Versión {ultima.numero}, ID {ultima.pk}: {decision}. {comentario}')
            for usuario_id in {asignacion.encargado_id, ultima.subido_por_id} - {None}:
                from accounts.models import Usuario

                crear_notificacion(Usuario.objects.get(pk=usuario_id), 'Documento revisado',
                    f'{solicitud.titulo}, versión {ultima.numero}: {decision}. {comentario}')
        return Response(self.get_serializer(solicitud).data)

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        return self.decidir(request, EstadoDocumento.APROBADA)

    @action(detail=True, methods=['post'])
    def solicitar_cambios(self, request, pk=None):
        return self.decidir(request, EstadoDocumento.OBSERVADA)

    @action(detail=True, methods=['get'])
    def descargar(self, request, pk=None):
        solicitud = self.get_object()
        versiones = solicitud.versiones.all()
        if es_evaluador_externo(request):
            versiones = versiones.filter(pk=versiones.first().pk) if versiones.exists() else versiones
        version_id = request.query_params.get('version')
        if version_id is not None and not str(version_id).isdigit():
            raise ValidationError({'version': 'Debe ser un identificador entero.'})
        version = get_object_or_404(versiones, pk=version_id) if version_id else versiones.first()
        if version is None:
            raise ValidationError('El documento todavía no tiene archivo.')
        registrar(request, solicitud, 'Descargar documento', f'Versión {version.numero}, ID {version.pk}.')
        return FileResponse(version.archivo.open('rb'), as_attachment=True, filename=PurePosixPath(version.archivo.name).name)
