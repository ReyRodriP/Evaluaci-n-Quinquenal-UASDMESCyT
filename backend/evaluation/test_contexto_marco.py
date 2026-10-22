"""Opciones de alta del marco y revalidación de las condiciones al crear."""
from django.test import TestCase, override_settings

from evaluation.models import Asignacion, Indicador
from evaluation.test_asignaciones_marco import EscenarioMarco
from organization.models import PerfilUsuario


@override_settings(AMBITOS_REVISION_EXPLICITOS=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ContextoMarcoTests(EscenarioMarco, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_escenario()

    def consultar(self, usuario=None, **params):
        return self.cliente(usuario).get('/api/asignaciones/contexto-marco/', {'periodo': self.periodo.pk, **params})

    def test_version_explicita_inactiva_y_catalogo_sin_crear_datos(self):
        antes = (Asignacion.objects.count(), Indicador.objects.count())
        response = self.consultar()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['version']['id'], self.version.pk)
        self.assertFalse(response.data['version']['activo'])
        self.assertEqual({i['id'] for i in response.data['indicadores']}, {self.marco.pk, self.marco_hermano.pk, self.marco_otra_dimension.pk})
        self.assertTrue(response.data['indicadores'][0]['ruta']['indicador']['codigo_sintetico'])
        self.assertEqual((Asignacion.objects.count(), Indicador.objects.count()), antes)

    def test_solo_usuarios_activos_autorizados_de_la_unidad(self):
        PerfilUsuario.objects.create(usuario=self.externo, unidad_organizacional=self.unidad)
        self.colaborador.is_active = False
        self.colaborador.save(update_fields=['is_active'])
        response = self.consultar(unidad=self.unidad.pk)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([u['id'] for u in response.data['encargados']], [self.responsable.pk])
        unidad = next(u for u in response.data['unidades'] if u['id'] == self.unidad.pk)
        self.assertIn(self.raiz.nombre, unidad['ruta'])
        self.assertIn(self.unidad.nombre, unidad['ruta'])

    def test_contexto_reservado_a_roles_globales_con_permiso_de_alta(self):
        for usuario in (self.responsable, self.revisor, self.externo):
            response = self.consultar(usuario)
            self.assertEqual(response.status_code, 403, response.data)

    def test_periodo_sin_version_finalizado_y_parametros_invalidos(self):
        self.periodo.version_marco = None
        self.periodo.save()
        response = self.consultar()
        self.assertEqual(response.status_code, 400)
        self.assertIn('version_marco', response.data)
        self.assertEqual(self.consultar(periodo=self.historico.pk).status_code, 400)
        self.assertEqual(self.consultar(periodo='texto').status_code, 400)
        self.assertEqual(self.consultar(unidad='-1').status_code, 400)

    def test_excluye_indicadores_inactivos_y_ancestros_incoherentes(self):
        self.marco_hermano.activo = False
        self.marco_hermano.save()
        self.assertNotIn(self.marco_hermano.pk, [i['id'] for i in self.consultar().data['indicadores']])
        self.marco.estandar.criterio_marco = self.marco_b.estandar.criterio_marco
        self.marco.estandar.save()
        self.assertNotIn(self.marco.pk, [i['id'] for i in self.consultar().data['indicadores']])

    def test_creacion_desde_contexto_y_acceso_a_gestion_documental(self):
        response = self.consultar(unidad=self.unidad.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['asignaciones_existentes'], [])
        payload = {'periodo': response.data['periodo']['id'], 'indicador_marco': self.marco.pk,
            'unidad_responsable': self.unidad.pk, 'encargado': self.responsable.pk}
        response = self.cliente().post('/api/asignaciones/', payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        pk = response.data['id']
        self.assertEqual(response.data['estado'], 'pendiente')
        self.assertIsNone(response.data['indicador'])
        self.assertEqual(self.consultar(unidad=self.unidad.pk).data['asignaciones_existentes'], [{'id': pk, 'indicador_marco': self.marco.pk}])
        contexto = self.cliente().get('/api/solicitudes-documentales/contexto/', {'asignacion': pk})
        self.assertTrue(contexto.data['puede_definir'])
        self.assertEqual(self.cliente().post('/api/asignaciones/', payload, format='json').status_code, 400)

    def test_guardado_revalida_responsable_despues_de_consultar(self):
        self.assertIn(self.responsable.pk, [u['id'] for u in self.consultar(unidad=self.unidad.pk).data['encargados']])
        self.responsable.is_active = False
        self.responsable.save(update_fields=['is_active'])
        response = self.cliente().post('/api/asignaciones/', self.payload(), format='json')
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Asignacion.objects.filter(indicador_marco=self.marco).exists())
