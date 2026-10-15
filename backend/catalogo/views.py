"""@file views.py
@brief ViewSets de solo lectura para consultar el catalogo EQ-SIDACES.
@details Solo lectura (GET/list/retrieve); requiere autenticacion (IsAuthenticated,
politica global del proyecto). Los filtros por padre/version se validan y un
filtro inexistente responde 400; un identificador de detalle inexistente responde
404. select_related en listas y subconsultas por metodo en detalle evitan N+1.
"""

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import Componente, CriterioMarco, Dimension, Estandar, IndicadorMarco, VersionMarcoEvaluacion
from .serializers import (
    ComponenteSerializer,
    CriterioSerializer,
    DimensionSerializer,
    EstandarSerializer,
    IndicadorSerializer,
    VersionMarcoEvaluacionSerializer,
)


def _resolver_version(param: str) -> VersionMarcoEvaluacion:
    """Acepta slug (legible) o id numerico; 400 si no existe."""
    filtro = {"slug": param} if not param.isdigit() else {"pk": int(param)}
    try:
        return VersionMarcoEvaluacion.objects.get(**filtro)
    except VersionMarcoEvaluacion.DoesNotExist:
        raise ValidationError(
            {"version": f"No existe una version de marco con el identificador '{param}'."}
        )


def _resolver_objeto(model, param: str, nombre: str):
    if not param.isdigit():
        raise ValidationError({nombre: f"El filtro '{nombre}' debe ser un identificador numerico."})
    try:
        return model.objects.get(pk=int(param))
    except model.DoesNotExist:
        raise ValidationError({nombre: f"No existe {nombre} con identificador '{param}'."})


class VersionMarcoEvaluacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VersionMarcoEvaluacion.objects.all().order_by("-fecha_vigencia", "id")
    serializer_class = VersionMarcoEvaluacionSerializer
    permission_classes = [IsAuthenticated]


class DimensionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DimensionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Dimension.objects.select_related("version_marco").order_by("version_marco_id", "orden", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        version = self.request.query_params.get("version")
        if version is not None:
            qs = qs.filter(version_marco=_resolver_version(version))
        return qs


class ComponenteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ComponenteSerializer
    permission_classes = [IsAuthenticated]
    queryset = Componente.objects.select_related(
        "version_marco", "dimension"
    ).order_by("dimension_id", "orden", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        dimension = self.request.query_params.get("dimension")
        if dimension is not None:
            qs = qs.filter(dimension=_resolver_objeto(Dimension, dimension, "dimension"))
        return qs


class CriterioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CriterioSerializer
    permission_classes = [IsAuthenticated]
    queryset = CriterioMarco.objects.select_related(
        "version_marco", "componente__dimension"
    ).order_by("componente_id", "orden", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        componente = self.request.query_params.get("componente")
        if componente is not None:
            qs = qs.filter(componente=_resolver_objeto(Componente, componente, "componente"))
        return qs


class EstandarViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EstandarSerializer
    permission_classes = [IsAuthenticated]
    queryset = Estandar.objects.select_related(
        "version_marco", "criterio_marco__componente__dimension"
    ).order_by("criterio_marco_id", "orden", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        criterio = self.request.query_params.get("criterio")
        if criterio is not None:
            qs = qs.filter(criterio_marco=_resolver_objeto(CriterioMarco, criterio, "criterio"))
        return qs


class IndicadorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IndicadorSerializer
    permission_classes = [IsAuthenticated]
    queryset = IndicadorMarco.objects.select_related(
        "version_marco", "estandar__criterio_marco__componente__dimension"
    ).order_by("estandar_id", "orden", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        estandar = self.request.query_params.get("estandar")
        if estandar is not None:
            qs = qs.filter(estandar=_resolver_objeto(Estandar, estandar, "estandar"))
        return qs
