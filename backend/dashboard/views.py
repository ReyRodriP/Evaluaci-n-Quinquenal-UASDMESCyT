"""
@file views.py
@brief Vistas de la app de dashboard.
@details Define las vistas para el panel de control (dashboard)
del sistema de evaluación quinquenal, incluyendo resumen general,
detalles por departamento, avance agrupado y filtrado por período.
"""

from django.core.cache import cache
from django.db.models import Count, Exists, OuterRef, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import (
    _grupos_usuario,
    _unidades_del_ambito,
    departamentos_permitidos,
    filtrar_por_rol,
    periodos_autorizados,
    unidades_organizacionales_permitidas,
)
from evaluation.models import Asignacion, Criterio, EstadoAsignacion, Indicador, Periodo
from evaluation.services import finalizar_periodos_vencidos
from evidence.models import Evidencia as EvidenciaVersionada
from evidencias.models import Evidencia as EvidenciaLegada
from organization.models import Departamento, Facultad, UnidadOrganizacional

CACHE_TTL = 60


def _cache_key(user, name, extra=""):
    return f"dashboard:{name}:{user.pk}:{extra}"


def _filtros_cache(request):
    keys = ("unidad", "tipo", "criterio", "indicador", "estado", "departamento", "agrupar")
    return "|".join(f"{key}={request.query_params.get(key, '')}" for key in keys)


def _asignaciones_dashboard(request, periodo, departamento_id=None):
    if periodo is None:
        return Asignacion.objects.none()

    qs = Asignacion.objects.filter(periodo=periodo)
    qs = filtrar_por_rol(qs, request, dept_field="unidad_responsable")

    unidad_id = request.query_params.get("unidad")
    if unidad_id:
        try:
            unidad_id = int(unidad_id)
        except (TypeError, ValueError):
            return qs.none()
        unidades_permitidas = unidades_organizacionales_permitidas(request)
        if unidades_permitidas is not None and unidad_id not in unidades_permitidas:
            return qs.none()
        descendientes = _unidades_del_ambito(unidad_id)
        if unidades_permitidas is not None:
            descendientes &= set(unidades_permitidas)
        qs = qs.filter(unidad_responsable_id__in=descendientes)

    tipo_id = request.query_params.get("tipo")
    if tipo_id:
        qs = qs.filter(unidad_responsable__tipo_id=tipo_id)

    criterio_id = request.query_params.get("criterio")
    if criterio_id:
        qs = qs.filter(indicador__criterio_id=criterio_id)

    indicador_id = request.query_params.get("indicador")
    if indicador_id:
        qs = qs.filter(indicador_id=indicador_id)

    estado = request.query_params.get("estado")
    if estado:
        valid_states = {value for value, _label in EstadoAsignacion.choices}
        if estado not in valid_states:
            return qs.none()
        qs = qs.filter(estado=estado)

    departamento_id = departamento_id or request.query_params.get("departamento")
    if departamento_id:
        try:
            departamento_id = int(departamento_id)
        except (TypeError, ValueError):
            return qs.none()
        departamentos_visibles = departamentos_permitidos(request)
        if departamentos_visibles is not None and departamento_id not in departamentos_visibles:
            return qs.none()
        qs = qs.filter(unidad_responsable__departamento_legacy_id=departamento_id)

    return qs.distinct()


def _metricas_asignaciones(qs):
    tiene_evidencia = Exists(EvidenciaVersionada.objects.filter(asignacion_id=OuterRef("pk"))) | Exists(
        EvidenciaLegada.objects.filter(asignacion_id=OuterRef("pk"))
    )
    agrupado = qs.annotate(_tiene_evidencia=tiene_evidencia).aggregate(
        total=Count("pk", distinct=True),
        con_evidencia=Count("pk", filter=Q(_tiene_evidencia=True), distinct=True),
        aprobadas=Count("pk", filter=Q(estado=EstadoAsignacion.APROBADO), distinct=True),
        pendientes=Count("pk", filter=Q(estado=EstadoAsignacion.PENDIENTE), distinct=True),
        en_progreso=Count("pk", filter=Q(estado=EstadoAsignacion.EN_PROGRESO), distinct=True),
        observadas=Count("pk", filter=Q(estado=EstadoAsignacion.OBSERVADA), distinct=True),
        rechazadas=Count("pk", filter=Q(estado=EstadoAsignacion.RECHAZADO), distinct=True),
        completadas=Count("pk", filter=Q(estado=EstadoAsignacion.COMPLETADO), distinct=True),
        indicadores=Count("indicador_id", distinct=True),
        unidades=Count("unidad_responsable_id", distinct=True),
        departamentos=Count(
            "unidad_responsable__departamento_legacy_id",
            filter=Q(unidad_responsable__departamento_legacy_id__isnull=False),
            distinct=True,
        ),
    )
    total = agrupado["total"] or 0
    con_evidencia = agrupado["con_evidencia"] or 0
    aprobadas = agrupado["aprobadas"] or 0
    return {
        "asignaciones": total,
        "indicadores": agrupado["indicadores"] or 0,
        "unidades": agrupado["unidades"] or 0,
        "departamentos": agrupado["departamentos"] or 0,
        "evidencias": con_evidencia,
        "sin_evidencia": total - con_evidencia,
        "cobertura_porcentaje": round(con_evidencia * 100 / total, 1) if total else 0,
        "cumplimiento_porcentaje": round(aprobadas * 100 / total, 1) if total else 0,
        "aprobadas": aprobadas,
        "pendientes": agrupado["pendientes"] or 0,
        "en_progreso": agrupado["en_progreso"] or 0,
        "observadas": agrupado["observadas"] or 0,
        "rechazadas": agrupado["rechazadas"] or 0,
        "completadas": agrupado["completadas"] or 0,
    }


def _periodo_solicitado(request, periodo_id=None):
    finalizar_periodos_vencidos()
    periodo_id = periodo_id or request.query_params.get("periodo")
    if not request.user.is_superuser and "Evaluador Externo" in _grupos_usuario(request.user):
        permitidos = periodos_autorizados(request)
        if periodo_id:
            return get_object_or_404(Periodo.objects.filter(pk__in=permitidos), pk=periodo_id)
        return Periodo.objects.filter(pk__in=permitidos, activo=True).order_by("-fecha_inicio").first()
    if periodo_id:
        return get_object_or_404(Periodo, pk=periodo_id)
    return Periodo.objects.filter(activo=True).first()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resumen(request):
    """@brief Retorna un resumen general del dashboard.
    @details Calcula y retorna estadísticas generales del sistema
    incluyendo departamentos, indicadores, asignaciones y estados.
    @param request Request HTTP autenticada.
    @return Response con diccionario de estadísticas generales.
    """
    periodo = _periodo_solicitado(request)
    extra_cache = f"{periodo.pk if periodo else 'sin-periodo'}|{_filtros_cache(request)}"
    key = _cache_key(request.user, "resumen", extra_cache)
    cached = cache.get(key)
    if cached is not None:
        return Response(cached)

    metricas = _metricas_asignaciones(_asignaciones_dashboard(request, periodo))
    data = {
        "periodo": (
            {
                "id": periodo.pk,
                "nombre": periodo.nombre,
                "activo": periodo.activo,
                "fecha_inicio": periodo.fecha_inicio,
                "fecha_fin": periodo.fecha_fin,
            }
            if periodo
            else None
        ),
        **metricas,
    }
    cache.set(key, data, CACHE_TTL)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def departamento_dashboard(request, pk):
    """@brief Retorna estadísticas detalladas de un departamento.
    @details Calcula indicadores, asignaciones, evidencias y estados
    de un departamento específico.
    @param request Request HTTP autenticada.
    @param pk Identificador del departamento.
    @return Response con estadísticas del departamento o error 403/404.
    """
    deptos_ids = departamentos_permitidos(request)
    if deptos_ids is not None and pk not in deptos_ids:
        return Response({"error": "No tienes acceso a este departamento"}, status=403)
    try:
        depto = Departamento.objects.get(pk=pk)
    except Departamento.DoesNotExist:
        return Response({"error": "Departamento no encontrado"}, status=404)

    periodo = _periodo_solicitado(request)
    metricas = _metricas_asignaciones(_asignaciones_dashboard(request, periodo, departamento_id=depto.pk))

    return Response(
        {
            "departamento": {
                "id": depto.pk,
                "nombre": depto.nombre,
                "facultad": depto.facultad.nombre,
            },
            **metricas,
            "asignados": metricas["asignaciones"],
            "con_evidencia": metricas["evidencias"],
            "aprobados": metricas["aprobadas"],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def avance(request):
    """@brief Retorna el porcentaje de avance agrupado.
    @details Calcula el porcentaje de asignaciones aprobadas sobre el total
    de asignaciones para cada grupo. El parámetro ``agrupar`` admite
    ``criterio``, ``unidad`` o ``estado``; omitiéndolo se conserva la
    agrupación histórica por facultad.
    @param request Request HTTP autenticada.
    @return Response con lista de grupos y su porcentaje de avance.
    """
    agrupar = request.query_params.get("agrupar", "")
    if agrupar not in {"", "criterio", "unidad", "estado"}:
        return Response({"error": "El parámetro 'agrupar' no es válido."}, status=400)

    periodo = _periodo_solicitado(request)
    extra_cache = f"{periodo.pk if periodo else 'sin-periodo'}|agrupar={agrupar}|{_filtros_cache(request)}"
    key = _cache_key(request.user, "avance", extra_cache)
    cached = cache.get(key)
    if cached is not None:
        return Response(cached)

    deptos_ids = departamentos_permitidos(request)
    asignaciones_base = _asignaciones_dashboard(request, periodo)
    resultado = []

    if agrupar == "criterio":
        criterios_ids = asignaciones_base.values_list("indicador__criterio_id", flat=True).distinct()
        criterios = Criterio.objects.filter(pk__in=criterios_ids).order_by("pk")
        for criterio in criterios:
            metricas = _metricas_asignaciones(asignaciones_base.filter(indicador__criterio=criterio))
            resultado.append(
                {"nombre": criterio.nombre, "porcentaje": metricas["cumplimiento_porcentaje"], **metricas}
            )
    elif agrupar == "unidad":
        unidades_ids = asignaciones_base.values_list("unidad_responsable_id", flat=True).distinct()
        unidades = UnidadOrganizacional.objects.filter(pk__in=unidades_ids).order_by("pk")
        for unidad in unidades:
            metricas = _metricas_asignaciones(asignaciones_base.filter(unidad_responsable=unidad))
            resultado.append(
                {"nombre": unidad.nombre, "porcentaje": metricas["cumplimiento_porcentaje"], **metricas}
            )
    elif agrupar == "estado":
        total = asignaciones_base.count()
        conteo = (
            asignaciones_base.values("estado")
            .annotate(cantidad=Count("pk"))
            .order_by("estado")
        )
        por_estado = {fila["estado"]: fila["cantidad"] for fila in conteo}
        for value, label in EstadoAsignacion.choices:
            cantidad = por_estado.get(value, 0)
            resultado.append(
                {
                    "estado": value,
                    "nombre": label,
                    "asignaciones": cantidad,
                    "porcentaje": round(cantidad * 100 / total, 1) if total else 0,
                }
            )
    else:
        facultades_qs = Facultad.objects.filter(activo=True)
        if deptos_ids is not None:
            facultades_qs = facultades_qs.filter(departamentos__pk__in=deptos_ids).distinct()

        for facultad in facultades_qs.prefetch_related("departamentos"):
            deptos = facultad.departamentos.filter(activo=True)
            if deptos_ids is not None:
                deptos = deptos.filter(pk__in=deptos_ids)
            metricas = _metricas_asignaciones(
                asignaciones_base.filter(unidad_responsable__departamento_legacy__in=deptos)
            )
            resultado.append(
                {
                    "facultad": facultad.nombre,
                    "porcentaje": metricas["cumplimiento_porcentaje"],
                    **metricas,
                }
            )

    cache.set(key, resultado, CACHE_TTL)
    return Response(resultado)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pendientes(request):
    periodo = _periodo_solicitado(request)
    if periodo is None:
        return Response([])

    grupos = _grupos_usuario(request.user)
    if request.user.is_superuser or grupos & {"Administrador General", "Coordinador Quinquenal"}:
        estados = [
            EstadoAsignacion.PENDIENTE,
            EstadoAsignacion.EN_PROGRESO,
            EstadoAsignacion.OBSERVADA,
            EstadoAsignacion.RECHAZADO,
        ]
    elif "Revisor Institucional" in grupos:
        estados = [EstadoAsignacion.EN_PROGRESO]
    elif "Responsable Departamental" in grupos:
        estados = [EstadoAsignacion.PENDIENTE, EstadoAsignacion.OBSERVADA, EstadoAsignacion.RECHAZADO]
    else:
        return Response([])

    queryset = _asignaciones_dashboard(request, periodo).filter(estado__in=estados).select_related(
        "indicador__criterio", "unidad_responsable", "periodo"
    ).order_by("estado", "pk")[:50]

    rows = []
    for asignacion in queryset:
        evidencia = EvidenciaVersionada.objects.filter(asignacion=asignacion).first()
        rows.append({
            "asignacion_id": asignacion.pk,
            "evidencia_id": evidencia.pk if evidencia else None,
            "indicador": asignacion.indicador.nombre,
            "criterio": asignacion.indicador.criterio.nombre,
            "unidad": asignacion.unidad_responsable.nombre,
            "periodo": asignacion.periodo.nombre,
            "periodo_id": asignacion.periodo_id,
            "estado": asignacion.estado,
            "estado_display": asignacion.get_estado_display(),
        })
    return Response(rows)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def periodo_dashboard(request, pk):
    """@brief Retorna estadísticas del dashboard filtradas por período.
    @details Calcula departamentos, indicadores, asignaciones y estados
    para un período específico.
    @param request Request HTTP autenticada.
    @param pk Identificador del período.
    @return Response con estadísticas del período o error 404.
    """
    try:
        periodo = _periodo_solicitado(request, pk)
    except Http404:
        return Response({"error": "Período no encontrado"}, status=404)
    if periodo is None:
        return Response({"error": "Período no encontrado"}, status=404)

    asignaciones = _asignaciones_dashboard(request, periodo)

    deptos_ids = departamentos_permitidos(request)
    deptos = Departamento.objects.filter(activo=True)
    if deptos_ids is not None:
        deptos = deptos.filter(pk__in=deptos_ids)

    indicadores_ids = asignaciones.values("indicador").distinct()
    total_indicadores = Indicador.objects.filter(pk__in=indicadores_ids, activo=True).count()

    metricas = _metricas_asignaciones(asignaciones)

    return Response(
        {
            "periodo": {
                "id": periodo.pk,
                "nombre": periodo.nombre,
            },
            "departamentos": deptos.count(),
            **{**metricas, "indicadores": total_indicadores},
        }
    )


class _ApiDocSerializer(serializers.Serializer):
    """Serializer generico para documentacion OpenAPI."""


resumen.cls.serializer_class = _ApiDocSerializer
pendientes.cls.serializer_class = _ApiDocSerializer
departamento_dashboard.cls.serializer_class = _ApiDocSerializer
avance.cls.serializer_class = _ApiDocSerializer
periodo_dashboard.cls.serializer_class = _ApiDocSerializer
