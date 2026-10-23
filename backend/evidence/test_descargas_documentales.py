"""Descarga mixta: versiones actuales, IDs independientes y alcance completo del lote."""
import csv
import io
import tempfile
import zipfile
from pathlib import PurePosixPath
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from auditoria.models import Auditoria
from evidence.models import Evidencia, VersionDocumento, VersionEvidencia
from evidence.test_documentos import EscenarioDocumental


@override_settings(AMBITOS_REVISION_EXPLICITOS=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DescargasDocumentalesTests(EscenarioDocumental, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_escenario()

    def setUp(self):
        self.preparar()

    def descargar(self, usuario=None, **seleccion):
        return self.cliente(usuario).post('/api/evidencias/descargas-masivas/', seleccion, format='json')

    def archivo_zip(self, response):
        self.assertEqual(response.status_code, 200, getattr(response, 'data', ''))
        return zipfile.ZipFile(io.BytesIO(b''.join(response.streaming_content)))

    def manifest(self, archive):
        return list(csv.DictReader(io.StringIO(archive.read('manifest.csv').decode('utf-8-sig'))))

    def test_dos_documentos_incluyen_solo_sus_ultimas_versiones(self):
        a, b = self.solicitar(), self.solicitar('Documento B')
        for pk in (a, a, b):
            self.assertEqual(self.subir(pk).status_code, 201)
        with self.archivo_zip(self.descargar(solicitudes=[a, b, a])) as archive:
            filas = self.manifest(archive)
            self.assertEqual(len(filas), 2)
            self.assertEqual({(r['solicitud_id'], r['version']) for r in filas}, {(str(a), '2'), (str(b), '1')})
            self.assertTrue(all(r['tipo_recurso'] == 'documento' and r['resultado'] == 'INCLUIDO' for r in filas))
            for fila in filas:
                version = VersionDocumento.objects.get(pk=fila['version_id'])
                self.assertEqual(version.solicitud_id, int(fila['solicitud_id']))
                self.assertTrue(archive.read(fila['archivo']).startswith(b'%PDF'))
                self.assertNotIn('..', PurePosixPath(fila['archivo']).parts)
                self.assertFalse(fila['archivo'].startswith('/'))

    def test_ids_coincidentes_no_mezclan_evidencia_y_documento(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        evidencia = Evidencia.objects.create(id_evidencia=pk, asignacion=self.legada, titulo='Anterior', descripcion='Conservar')
        VersionEvidencia.objects.create(evidencia=evidencia, version=1, archivo=SimpleUploadedFile('anterior.pdf', b'archivo anterior'))
        with self.archivo_zip(self.descargar(evidencias=[pk], solicitudes=[pk])) as archive:
            filas = self.manifest(archive)
            self.assertEqual([r['tipo_recurso'] for r in filas], ['evidencia', 'documento'])
            self.assertEqual(filas[0]['evidencia_id'], str(pk))
            self.assertEqual(filas[0]['solicitud_id'], '')
            self.assertEqual(filas[1]['solicitud_id'], str(pk))
            self.assertEqual(filas[1]['evidencia_id'], '')
            self.assertEqual(archive.read(filas[0]['archivo']), b'archivo anterior')
            self.assertNotEqual(filas[0]['archivo'], filas[1]['archivo'])
        auditoria = Auditoria.objects.get(accion='Descarga masiva')
        self.assertIn(f'solicitudes: {pk}', auditoria.descripcion)

    def test_revisor_y_responsable_no_descargan_fuera_de_su_ambito(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        self.assertEqual(self.descargar(self.otro, solicitudes=[pk]).status_code, 404)
        self.assertEqual(self.descargar(self.revisor, solicitudes=[pk, 999999]).status_code, 404)
        with self.archivo_zip(self.descargar(self.revisor, solicitudes=[pk])) as archive:
            self.assertEqual(len(self.manifest(archive)), 1)
        self.ambito.activo = False
        self.ambito.save()
        self.assertEqual(self.descargar(self.revisor, solicitudes=[pk]).status_code, 404)

    def test_externo_solo_descarga_asignacion_aprobada_y_version_actual(self):
        pk = self.solicitar()
        for _ in range(2):
            self.assertEqual(self.subir(pk).status_code, 201)
        self.assertEqual(self.descargar(self.externo, solicitudes=[pk]).status_code, 404)
        self.enviar(pk)
        self.assertEqual(self.revisar(pk).status_code, 200)
        self.assertEqual(self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/').status_code, 200)
        with self.archivo_zip(self.descargar(self.externo, solicitudes=[pk])) as archive:
            filas = self.manifest(archive)
            self.assertEqual(len(filas), 1)
            self.assertEqual(filas[0]['version'], '2')
            self.assertNotIn('observaciones', ','.join(archive.namelist()))

    def test_limites_de_seleccion_y_bytes_son_comunes_a_ambos_flujos(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        self.assertEqual(self.descargar(evidencias=list(range(1, 101)), solicitudes=[pk]).status_code, 413)
        with patch('evidence.views.MAX_TAMANO_DESCARGA', 8):
            self.assertEqual(self.descargar(solicitudes=[pk]).status_code, 413)
            with patch('django.core.files.storage.filesystem.FileSystemStorage.size', return_value=0):
                self.assertEqual(self.descargar(solicitudes=[pk]).status_code, 413)
        self.assertFalse(Auditoria.objects.filter(accion='Descarga masiva').exists())

    def test_ausencias_de_archivo_se_informan_y_no_modifican_las_solicitudes(self):
        a, b = self.solicitar('=SUM(1,1)'), self.solicitar('Documento B')
        self.assertEqual(self.subir(b).status_code, 201)
        version = VersionDocumento.objects.get(solicitud_id=b)
        version.archivo.storage.delete(version.archivo.name)
        with self.archivo_zip(self.descargar(solicitudes=[a, b])) as archive:
            filas = self.manifest(archive)
            self.assertEqual({r['resultado'] for r in filas}, {'SIN_ARCHIVO', 'ERROR_ARCHIVO'})
            self.assertTrue(next(r for r in filas if r['solicitud_id'] == str(a))['titulo_documento'].startswith("'="))
            errores = list(csv.DictReader(io.StringIO(archive.read('errors.csv').decode('utf-8-sig'))))
            self.assertEqual({r['solicitud_id'] for r in errores}, {str(a), str(b)})
        self.assertEqual(self.asignacion.solicitudes_documentales.count(), 2)
        self.assertEqual(VersionDocumento.objects.get(pk=version.pk).archivo.name, version.archivo.name)

    def test_selecciones_invalidas_y_periodo_incompatible_se_rechazan(self):
        for seleccion in ({}, {'solicitudes': []}, {'solicitudes': [True]}, {'solicitudes': [1.5]}, {'solicitudes': ['-1']}, {'evidencias': '1'}):
            self.assertEqual(self.descargar(**seleccion).status_code, 400)
        self.assertEqual(self.cliente().post('/api/evidencias/descargas-masivas/', [], format='json').status_code, 400)
        pk = self.solicitar()
        response = self.cliente().post(f'/api/evidencias/descargas-masivas/?periodo={self.historico.pk}', {'solicitudes': [pk]}, format='json')
        self.assertEqual(response.status_code, 404)
        response = self.cliente().post('/api/evidencias/descargas-masivas/?periodo=texto', {'solicitudes': [pk]}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_fallo_de_auditoria_cierra_los_buffers(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        original = tempfile.SpooledTemporaryFile
        buffers = []

        def temporal(*args, **kwargs):
            archivo = original(*args, **kwargs)
            buffers.append(archivo)
            return archivo

        with patch('evidence.descargas.tempfile.SpooledTemporaryFile', side_effect=temporal), patch('evidence.descargas.registrar_auditoria', side_effect=RuntimeError('fallo simulado')), self.assertRaises(RuntimeError):
            self.descargar(solicitudes=[pk])
        self.assertTrue(buffers)
        self.assertTrue(all(archivo.closed for archivo in buffers))
