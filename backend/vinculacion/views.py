"""Vistas de la API de vinculación.

CorrespondenciaViewSet: lista/consulta (alcance por rol y ámbito del origen
operativo), creación de propuestas (crear_propuesta) y acciones de estado
confirmar/rechazar/desconfirmar (métodos de dominio, con select_for_update y
auditoría en la misma transacción). No se exponen PUT/PATCH/DELETE: los sellos
y el estado solo cambian por los servicios de dominio. Los filtros de versión
usan version_marco de la correspondencia (sin conmutar a la versión activa).

ContextoCriterio/ContextoIndicador: lectura del contexto de correspondencias de
un origen operativo; un origen inexistente o fuera del ámbito responde 404
genérico (ocultación, patrón del proyecto).

Búsqueda inversa marco→operativo: la lista admite filtros opcionales por destino
del marco (dimension, componente, estandar, indicador_marco) para localizar las
correspondencias aplicables a un nodo del catálogo. Se validan igual que los
filtros existentes (400 si el valor no es numérico o no existe) y se aplican
después del alcance por rol, por lo que no amplían la visibilidad.
"""

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import (
    ROLES_SIN_RESTRICCION,
    _grupos_usuario,
    ambitos_activos,
    filtrar_revision,
    revision_con_ambitos,
    unidades_organizacionales_permitidas,
    _unidades_del_ambito,
)
from catalogo.models import Componente, Dimension, Estandar, IndicadorMarco
from django.core.exceptions import ValidationError as DjangoValidationError
from evaluation.models import Asignacion, Criterio, Indicador

from .models import Correspondencia, EstadoCorrespondencia, ProcedenciaCorrespondencia
from .permisos import PermisosCorrespondencia
from .serializers import (
    CorrespondenciaCreacionSerializer,
    CorrespondenciaSerializer,
    TransicionCorrespondenciaSerializer,
)
from .validaciones import validar_destino_en_version


def _alcance_correspondencias(queryset, request):
    """Aplica el alcance del origen operativo al queryset de correspondencias.

    Reutiliza los helpers reales de accounts.permissions: Administrador General,
    Coordinador Quinquenal y superuser ven todo; Evaluador Externo solo
    correspondencias cuyo origen tenga asignaciones aprobadas en sus ámbitos
    (unidad + período); el resto de roles solo orígenes con asignaciones en sus
    unidades organizacionales permitidas.
    """
    user = request.user
    if user.is_superuser or (ROLES_SIN_RESTRICCION & _grupos_usuario(user)):
        return queryset
    grupos = _grupos_usuario(user)
    if "Evaluador Externo" in grupos:
        ambitos = list(ambitos_activos(user))
        if not ambitos:
            return queryset.none()
        alcance = Q(pk__in=[])
        for ambito in ambitos:
            unidades = _unidades_del_ambito(ambito.unidad_organizacional_id)
            alcance |= Q(
                Q(criterio_op__indicadores__asignaciones__unidad_responsable_id__in=unidades)
                & Q(criterio_op__indicadores__asignaciones__periodo_id=ambito.periodo_id)
                & Q(criterio_op__indicadores__asignaciones__estado="aprobado")
            ) | Q(
                Q(indicador_op__asignaciones__unidad_responsable_id__in=unidades)
                & Q(indicador_op__asignaciones__periodo_id=ambito.periodo_id)
                & Q(indicador_op__asignaciones__estado="aprobado")
            )
        return queryset.filter(alcance).distinct()
    if revision_con_ambitos(request):
        return (
            filtrar_revision(queryset, request, "criterio_op__indicadores__asignaciones")
            | filtrar_revision(queryset, request, "indicador_op__asignaciones")
        ).distinct()
    permitidas = unidades_organizacionales_permitidas(request)
    if permitidas is None:
        return queryset
    return queryset.filter(
        Q(criterio_op__indicadores__asignaciones__unidad_responsable_id__in=permitidas)
        | Q(indicador_op__asignaciones__unidad_responsable_id__in=permitidas)
    ).distinct()


def _origen_accesible(request, *, criterio_op=None, indicador_op=None):
    """Verifica que el usuario pueda acceder al origen operativo indicado."""
    user = request.user
    if user.is_superuser or (ROLES_SIN_RESTRICCION & _grupos_usuario(user)):
        return True
    grupos = _grupos_usuario(user)
    if "Evaluador Externo" in grupos:
        ambitos = list(ambitos_activos(user))
        if not ambitos:
            return False
        for ambito in ambitos:
            unidades = _unidades_del_ambito(ambito.unidad_organizacional_id)
            filtros = {"unidad_responsable_id__in": unidades, "periodo_id": ambito.periodo_id, "estado": "aprobado"}
            if criterio_op is not None:
                if Asignacion.objects.filter(indicador__criterio=criterio_op, **filtros).exists():
                    return True
            if indicador_op is not None:
                if Asignacion.objects.filter(indicador=indicador_op, **filtros).exists():
                    return True
        return False
    if revision_con_ambitos(request):
        asignaciones = filtrar_revision(Asignacion.objects.all(), request)
        if criterio_op is not None:
            return asignaciones.filter(indicador__criterio=criterio_op).exists()
        if indicador_op is not None:
            return asignaciones.filter(indicador=indicador_op).exists()
        return False
    permitidas = unidades_organizacionales_permitidas(request)
    if permitidas is None:
        return True
    if criterio_op is not None:
        return Asignacion.objects.filter(indicador__criterio=criterio_op, unidad_responsable_id__in=permitidas).exists()
    if indicador_op is not None:
        return Asignacion.objects.filter(indicador=indicador_op, unidad_responsable_id__in=permitidas).exists()
    return False


def _resolver_version_filtro(param):
    """Acepta slug o id; 400 si no existe. El filtro usa version_marco de la fila."""
    from catalogo.models import VersionMarcoEvaluacion

    filtro = {"slug": param} if not param.isdigit() else {"pk": int(param)}
    try:
        return VersionMarcoEvaluacion.objects.get(**filtro)
    except VersionMarcoEvaluacion.DoesNotExist:
        raise ValidationError({"version": f"No existe una versión de marco con el identificador '{param}'."})


def _resolver_id_modelo(param, nombre, model):
    """Filtro numérico por PK; 400 si no es numérico o el registro no existe."""
    if not param.isdigit():
        raise ValidationError({nombre: f"El filtro '{nombre}' debe ser un identificador numérico."})
    try:
        return model.objects.get(pk=int(param))
    except model.DoesNotExist:
        raise ValidationError({nombre: f"No existe {nombre} con identificador '{param}'."})


class CorrespondenciaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """API de correspondencias: lectura, creación de propuestas y transiciones."""

    serializer_class = CorrespondenciaSerializer
    permission_classes = [IsAuthenticated, PermisosCorrespondencia]
    http_method_names = ["get", "post", "head", "options"]
    queryset = Correspondencia.objects.all()

    def get_queryset(self):
        qs = Correspondencia.objects.select_related(
            "criterio_op",
            "indicador_op",
            "dimension",
            "estandar",
            "indicador_marco",
            "version_marco",
            "creado_por",
            "confirmado_por",
            "rechazado_por",
        ).order_by("-fecha_creacion", "-id")
        qs = _alcance_correspondencias(qs, self.request)
        version = self.request.query_params.get("version")
        if version is not None:
            qs = qs.filter(version_marco=_resolver_version_filtro(version))
        estado = self.request.query_params.get("estado")
        if estado is not None:
            if estado not in EstadoCorrespondencia.values:
                raise ValidationError({"estado": f"Estado inválido: '{estado}'."})
            qs = qs.filter(estado=estado)
        criterio_op = self.request.query_params.get("criterio_op")
        if criterio_op is not None:
            if not criterio_op.isdigit():
                raise ValidationError({"criterio_op": "El filtro 'criterio_op' debe ser un identificador numérico."})
            qs = qs.filter(criterio_op_id=int(criterio_op))
        indicador_op = self.request.query_params.get("indicador_op")
        if indicador_op is not None:
            if not indicador_op.isdigit():
                raise ValidationError({"indicador_op": "El filtro 'indicador_op' debe ser un identificador numérico."})
            qs = qs.filter(indicador_op_id=int(indicador_op))
        # Búsqueda inversa marco→operativo: filtros por destino del marco.
        # dimension y estandar abarcan el subárbol (destino dimensión o estándar
        # bajo ella; destino estándar o indicador del marco bajo ese estándar);
        # componente solo acepta destinos anclados a un estándar o indicador de
        # ese componente (una correspondencia a dimensión no queda anclada a un
        # componente).
        dimension = self.request.query_params.get("dimension")
        if dimension is not None:
            dim = _resolver_id_modelo(dimension, "dimension", Dimension)
            qs = qs.filter(
                Q(dimension=dim)
                | Q(estandar__criterio_marco__componente__dimension=dim)
                | Q(indicador_marco__estandar__criterio_marco__componente__dimension=dim)
            ).distinct()
        componente = self.request.query_params.get("componente")
        if componente is not None:
            comp = _resolver_id_modelo(componente, "componente", Componente)
            qs = qs.filter(
                Q(estandar__criterio_marco__componente=comp)
                | Q(indicador_marco__estandar__criterio_marco__componente=comp)
            ).distinct()
        estandar = self.request.query_params.get("estandar")
        if estandar is not None:
            est = _resolver_id_modelo(estandar, "estandar", Estandar)
            qs = qs.filter(Q(estandar=est) | Q(indicador_marco__estandar=est)).distinct()
        indicador_marco = self.request.query_params.get("indicador_marco")
        if indicador_marco is not None:
            qs = qs.filter(indicador_marco=_resolver_id_modelo(indicador_marco, "indicador_marco", IndicadorMarco))
        return qs

    def create(self, request, *args, **kwargs):
        """Crea una propuesta manual mediante el servicio de dominio crear_propuesta()."""
        serializer = CorrespondenciaCreacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        criterio_op = datos.get("criterio_op")
        indicador_op = datos.get("indicador_op")
        if not _origen_accesible(request, criterio_op=criterio_op, indicador_op=indicador_op):
            raise NotFound("No existe el origen solicitado o no tiene acceso al mismo.")
        # Validación central de versión, invocada explícitamente además de crear_propuesta.
        validar_destino_en_version(
            datos["version_marco"],
            dimension=datos.get("dimension"),
            estandar=datos.get("estandar"),
            indicador_marco=datos.get("indicador_marco"),
        )
        try:
            correspondencia = Correspondencia.crear_propuesta(
                actor=request.user,
                version_marco=datos["version_marco"],
                dimension=datos.get("dimension"),
                estandar=datos.get("estandar"),
                indicador_marco=datos.get("indicador_marco"),
                criterio_op=criterio_op,
                indicador_op=indicador_op,
                procedencia=datos.get("procedencia", ProcedenciaCorrespondencia.MANUAL),
                comentario=datos.get("comentario", ""),
            )
        except DjangoValidationError as exc:
            raise ValidationError(getattr(exc, "message_dict", None) or exc.messages)
        except IntegrityError as exc:
            raise ValidationError(
                {"detalle": "Ya existe una correspondencia viva para este par origen-destino."}
            ) from exc
        return Response(self.get_serializer(correspondencia).data, status=status.HTTP_201_CREATED)

    def _ejecutar_transicion(self, request, metodo):
        """Ejecuta una transición de estado con bloqueo pesimista y auditoría atómica."""
        transicion = TransicionCorrespondenciaSerializer(data=request.data)
        transicion.is_valid(raise_exception=True)
        with transaction.atomic():
            correspondencia = self.get_object()
            correspondencia = Correspondencia.objects.select_for_update().get(pk=correspondencia.pk)
            try:
                getattr(correspondencia, metodo)(request.user, transicion.validated_data.get("comentario", ""))
            except DjangoValidationError as exc:
                raise ValidationError(getattr(exc, "message_dict", None) or exc.messages)
        return Response(self.get_serializer(correspondencia).data)

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        """POST /correspondencias/{id}/confirmar/ — propuesta → confirmada."""
        return self._ejecutar_transicion(request, "confirmar")

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        """POST /correspondencias/{id}/rechazar/ — propuesta → rechazada (comentario obligatorio)."""
        return self._ejecutar_transicion(request, "rechazar")

    @action(detail=True, methods=["post"])
    def desconfirmar(self, request, pk=None):
        """POST /correspondencias/{id}/desconfirmar/ — confirmada → propuesta (comentario obligatorio)."""
        return self._ejecutar_transicion(request, "desconfirmar")


class ContextoCriterio(APIView):
    """Contexto de correspondencias de un criterio operativo (GET)."""

    permission_classes = [IsAuthenticated, PermisosCorrespondencia]
    queryset = Correspondencia.objects.all()

    def get(self, request, criterio_id):
        criterio = get_object_or_404(Criterio, pk=criterio_id)
        if not _origen_accesible(request, criterio_op=criterio):
            raise NotFound("No existe el criterio solicitado o no tiene acceso al mismo.")
        qs = _alcance_correspondencias(Correspondencia.objects.all(), request).filter(criterio_op=criterio)
        return Response(
            {
                "origen": {"nivel": "criterio", "id": criterio.pk, "texto": criterio.nombre},
                "correspondencias": CorrespondenciaSerializer(qs, many=True).data,
            }
        )


class ContextoIndicador(APIView):
    """Contexto de correspondencias de un indicador operativo (GET)."""

    permission_classes = [IsAuthenticated, PermisosCorrespondencia]
    queryset = Correspondencia.objects.all()

    def get(self, request, indicador_id):
        indicador = get_object_or_404(Indicador, pk=indicador_id)
        if not _origen_accesible(request, indicador_op=indicador):
            raise NotFound("No existe el indicador solicitado o no tiene acceso al mismo.")
        qs = _alcance_correspondencias(Correspondencia.objects.all(), request).filter(indicador_op=indicador)
        return Response(
            {
                "origen": {"nivel": "indicador", "id": indicador.pk, "texto": indicador.nombre},
                "correspondencias": CorrespondenciaSerializer(qs, many=True).data,
            }
        )
