"""@file views.py
@brief ViewSets de solo lectura para consultar el catalogo EQ-SIDACES.
@details Solo lectura (GET/list/retrieve); requiere autenticacion (IsAuthenticated,
politica global del proyecto). Los filtros por padre/version se validan y un
filtro inexistente responde 400; un identificador de detalle inexistente responde
404. select_related en listas y subconsultas por metodo en detalle evitan N+1.
El endpoint exportar/ devuelve el arbol completo (o una rama) de una version
como CSV descargable; tambien es de solo lectura (GET).
"""

import csv
import io

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Componente, CriterioMarco, Dimension, Estandar, IndicadorMarco, VersionMarcoEvaluacion
from .serializers import (
    ComponenteSerializer,
    CriterioSerializer,
    DimensionSerializer,
    EstandarSerializer,
    IndicadorSerializer,
    VersionMarcoEvaluacionSerializer,
    es_codigo_sintetico,
)

CABECERA_CSV = (
    "nivel",
    "version",
    "dimension",
    "componente",
    "criterio",
    "estandar",
    "codigo",
    "nombre",
    "codigo_sintetico",
    "estado_revision",
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


def _codigo_de(nodo) -> str:
    """Codigo legible del nodo (codigo_completo cuando existe)."""
    return getattr(nodo, "codigo_completo", "") or getattr(nodo, "codigo", "")


def _texto_de(nodo) -> str:
    """Texto visible del nodo segun el nivel (nombre/redaccion/redaccion_oficial)."""
    return (
        getattr(nodo, "nombre", "")
        or getattr(nodo, "redaccion", "")
        or getattr(nodo, "redaccion_oficial", "")
    )


class ExportarArbolCSV(APIView):
    """Exporta el arbol completo (o una rama con ?dimension=id) de una version en CSV.

    Una fila por nodo con las columnas de ruta jerarquica; solo lectura (GET),
    autenticacion requerida. El CSV incluye BOM UTF-8 para Excel.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        param = request.query_params.get("version")
        if not param:
            raise ValidationError({"version": "Debe indicar el filtro 'version' (slug o id)."})
        version = _resolver_version(param)

        dimensiones = version.dimensiones.prefetch_related(
            "componentes",
            "componentes__criterios_marco",
            "componentes__criterios_marco__estandares",
            "componentes__criterios_marco__estandares__indicadores_marco",
        )
        dimension_param = request.query_params.get("dimension")
        if dimension_param is not None:
            if not dimension_param.isdigit():
                raise ValidationError(
                    {"dimension": "El filtro 'dimension' debe ser un identificador numerico."}
                )
            dimensiones = dimensiones.filter(pk=int(dimension_param))
            if not dimensiones.exists():
                raise ValidationError(
                    {"dimension": f"No existe dimension con identificador '{dimension_param}' en esta version."}
                )

        filas = []
        for dim in dimensiones:
            cod_dim = dim.codigo
            filas.append(
                ["dimension", version.slug, cod_dim, "", "", "", cod_dim, dim.nombre, "", "confirmado"]
            )
            for comp in dim.componentes.all():
                cod_comp = _codigo_de(comp)
                filas.append(
                    ["componente", version.slug, cod_dim, cod_comp, "", "", cod_comp, comp.nombre, "", "confirmado"]
                )
                for cri in comp.criterios_marco.all():
                    cod_cri = _codigo_de(cri)
                    filas.append(
                        ["criterio", version.slug, cod_dim, cod_comp, cod_cri, "", cod_cri, cri.nombre, "", "confirmado"]
                    )
                    for std in cri.estandares.all():
                        cod_std = _codigo_de(std)
                        filas.append(
                            ["estandar", version.slug, cod_dim, cod_comp, cod_cri, cod_std, cod_std, _texto_de(std), "", "confirmado"]
                        )
                        for ind in std.indicadores_marco.all():
                            sintetico = "true" if es_codigo_sintetico(ind.codigo) else "false"
                            filas.append(
                                ["indicador", version.slug, cod_dim, cod_comp, cod_cri, cod_std, _codigo_de(ind), _texto_de(ind), sintetico, "confirmado"]
                            )

        buffer = io.StringIO()
        escritor = csv.writer(buffer, lineterminator="\r\n")
        escritor.writerow(CABECERA_CSV)
        escritor.writerows(filas)
        contenido = "\ufeff" + buffer.getvalue()

        respuesta = HttpResponse(contenido, content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = f'attachment; filename="arbol_eq_sidaces_{version.slug}.csv"'
        return respuesta
