"""Regresiones del flujo documental sin reclasificar entregas históricas."""
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings

from evaluation.models import Asignacion
from evaluation.test_asignaciones_marco import EscenarioMarco
from evidence.models import Evidencia, RevisionDocumento, SolicitudDocumental, VersionDocumento


class EscenarioDocumental(EscenarioMarco):
    def preparar(self):
        self.media = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=self.media))
        self.asignacion = Asignacion.objects.create(indicador_marco=self.marco, periodo=self.periodo,
            unidad_responsable=self.unidad, encargado=self.responsable)

    def solicitar(self, titulo='Documento A'):
        r = self.cliente().post('/api/solicitudes-documentales/', {
            'asignacion': self.asignacion.pk, 'titulo': titulo, 'descripcion': 'Requisito técnico de prueba.'}, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        return r.data['id']

    def subir(self, pk, usuario=None):
        return self.cliente(usuario or self.responsable).post(f'/api/solicitudes-documentales/{pk}/subir_version/',
            {'archivo': SimpleUploadedFile('prueba.pdf', b'%PDF-1.4\nDocumento de prueba\n%%EOF', content_type='application/pdf')}, format='multipart')

    def enviar(self, pk):
        r = self.cliente(self.responsable).post(f'/api/solicitudes-documentales/{pk}/enviar/')
        self.assertEqual(r.status_code, 200, r.data)

    def revisar(self, pk, accion='aprobar', comentario='', version=None):
        version = version or VersionDocumento.objects.filter(solicitud_id=pk).first().pk
        return self.cliente(self.revisor).post(f'/api/solicitudes-documentales/{pk}/{accion}/',
            {'version_id': version, 'comentario': comentario}, format='json')

    def aprobar_documento(self, pk):
        self.assertEqual(self.subir(pk).status_code, 201)
        self.enviar(pk)
        r = self.revisar(pk)
        self.assertEqual(r.status_code, 200, r.data)


@override_settings(AMBITOS_REVISION_EXPLICITOS=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DocumentosTests(EscenarioDocumental, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_escenario()

    def setUp(self):
        self.preparar()

    def test_solo_administracion_y_coordinacion_definen_solicitudes(self):
        for usuario in (self.responsable, self.revisor, self.externo):
            r = self.cliente(usuario).post('/api/solicitudes-documentales/', {
                'asignacion': self.asignacion.pk, 'titulo': 'No permitido', 'descripcion': 'Prueba'}, format='json')
            self.assertEqual(r.status_code, 403, r.data)
        self.solicitar()
        self.asignacion.refresh_from_db()
        self.assertTrue(self.asignacion.gestion_documental)

    def test_dos_documentos_correccion_independiente_y_cierre_explicito(self):
        a, b = self.solicitar(), self.solicitar('Documento B')
        self.aprobar_documento(a)
        self.assertEqual(self.subir(b).status_code, 201)
        self.enviar(b)
        self.assertEqual(self.revisar(b, 'solicitar_cambios', 'Corregir la fecha').status_code, 200)
        self.assertEqual(self.subir(b, self.colaborador).status_code, 201)
        self.enviar(b)
        self.assertEqual(self.revisar(b).status_code, 200)
        self.assertEqual(list(VersionDocumento.objects.filter(solicitud_id=a).values_list('numero', flat=True)), [1])
        self.assertEqual(list(VersionDocumento.objects.filter(solicitud_id=b).values_list('numero', flat=True)), [2, 1])
        self.assertEqual(RevisionDocumento.objects.filter(version__solicitud_id=b).count(), 2)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, 'en_progreso')
        r = self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/')
        self.assertEqual(r.status_code, 200, r.data)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, 'aprobado')
        self.assertEqual(self.subir(b).status_code, 400)

    def test_cierre_bloqueado_y_sin_actualizacion_alternativa(self):
        self.solicitar()
        for estado in ('aprobado', 'completado', 'en_progreso'):
            r = self.cliente().patch(f'/api/asignaciones/{self.asignacion.pk}/', {'estado': estado}, format='json')
            self.assertEqual(r.status_code, 400, r.data)
        r = self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/')
        self.assertEqual(r.status_code, 400)
        self.asignacion.refresh_from_db()
        self.asignacion.estado = 'aprobado'
        with self.assertRaises(ValidationError):
            self.asignacion.save()

    def test_no_se_puede_cerrar_con_otra_solicitud_pendiente(self):
        a = self.solicitar()
        self.solicitar('Documento B')
        self.aprobar_documento(a)
        self.assertEqual(self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/').status_code, 400)

    def test_se_conserva_definicion_y_archivos_una_vez_entregado(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        for metodo in ('patch', 'delete'):
            r = getattr(self.cliente(), metodo)(f'/api/solicitudes-documentales/{pk}/', {'titulo': 'Cambio'}, format='json')
            self.assertEqual(r.status_code, 400, r.data)
        self.enviar(pk)
        self.assertEqual(self.subir(pk).status_code, 400)
        self.assertEqual(self.revisar(pk, version=999999).status_code, 400)
        self.assertEqual(self.revisar(pk, 'solicitar_cambios').status_code, 400)

    def test_edicion_previa_y_cero_solicitudes_no_autorizan_cierre(self):
        pk = self.solicitar()
        self.assertEqual(self.cliente().patch(f'/api/solicitudes-documentales/{pk}/', {'titulo': 'Definitivo'}, format='json').status_code, 200)
        self.assertEqual(self.cliente().delete(f'/api/solicitudes-documentales/{pk}/').status_code, 204)
        self.assertEqual(self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/').status_code, 400)
        self.asignacion.refresh_from_db()
        self.assertTrue(self.asignacion.gestion_documental)

    def test_ambitos_listado_y_revocacion(self):
        pk = self.solicitar()
        self.assertEqual(self.cliente(self.otro).get(f'/api/solicitudes-documentales/{pk}/').status_code, 404)
        self.assertEqual(self.subir(pk, self.otro).status_code, 404)
        self.assertEqual(self.cliente(self.revisor).get(f'/api/solicitudes-documentales/{pk}/').status_code, 200)
        self.ambito.activo = False
        self.ambito.save()
        self.assertEqual(self.cliente(self.revisor).get(f'/api/solicitudes-documentales/{pk}/').status_code, 404)
        self.assertEqual(self.cliente(self.revisor).get(f'/api/solicitudes-documentales/contexto/?asignacion={self.asignacion.pk}').status_code, 404)

    def test_historico_no_admite_nuevas_operaciones(self):
        pk = self.solicitar()
        self.periodo.activo = False
        self.periodo.save()
        self.assertEqual(self.subir(pk).status_code, 400)
        self.assertEqual(self.cliente(self.responsable).get(f'/api/solicitudes-documentales/{pk}/').status_code, 200)

    def test_no_reclasifica_entregas_existentes_ni_asignaciones_operativas(self):
        evidencia = Evidencia.objects.create(asignacion=self.asignacion, titulo='Histórica', descripcion='Conservar')
        r = self.cliente().post('/api/solicitudes-documentales/', {'asignacion': self.asignacion.pk, 'titulo': 'Nueva', 'descripcion': 'Prueba'}, format='json')
        self.assertEqual(r.status_code, 400)
        evidencia.refresh_from_db()
        self.assertEqual(evidencia.titulo, 'Histórica')
        r = self.cliente().post('/api/solicitudes-documentales/', {'asignacion': self.legada.pk, 'titulo': 'Nueva', 'descripcion': 'Prueba'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_no_admite_evidencia_unica_en_flujo_documental(self):
        self.solicitar()
        r = self.cliente(self.responsable).post('/api/evidencias/', {'asignacion': self.asignacion.pk, 'titulo': 'Bypass', 'descripcion': 'Prueba'}, format='json')
        self.assertEqual(r.status_code, 400)
        for accion in ('en_revision', 'observada', 'rechazar'):
            self.assertEqual(self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/{accion}/').status_code, 400)

    def test_descarga_autorizada_e_historial_inmutable(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        v = VersionDocumento.objects.get(solicitud_id=pk)
        self.assertEqual(self.cliente(self.otro).get(f'/api/solicitudes-documentales/{pk}/descargar/?version={v.pk}').status_code, 404)
        r = self.cliente(self.responsable).get(f'/api/solicitudes-documentales/{pk}/descargar/?version={v.pk}')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(b''.join(r.streaming_content).startswith(b'%PDF'))
        self.assertEqual(self.cliente().patch(f'/api/solicitudes-documentales/{pk}/subir_version/', {}).status_code, 405)

    def test_auditoria_fallida_revierte_version_y_archivo(self):
        pk = self.solicitar()
        with patch('evidence.documentos.registrar_auditoria', side_effect=RuntimeError('fallo simulado')), self.assertRaises(RuntimeError):
            self.subir(pk)
        self.assertFalse(VersionDocumento.objects.exists())
        self.assertEqual(list(Path(self.media).rglob('*.pdf')), [])
        self.assertEqual(SolicitudDocumental.objects.get(pk=pk).estado, 'pendiente')

    def test_externo_solo_consulta_cierre_aprobado_y_ultima_version(self):
        pk = self.solicitar()
        self.assertEqual(self.cliente(self.externo).get(f'/api/solicitudes-documentales/{pk}/').status_code, 404)
        self.assertEqual(self.subir(pk).status_code, 201)
        self.assertEqual(self.subir(pk).status_code, 201)
        self.enviar(pk)
        self.assertEqual(self.revisar(pk).status_code, 200)
        self.assertEqual(self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/').status_code, 200)
        r = self.cliente(self.externo).get(f'/api/solicitudes-documentales/{pk}/')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual([v['numero'] for v in r.data['versiones']], [2])
        self.assertEqual(r.data['versiones'][0]['revisiones'], [])
        anterior = VersionDocumento.objects.get(solicitud_id=pk, numero=1)
        self.assertEqual(self.cliente(self.externo).get(f'/api/solicitudes-documentales/{pk}/descargar/?version={anterior.pk}').status_code, 404)

    def test_documentos_no_duplican_cobertura_y_aparecen_en_reporte(self):
        from dashboard.views import _metricas_asignaciones

        a, b = self.solicitar(), self.solicitar('Documento B')
        for pk in (a, b):
            self.assertEqual(self.subir(pk).status_code, 201)
        metricas = _metricas_asignaciones(Asignacion.objects.filter(pk=self.asignacion.pk))
        self.assertEqual(metricas['asignaciones'], 1)
        self.assertEqual(metricas['evidencias'], 1)
        r = self.cliente().get('/api/reportes/evidencias/', {'periodo': self.periodo.pk})
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual({row['evidencia'] for row in r.data['rows']}, {'Documento A', 'Documento B'})

    def test_no_traslada_ni_desactiva_flujo_desde_payload(self):
        self.solicitar()
        self.assertEqual(self.cliente().delete(f'/api/asignaciones/{self.asignacion.pk}/').status_code, 400)
        r = self.cliente().patch(f'/api/asignaciones/{self.asignacion.pk}/', {'unidad_responsable': self.ajena.pk}, format='json')
        self.assertEqual(r.status_code, 400)
        r = self.cliente().patch(f'/api/asignaciones/{self.asignacion.pk}/', {'gestion_documental': False}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.asignacion.refresh_from_db()
        self.assertTrue(self.asignacion.gestion_documental)


@override_settings(AMBITOS_REVISION_EXPLICITOS=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ConcurrenciaDocumentalTests(EscenarioDocumental, TransactionTestCase):
    def setUp(self):
        self.crear_escenario()
        self.preparar()

    def test_cargas_concurrentes_numeran_por_documento(self):
        pk = self.solicitar()

        def cargar(_):
            close_old_connections()
            try:
                return self.subir(pk).status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(cargar, range(2))), [201, 201])
        self.assertEqual(list(VersionDocumento.objects.filter(solicitud_id=pk).values_list('numero', flat=True)), [2, 1])

    def test_cierre_frente_a_nuevo_requisito_no_omite_documentos(self):
        pk = self.solicitar()
        self.aprobar_documento(pk)

        def operar(accion):
            close_old_connections()
            try:
                if accion == 'cerrar':
                    return self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/').status_code
                return self.cliente().post('/api/solicitudes-documentales/', {
                    'asignacion': self.asignacion.pk, 'titulo': 'Nuevo requisito', 'descripcion': 'También obligatorio'}, format='json').status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            cerrar, crear = list(pool.map(operar, ['cerrar', 'crear']))
        self.assertIn((cerrar, crear), [(200, 400), (400, 201)])
        self.asignacion.refresh_from_db()
        if self.asignacion.estado == 'aprobado':
            self.assertFalse(self.asignacion.solicitudes_documentales.exclude(estado='aprobada').exists())
