"""
@file views.py
@brief Vistas de la app de dashboard.
@details Define las vistas para el panel de control (dashboard)
del sistema de evaluación quinquenal, incluyendo resumen general,
detalles por departamento, avance por facultad y filtrado por período.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import departamentos_permitidos
from evaluation.models import Asignacion, EstadoAsignacion, Indicador, Periodo
from evidencias.models import Evidencia
from organization.models import Departamento, Facultad


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def resumen(request):
    """@brief Retorna un resumen general del dashboard.
    @details Calcula y retorna estadísticas generales del sistema
    incluyendo departamentos, indicadores, asignaciones y estados.
    @param request Request HTTP autenticada.
    @return Response con diccionario de estadísticas generales.
    """
    deptos_ids = departamentos_permitidos(request)
    asig_qs = Asignacion.objects.all()
    if deptos_ids is not None:
        asig_qs = asig_qs.filter(departamento_id__in=deptos_ids)

    deptos = Departamento.objects.filter(activo=True)
    if deptos_ids is not None:
        deptos = deptos.filter(pk__in=deptos_ids)
    total_deptos = deptos.count()

    indicadores_ids = asig_qs.values("indicador").distinct()
    total_indicadores = Indicador.objects.filter(pk__in=indicadores_ids, activo=True).count()

    asignaciones = asig_qs.count()

    obligatorias = asig_qs.filter(indicador__obligatorio=True)
    pendientes = obligatorias.filter(estado=EstadoAsignacion.PENDIENTE).count()
    en_progreso = obligatorias.filter(estado=EstadoAsignacion.EN_PROGRESO).count()
    observadas = obligatorias.filter(estado=EstadoAsignacion.OBSERVADA).count()
    aprobadas = obligatorias.filter(estado=EstadoAsignacion.APROBADO).count()
    rechazadas = obligatorias.filter(estado=EstadoAsignacion.RECHAZADO).count()

    return Response(
        {
            "departamentos": total_deptos,
            "indicadores": total_indicadores,
            "asignaciones": asignaciones,
            "pendientes": pendientes,
            "en_progreso": en_progreso,
            "observadas": observadas,
            "aprobadas": aprobadas,
            "rechazadas": rechazadas,
        }
    )


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

    asignaciones = Asignacion.objects.filter(departamento=depto)
    total_asignados = asignaciones.count()
    indicadores = asignaciones.values("indicador").distinct().count()

    aprobados = asignaciones.filter(estado=EstadoAsignacion.APROBADO).count()
    pendientes = asignaciones.filter(estado=EstadoAsignacion.PENDIENTE).count()

    ids_asignacion = asignaciones.values_list("pk", flat=True)
    con_evidencia = Evidencia.objects.filter(asignacion_id__in=ids_asignacion).values("asignacion").distinct().count()
    sin_evidencia = total_asignados - con_evidencia

    return Response(
        {
            "departamento": {
                "id": depto.pk,
                "nombre": depto.nombre,
                "facultad": depto.facultad.nombre,
            },
            "indicadores": indicadores,
            "asignados": total_asignados,
            "con_evidencia": con_evidencia,
            "sin_evidencia": sin_evidencia,
            "aprobados": aprobados,
            "pendientes": pendientes,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def avance(request):
    """@brief Retorna el porcentaje de avance por facultad.
    @details Calcula el porcentaje de asignaciones completadas
    sobre el total de asignaciones obligatorias para cada facultad.
    @param request Request HTTP autenticada.
    @return Response con lista de facultades y su porcentaje de avance.
    """
    deptos_ids = departamentos_permitidos(request)

    facultades_qs = Facultad.objects.filter(activo=True)
    if deptos_ids is not None:
        facultades_qs = facultades_qs.filter(departamentos__pk__in=deptos_ids).distinct()

    resultado = []
    for facultad in facultades_qs.prefetch_related("departamentos"):
        deptos = facultad.departamentos.filter(activo=True)
        if deptos_ids is not None:
            deptos = deptos.filter(pk__in=deptos_ids)
        total_asignaciones = Asignacion.objects.filter(
            departamento__in=deptos,
            indicador__obligatorio=True,
        ).count()
        completadas = Asignacion.objects.filter(
            departamento__in=deptos,
            indicador__obligatorio=True,
            estado__in=[EstadoAsignacion.APROBADO, EstadoAsignacion.COMPLETADO],
        ).count()

        porcentaje = round((completadas / total_asignaciones) * 100, 1) if total_asignaciones > 0 else 0.0

        resultado.append(
            {
                "facultad": facultad.nombre,
                "porcentaje": porcentaje,
            }
        )

    return Response(resultado)


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
        periodo = Periodo.objects.get(pk=pk)
    except Periodo.DoesNotExist:
        return Response({"error": "Período no encontrado"}, status=404)

    deptos_ids = departamentos_permitidos(request)
    asignaciones = Asignacion.objects.filter(periodo=periodo)
    if deptos_ids is not None:
        asignaciones = asignaciones.filter(departamento_id__in=deptos_ids)

    deptos = Departamento.objects.filter(activo=True)
    if deptos_ids is not None:
        deptos = deptos.filter(pk__in=deptos_ids)

    indicadores_ids = asignaciones.values("indicador").distinct()
    total_indicadores = Indicador.objects.filter(pk__in=indicadores_ids, activo=True).count()

    pendientes = asignaciones.filter(estado=EstadoAsignacion.PENDIENTE).count()
    observadas = asignaciones.filter(estado=EstadoAsignacion.OBSERVADA).count()
    aprobadas = asignaciones.filter(estado=EstadoAsignacion.APROBADO).count()
    rechazadas = asignaciones.filter(estado=EstadoAsignacion.RECHAZADO).count()

    return Response(
        {
            "periodo": {
                "id": periodo.pk,
                "nombre": periodo.nombre,
            },
            "departamentos": deptos.count(),
            "indicadores": total_indicadores,
            "asignaciones": asignaciones.count(),
            "pendientes": pendientes,
            "observadas": observadas,
            "aprobadas": aprobadas,
            "rechazadas": rechazadas,
        }
    )
