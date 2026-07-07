from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Periodo, Criterio, Indicador, Asignacion
from .serializers import (
    PeriodoSerializer,
    CriterioSerializer,
    IndicadorSerializer,
    AsignacionSerializer
)
from accounts.permissions import CustomModelPermissions
from organization.models import Departamento, Facultad
from accounts.models import Usuario


class PeriodoViewSet(viewsets.ModelViewSet):
    queryset = Periodo.objects.all().order_by('-fecha_inicio')
    serializer_class = PeriodoSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class CriterioViewSet(viewsets.ModelViewSet):
    queryset = Criterio.objects.all().order_by('nombre')
    serializer_class = CriterioSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class IndicadorViewSet(viewsets.ModelViewSet):
    queryset = Indicador.objects.all().order_by('nombre')
    serializer_class = IndicadorSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


class AsignacionViewSet(viewsets.ModelViewSet):
    queryset = Asignacion.objects.all().order_by('periodo', 'departamento')
    serializer_class = AsignacionSerializer
    permission_classes = [IsAuthenticated, CustomModelPermissions]


# --- Dashboard & Search Views ---

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_resumen(request):
    total_departamentos = Departamento.objects.count()
    total_indicadores = Indicador.objects.count()
    total_asignaciones = Asignacion.objects.count()
    pendientes = Asignacion.objects.filter(estado='pendiente').count()
    observadas = Asignacion.objects.filter(estado='en_progreso').count()
    aprobadas = Asignacion.objects.filter(estado='aprobado').count()
    rechazadas = Asignacion.objects.filter(estado='rechazado').count()

    return Response({
        'departamentos': total_departamentos,
        'indicadores': total_indicadores,
        'asignaciones': total_asignaciones,
        'pendientes': pendientes,
        'observadas': observadas,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_departamento(request, departamento_id):
    try:
        depto = Departamento.objects.get(id=departamento_id)
    except Departamento.DoesNotExist:
        return Response({'error': 'Departamento no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    asignaciones = Asignacion.objects.filter(departamento=depto)
    total_asignados = asignaciones.count()
    total_indicadores = asignaciones.values('indicador').distinct().count()
    con_evidencia = asignaciones.filter(estado__in=['completado', 'aprobado']).count()
    sin_evidencia = asignaciones.filter(estado__in=['pendiente', 'en_progreso', 'rechazado']).count()
    aprobados = asignaciones.filter(estado='aprobado').count()
    pendientes = asignaciones.filter(estado='pendiente').count()

    return Response({
        'departamento_id': depto.id,
        'departamento': depto.nombre,
        'facultad': depto.facultad.nombre,
        'indicadores': total_indicadores,
        'asignados': total_asignados,
        'con_evidencia': con_evidencia,
        'sin_evidencia': sin_evidencia,
        'aprobados': aprobados,
        'pendientes': pendientes,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_periodo(request):
    asignaciones = Asignacion.objects.all()
    periodo_id = request.query_params.get('periodo_id')
    departamento_id = request.query_params.get('departamento_id')

    if periodo_id:
        asignaciones = asignaciones.filter(periodo_id=periodo_id)
    if departamento_id:
        asignaciones = asignaciones.filter(departamento_id=departamento_id)

    deptos_ids = asignaciones.values_list('departamento_id', flat=True).distinct()
    data = []
    for depto in Departamento.objects.filter(id__in=deptos_ids):
        depto_asigs = asignaciones.filter(departamento=depto)
        total = depto_asigs.count()
        completadas = depto_asigs.filter(estado__in=['completado', 'aprobado']).count()
        avance = round((completadas / total * 100)) if total > 0 else 0

        data.append({
            'departamento_id': depto.id,
            'departamento': depto.nombre,
            'facultad': depto.facultad.nombre,
            'total_asignaciones': total,
            'completadas': completadas,
            'avance': avance,
            'pendientes': depto_asigs.filter(estado='pendiente').count(),
            'en_progreso': depto_asigs.filter(estado='en_progreso').count(),
            'aprobados': depto_asigs.filter(estado='aprobado').count(),
            'rechazados': depto_asigs.filter(estado='rechazado').count(),
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_avance(request):
    data = []
    for facultad in Facultad.objects.filter(departamentos__asignaciones__isnull=False).distinct():
        deptos = facultad.departamentos.all()
        total_asignaciones = Asignacion.objects.filter(departamento__in=deptos).count()
        completadas = Asignacion.objects.filter(
            departamento__in=deptos,
            estado__in=['completado', 'aprobado']
        ).count()
        avance = round((completadas / total_asignaciones * 100)) if total_asignaciones > 0 else 0

        data.append({
            'facultad_id': facultad.id,
            'facultad': facultad.nombre,
            'total_asignaciones': total_asignaciones,
            'completadas': completadas,
            'avance': avance,
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_view(request):
    q = request.query_params.get('q', '').strip()
    if not q or len(q) < 2:
        return Response(
            {'error': 'Proporcione al menos 2 caracteres para buscar'},
            status=status.HTTP_400_BAD_REQUEST
        )

    results = {
        'departamentos': [],
        'facultades': [],
        'indicadores': [],
        'criterios': [],
        'periodos': [],
        'usuarios': [],
    }

    deptos = Departamento.objects.filter(
        Q(nombre__icontains=q) | Q(descripcion__icontains=q)
    )[:10]
    results['departamentos'] = [
        {'id': d.id, 'nombre': d.nombre, 'facultad': d.facultad.nombre}
        for d in deptos
    ]

    facultades = Facultad.objects.filter(
        Q(nombre__icontains=q) | Q(descripcion__icontains=q)
    )[:10]
    results['facultades'] = [
        {'id': f.id, 'nombre': f.nombre}
        for f in facultades
    ]

    indicadores = Indicador.objects.filter(
        Q(nombre__icontains=q) | Q(descripcion__icontains=q)
    )[:10]
    results['indicadores'] = [
        {'id': i.id, 'nombre': i.nombre, 'criterio': i.criterio.nombre}
        for i in indicadores
    ]

    criterios = Criterio.objects.filter(
        Q(nombre__icontains=q) | Q(descripcion__icontains=q)
    )[:10]
    results['criterios'] = [
        {
            'id': c.id,
            'nombre': c.nombre,
            'periodo': c.periodo.nombre if c.periodo else None
        }
        for c in criterios
    ]

    periodos = Periodo.objects.filter(nombre__icontains=q)[:10]
    results['periodos'] = [
        {'id': p.id, 'nombre': p.nombre}
        for p in periodos
    ]

    usuarios = Usuario.objects.filter(
        Q(username__icontains=q)
        | Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(email__icontains=q)
    )[:10]
    results['usuarios'] = [
        {
            'id': u.id,
            'username': u.username,
            'nombre': f'{u.first_name} {u.last_name}'.strip(),
            'email': u.email,
        }
        for u in usuarios
    ]

    return Response(results)
