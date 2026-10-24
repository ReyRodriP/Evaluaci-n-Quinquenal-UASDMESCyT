"""Consulta de decisiones globales reales, cronología y permisos de asignación."""
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.utils import timezone

from evaluation.models import Asignacion, HistorialEstado
from evidence.test_documentos import EscenarioDocumental
from organization.models import AmbitoRevision


@override_settings(AMBITOS_REVISION_EXPLICITOS=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class HistorialAsignacionTests(EscenarioDocumental, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_escenario()

    def setUp(self):
        self.preparar()

    def consultar(self, actor=None, asignacion=None, **params):
        response = self.cliente(actor).get(f'/api/asignaciones/{(asignacion or self.asignacion).pk}/historial/',
            {'periodo': self.periodo.pk, **params})
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def test_envio_y_cierre_global_conservan_actor_estado_y_comentario(self):
        pk = self.solicitar()
        self.aprobar_documento(pk)
        response = self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/', {'comentario': 'Cierre global confirmado'}, format='json')
        self.assertEqual(response.status_code, 200)
        data = self.consultar(self.responsable)
        self.assertEqual(data['count'], 2)
        cierre, envio = data['results']
        self.assertEqual(cierre['estado_anterior'], 'en_progreso')
        self.assertEqual(cierre['estado_nuevo_display'], 'Aprobado')
        self.assertEqual(cierre['usuario_identificador'], self.revisor.username)
        self.assertEqual(cierre['comentario'], 'Cierre global confirmado')
        self.assertEqual(envio['usuario_identificador'], self.responsable.username)
        self.assertEqual(envio['estado_anterior_display'], 'Pendiente')

    def test_paginacion_orden_estable_y_registros_anteriores_accesibles(self):
        for numero in range(13):
            HistorialEstado.objects.create(asignacion=self.legada, estado_anterior='en_progreso', estado_nuevo='observada', usuario=self.revisor, comentario=f'Registro {numero}')
        HistorialEstado.objects.filter(asignacion=self.legada).update(fecha=timezone.now())
        ids = list(HistorialEstado.objects.filter(asignacion=self.legada).order_by('-pk').values_list('pk', flat=True))
        data = self.consultar(asignacion=self.legada, page_size=5)
        self.assertEqual(data['count'], 13)
        self.assertEqual(data['page_size'], 5)
        self.assertEqual([r['id'] for r in data['results']], ids[:5])
        ultima = self.consultar(asignacion=self.legada, page=3, page_size=5)
        self.assertEqual([r['id'] for r in ultima['results']], ids[10:])

    def test_revocacion_y_unidad_ajena_no_revelan_historial(self):
        HistorialEstado.objects.create(asignacion=self.asignacion, estado_nuevo='en_progreso', usuario=self.responsable, comentario='Dato interno')
        self.assertEqual(self.cliente(self.otro).get(f'/api/asignaciones/{self.asignacion.pk}/historial/').status_code, 404)
        self.assertEqual(self.consultar(self.revisor)['count'], 1)
        self.ambito.activo = False
        self.ambito.save()
        self.assertEqual(self.cliente(self.revisor).get(f'/api/asignaciones/{self.asignacion.pk}/historial/').status_code, 404)

    def test_consulta_historica_respetando_parejas_unidad_periodo(self):
        historica = Asignacion.objects.create(indicador_marco=self.marco, periodo=self.historico,
            unidad_responsable=self.unidad, encargado=self.responsable)
        HistorialEstado.objects.create(asignacion=historica, estado_nuevo='en_progreso', usuario=self.responsable)
        self.assertEqual(self.consultar(asignacion=historica, periodo=self.historico.pk)['count'], 1)
        AmbitoRevision.objects.create(usuario=self.revisor, unidad_organizacional=self.ajena, periodo=self.historico)
        self.assertEqual(self.cliente(self.revisor).get(f'/api/asignaciones/{historica.pk}/historial/', {'periodo': self.historico.pk}).status_code, 404)
        AmbitoRevision.objects.create(usuario=self.revisor, unidad_organizacional=self.unidad, periodo=self.historico)
        self.assertEqual(self.consultar(self.revisor, asignacion=historica, periodo=self.historico.pk)['count'], 1)

    def test_externo_sin_decisiones_internas_y_precedencia_de_roles_globales(self):
        self.asignacion.estado = 'aprobado'
        self.asignacion.save()
        HistorialEstado.objects.create(asignacion=self.asignacion, estado_nuevo='aprobado', usuario=self.revisor, comentario='Criterio de cierre interno')
        self.assertEqual(self.cliente(self.externo).get(f'/api/asignaciones/{self.asignacion.pk}/', {'periodo': self.periodo.pk}).status_code, 200)
        self.assertEqual(self.cliente(self.externo).get(f'/api/asignaciones/{self.asignacion.pk}/historial/', {'periodo': self.periodo.pk}).status_code, 403)
        self.coordinador.groups.add(Group.objects.get(name='Evaluador Externo'))
        self.assertEqual(self.consultar()['count'], 1)

    def test_no_inventa_creacion_y_no_ofrece_escritura_de_historial(self):
        self.assertEqual(self.consultar()['results'], [])
        self.assertEqual(self.cliente().post(f'/api/asignaciones/{self.asignacion.pk}/historial/', {'estado_nuevo': 'aprobado'}, format='json').status_code, 405)
        self.assertFalse(HistorialEstado.objects.exists())
        self.assertEqual(self.cliente().get(f'/api/asignaciones/{self.asignacion.pk}/historial/', {'periodo': 'texto'}).status_code, 400)

    def test_cuenta_eliminada_no_elimina_el_comentario_historico(self):
        registro = HistorialEstado.objects.create(asignacion=self.asignacion, estado_anterior=None,
            estado_nuevo='pendiente', usuario=self.colaborador, comentario='Registro conservado')
        self.colaborador.delete()
        data = self.consultar()['results'][0]
        self.assertEqual(data['id'], registro.pk)
        self.assertIsNone(data['usuario'])
        self.assertIsNone(data['usuario_identificador'])
        self.assertEqual(data['comentario'], 'Registro conservado')
