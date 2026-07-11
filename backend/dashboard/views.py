from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from organization.models import Facultad, Departamento
from evaluation.models import Periodo, Criterio, Indicador, Asignacion, EstadoAsignacion
from evidencias.models import Evidencia


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumen(request):
    deptos = Departamento.objects.filter(activo=True).count()
    indicadores = Indicador.objects.filter(activo=True).count()
    asignaciones = Asignacion.objects.count()

    pendientes = Asignacion.objects.filter(estado=EstadoAsignacion.PENDIENTE).count()
    observadas = Asignacion.objects.filter(estado=EstadoAsignacion.OBSERVADA).count()
    aprobadas = Asignacion.objects.filter(estado=EstadoAsignacion.APROBADO).count()
    rechazadas = Asignacion.objects.filter(estado=EstadoAsignacion.RECHAZADO).count()

    return Response({
        'departamentos': deptos,
        'indicadores': indicadores,
        'asignaciones': asignaciones,
        'pendientes': pendientes,
        'observadas': observadas,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def departamento_dashboard(request, pk):
    try:
        depto = Departamento.objects.get(pk=pk)
    except Departamento.DoesNotExist:
        return Response({'error': 'Departamento no encontrado'}, status=404)

    asignaciones = Asignacion.objects.filter(departamento=depto)
    total_asignados = asignaciones.count()
    indicadores = asignaciones.values('indicador').distinct().count()

    aprobados = asignaciones.filter(estado=EstadoAsignacion.APROBADO).count()
    pendientes = asignaciones.filter(estado=EstadoAsignacion.PENDIENTE).count()

    ids_asignacion = asignaciones.values_list('pk', flat=True)
    con_evidencia = Evidencia.objects.filter(asignacion_id__in=ids_asignacion).values('asignacion').distinct().count()
    sin_evidencia = total_asignados - con_evidencia

    return Response({
        'departamento': {
            'id': depto.pk,
            'nombre': depto.nombre,
            'facultad': depto.facultad.nombre,
        },
        'indicadores': indicadores,
        'asignados': total_asignados,
        'con_evidencia': con_evidencia,
        'sin_evidencia': sin_evidencia,
        'aprobados': aprobados,
        'pendientes': pendientes,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def avance(request):
    resultado = []
    facultades = Facultad.objects.filter(activo=True).prefetch_related('departamentos')

    for facultad in facultades:
        deptos = facultad.departamentos.filter(activo=True)
        total_asignaciones = Asignacion.objects.filter(departamento__in=deptos).count()
        completadas = Asignacion.objects.filter(
            departamento__in=deptos,
            estado__in=[EstadoAsignacion.APROBADO, EstadoAsignacion.COMPLETADO]
        ).count()

        porcentaje = round((completadas / total_asignaciones) * 100, 1) if total_asignaciones > 0 else 0.0

        resultado.append({
            'facultad': facultad.nombre,
            'porcentaje': porcentaje,
        })

    return Response(resultado)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def periodo_dashboard(request, pk):
    try:
        periodo = Periodo.objects.get(pk=pk)
    except Periodo.DoesNotExist:
        return Response({'error': 'Período no encontrado'}, status=404)

    asignaciones = Asignacion.objects.filter(periodo=periodo)
    deptos = Departamento.objects.filter(activo=True).count()
    indicadores = Indicador.objects.filter(activo=True).count()

    pendientes = asignaciones.filter(estado=EstadoAsignacion.PENDIENTE).count()
    observadas = asignaciones.filter(estado=EstadoAsignacion.OBSERVADA).count()
    aprobadas = asignaciones.filter(estado=EstadoAsignacion.APROBADO).count()
    rechazadas = asignaciones.filter(estado=EstadoAsignacion.RECHAZADO).count()

    return Response({
        'periodo': {
            'id': periodo.pk,
            'nombre': periodo.nombre,
        },
        'departamentos': deptos,
        'indicadores': indicadores,
        'asignaciones': asignaciones.count(),
        'pendientes': pendientes,
        'observadas': observadas,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
    })
