from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from organization.models import Facultad, Departamento
from evaluation.models import Criterio, Indicador
from accounts.permissions import departamentos_permitidos

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search(request):
    q = request.query_params.get('q', '').strip()
    if not q:
        return Response({
            'indicadores': [],
            'departamentos': [],
            'facultades': [],
            'criterios': [],
            'usuarios': [],
        })

    deptos_ids = departamentos_permitidos(request)

    def restringir_indicador(qs):
        if deptos_ids is not None:
            return qs.filter(asignaciones__departamento_id__in=deptos_ids)
        return qs

    def restringir_criterio(qs):
        if deptos_ids is not None:
            return qs.filter(indicadores__asignaciones__departamento_id__in=deptos_ids)
        return qs

    indicadores = restringir_indicador(Indicador.objects.filter(activo=True)).filter(
        nombre__icontains=q
    ) | restringir_indicador(Indicador.objects.filter(activo=True)).filter(
        descripcion__icontains=q
    )
    indicadores_data = [
        {'id': i.pk, 'nombre': i.nombre, 'criterio': i.criterio.nombre, 'tipo': 'Indicador'}
        for i in indicadores.distinct()[:10]
    ]

    deptos_qs = Departamento.objects.filter(activo=True, nombre__icontains=q)
    if deptos_ids is not None:
        deptos_qs = deptos_qs.filter(pk__in=deptos_ids)
    departamentos_data = [
        {'id': d.pk, 'nombre': d.nombre, 'facultad': d.facultad.nombre, 'tipo': 'Departamento'}
        for d in deptos_qs[:10]
    ]

    facultades_qs = Facultad.objects.filter(activo=True, nombre__icontains=q)
    if deptos_ids is not None:
        facultades_qs = facultades_qs.filter(departamentos__pk__in=deptos_ids).distinct()
    facultades_data = [
        {'id': f.pk, 'nombre': f.nombre, 'tipo': 'Facultad'}
        for f in facultades_qs[:10]
    ]

    criterios = restringir_criterio(Criterio.objects.filter(activo=True)).filter(
        nombre__icontains=q
    ) | restringir_criterio(Criterio.objects.filter(activo=True)).filter(
        descripcion__icontains=q
    )
    criterios_data = [
        {'id': c.pk, 'nombre': c.nombre, 'periodo': c.periodo.nombre if c.periodo else None, 'tipo': 'Criterio'}
        for c in criterios.distinct()[:10]
    ]

    usuarios = User.objects.filter(
        username__icontains=q
    ) | User.objects.filter(
        email__icontains=q
    ) | User.objects.filter(
        first_name__icontains=q
    ) | User.objects.filter(
        last_name__icontains=q
    )
    usuarios_data = [
        {'id': u.pk, 'username': u.username, 'email': u.email, 'nombre_completo': f'{u.first_name} {u.last_name}'.strip(), 'tipo': 'Usuario'}
        for u in usuarios.distinct()[:10]
    ]

    return Response({
        'indicadores': indicadores_data,
        'departamentos': departamentos_data,
        'facultades': facultades_data,
        'criterios': criterios_data,
        'usuarios': usuarios_data,
    })
