"""Filtros aditivos para referencias directas al marco; no infieren correspondencias."""

from rest_framework.exceptions import ValidationError

FILTROS_MARCO = {
    "version_marco": "indicador_marco__version_marco_id",
    "dimension": "indicador_marco__estandar__criterio_marco__componente__dimension_id",
    "componente": "indicador_marco__estandar__criterio_marco__componente_id",
    "criterio_marco": "indicador_marco__estandar__criterio_marco_id",
    "estandar": "indicador_marco__estandar_id",
    "indicador_marco": "indicador_marco_id",
}


def filtrar_por_marco(queryset, parametros, prefijo=""):
    for parametro, campo in FILTROS_MARCO.items():
        valor = parametros.get(parametro)
        if valor is None:
            continue
        if not str(valor).isdigit() or int(valor) < 1:
            raise ValidationError({parametro: "Debe ser un identificador entero positivo."})
        queryset = queryset.filter(**{prefijo + campo: int(valor)})
    return queryset
