"""Destinatarios y destinos documentales actuales; avisos atómicos y SMTP tras commit."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from evidence.models import SolicitudDocumental, VersionDocumento
from evidence.test_documentos import EscenarioDocumental
from notificaciones.documentales import avisar_solicitud
from notificaciones.models import DestinoNotificacionDocumental, Notificacion
from organization.models import AmbitoRevision


@override_settings(AMBITOS_REVISION_EXPLICITOS=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AvisosDocumentalesTests(EscenarioDocumental, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.crear_escenario()

    def setUp(self):
        self.preparar()

    def listar(self, usuario):
        response = self.cliente(usuario).get('/api/notificaciones/')
        self.assertEqual(response.status_code, 200, response.data)
        return response.data['results']

    def revisor_adicional(self, nombre, unidad=None, activo=True):
        usuario = get_user_model().objects.create_user(username=nombre, email=f'{nombre}@example.test', is_active=activo)
        usuario.groups.add(Group.objects.get(name='Revisor Institucional'))
        if unidad:
            AmbitoRevision.objects.create(usuario=usuario, unidad_organizacional=unidad, periodo=self.periodo)
        return usuario

    def test_solicitud_avisa_al_encargado_con_destino_y_propiedad_privada(self):
        pk = self.solicitar()
        aviso = Notificacion.objects.get(titulo='Nueva solicitud documental')
        self.assertEqual(aviso.usuario_id, self.responsable.pk)
        destino = self.listar(self.responsable)[0]['destino']
        self.assertEqual(destino, {'asignacion_id': self.asignacion.pk, 'periodo_id': self.periodo.pk, 'solicitud_id': pk, 'version_id': None})
        self.assertEqual(self.cliente(self.otro).patch(f'/api/notificaciones/{aviso.pk}/leer/').status_code, 404)
        response = self.cliente(self.responsable).patch(f'/api/notificaciones/{aviso.pk}/leer/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['leida'])
        self.assertEqual(response.data['destino'], destino)

    def test_envio_avisa_solo_a_revisores_autorizados_y_no_a_coordinacion(self):
        dentro = self.revisor_adicional('rev_dentro', self.raiz)
        fuera = self.revisor_adicional('rev_fuera', self.ajena)
        sin_ambito = self.revisor_adicional('rev_sin_ambito')
        inactivo = self.revisor_adicional('rev_inactivo', self.raiz, activo=False)
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        self.assertFalse(Notificacion.objects.filter(titulo='Documento enviado a revisión').exists())
        self.enviar(pk)
        avisos = Notificacion.objects.filter(titulo='Documento enviado a revisión')
        self.assertEqual(set(avisos.values_list('usuario_id', flat=True)), {self.revisor.pk, dentro.pk})
        self.assertFalse(avisos.filter(usuario_id__in=[self.coordinador.pk, fuera.pk, sin_ambito.pk, inactivo.pk]).exists())
        version = VersionDocumento.objects.get(solicitud_id=pk)
        self.assertTrue(all(a.destino_documental.version_id == version.pk for a in avisos))
        self.assertEqual(self.cliente(self.responsable).post(f'/api/solicitudes-documentales/{pk}/enviar/').status_code, 400)
        self.assertEqual(avisos.count(), 2)

    def test_envio_sin_revisores_no_bloquea_ni_envia_avisos_a_roles_globales(self):
        self.ambito.activo = False
        self.ambito.save()
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        self.enviar(pk)
        self.assertFalse(Notificacion.objects.filter(titulo='Documento enviado a revisión').exists())

    def test_correccion_notifica_la_nueva_version_y_revision_no_duplica_encargado_autor(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        self.enviar(pk)
        self.assertEqual(self.revisar(pk, 'solicitar_cambios', 'Corregir fecha').status_code, 200)
        avisos = Notificacion.objects.filter(titulo='Documento revisado')
        self.assertEqual(avisos.count(), 1)
        self.assertEqual(avisos.get().usuario_id, self.responsable.pk)
        self.assertEqual(self.subir(pk).status_code, 201)
        self.enviar(pk)
        destinos = DestinoNotificacionDocumental.objects.filter(notificacion__titulo='Documento enviado a revisión', notificacion__usuario=self.revisor)
        self.assertEqual(set(destinos.values_list('version__numero', flat=True)), {1, 2})

    def test_revision_avisa_al_colaborador_y_encargado_solo_si_conservan_acceso(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk, self.colaborador).status_code, 201)
        self.enviar(pk)
        self.assertEqual(self.revisar(pk, 'solicitar_cambios', 'Completar contenido').status_code, 200)
        self.assertEqual(set(Notificacion.objects.filter(titulo='Documento revisado').values_list('usuario_id', flat=True)), {self.responsable.pk, self.colaborador.pk})
        perfil = self.responsable.perfilusuario
        perfil.unidad_organizacional = self.ajena
        perfil.save()
        self.assertEqual(self.subir(pk, self.colaborador).status_code, 201)
        response = self.cliente(self.colaborador).post(f'/api/solicitudes-documentales/{pk}/enviar/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.revisar(pk).status_code, 200)
        self.assertEqual(Notificacion.objects.filter(titulo='Documento revisado', usuario=self.responsable).count(), 1)
        self.assertEqual(Notificacion.objects.filter(titulo='Documento revisado', usuario=self.colaborador).count(), 2)

    def test_revocacion_oculta_avisos_y_no_marca_invisibles_como_leidos(self):
        pk = self.solicitar()
        self.assertEqual(self.subir(pk).status_code, 201)
        self.enviar(pk)
        aviso = Notificacion.objects.get(usuario=self.revisor, titulo='Documento enviado a revisión')
        anterior = Notificacion.objects.create(usuario=self.revisor, titulo='Anterior', mensaje='Aviso personal anterior')
        self.assertEqual(len(self.listar(self.revisor)), 2)
        self.ambito.activo = False
        self.ambito.save()
        self.assertEqual([a['id'] for a in self.listar(self.revisor)], [anterior.pk])
        self.assertEqual(self.cliente(self.revisor).patch(f'/api/notificaciones/{aviso.pk}/leer/').status_code, 404)
        response = self.cliente(self.revisor).post('/api/notificaciones/marcar_todas/')
        self.assertEqual(response.data['actualizadas'], 1)
        aviso.refresh_from_db()
        self.assertFalse(aviso.leida)

    def test_solicitud_editada_no_duplica_si_no_cambia_y_retirada_abre_asignacion(self):
        pk = self.solicitar()
        for _ in range(2):
            response = self.cliente().patch(f'/api/solicitudes-documentales/{pk}/', {'titulo': 'Definitivo'}, format='json')
            self.assertEqual(response.status_code, 200)
        self.assertEqual(Notificacion.objects.filter(titulo='Solicitud documental actualizada').count(), 1)
        self.assertEqual(self.cliente().delete(f'/api/solicitudes-documentales/{pk}/').status_code, 204)
        avisos = self.listar(self.responsable)
        self.assertEqual(len(avisos), 3)
        self.assertTrue(all(a['destino']['solicitud_id'] is None and a['destino']['asignacion_id'] == self.asignacion.pk for a in avisos))

    def test_cierre_global_tiene_aviso_diferente_de_aprobacion_documental(self):
        pk = self.solicitar()
        self.aprobar_documento(pk)
        self.assertFalse(Notificacion.objects.filter(titulo='Asignación aprobada globalmente').exists())
        response = self.cliente(self.revisor).post(f'/api/asignaciones/{self.asignacion.pk}/aprobar/', {'comentario': 'Cierre confirmado'}, format='json')
        self.assertEqual(response.status_code, 200)
        aviso = Notificacion.objects.get(titulo='Asignación aprobada globalmente')
        self.assertEqual(aviso.usuario_id, self.responsable.pk)
        self.assertIsNone(aviso.destino_documental.solicitud_id)
        self.assertIn('Cierre confirmado', aviso.mensaje)
        self.assertFalse(Notificacion.objects.filter(titulo='Evidencia aprobada con comentarios').exists())

    @override_settings(NOTIFICACIONES_EMAIL_ENABLED=True)
    def test_correo_documental_se_entrega_despues_del_commit(self):
        with patch('notificaciones.documentales.enviar_correo_notificacion') as correo:
            with self.captureOnCommitCallbacks(execute=True):
                self.solicitar()
                correo.assert_not_called()
            self.assertEqual(correo.call_count, 1)
            correo.reset_mock()
            correo.side_effect = RuntimeError('fallo simulado de entrega después del commit')
            with self.assertLogs(level='ERROR'), self.captureOnCommitCallbacks(execute=True):
                self.solicitar('Documento B')
            self.assertEqual(Notificacion.objects.filter(titulo='Nueva solicitud documental').count(), 2)
            self.assertEqual(SolicitudDocumental.objects.count(), 2)

    @override_settings(NOTIFICACIONES_EMAIL_ENABLED=True)
    def test_rollback_descarta_aviso_destino_y_correo(self):
        def fallar(*args, **kwargs):
            avisar_solicitud(*args, **kwargs)
            raise RuntimeError('fallo simulado después de preparar el aviso')

        with patch('notificaciones.documentales.enviar_correo_notificacion') as correo, self.captureOnCommitCallbacks(execute=True), patch('evidence.documentos.avisar_solicitud', side_effect=fallar), self.assertRaises(RuntimeError):
            self.solicitar()
        correo.assert_not_called()
        self.assertFalse(Notificacion.objects.exists())
        self.assertFalse(DestinoNotificacionDocumental.objects.exists())
        self.assertFalse(SolicitudDocumental.objects.exists())

    @override_settings(NOTIFICACIONES_EMAIL_ENABLED=True)
    def test_correo_revalida_acceso_al_ejecutarse_el_callback(self):
        with patch('notificaciones.documentales.enviar_correo_notificacion') as correo:
            with self.captureOnCommitCallbacks(execute=True):
                self.solicitar()
                perfil = self.responsable.perfilusuario
                perfil.unidad_organizacional = self.ajena
                perfil.save()
            correo.assert_not_called()
        self.assertEqual(self.listar(self.responsable), [])

    def test_destinos_no_admiten_versiones_de_otra_solicitud(self):
        a, b = self.solicitar(), self.solicitar('Documento B')
        self.assertEqual(self.subir(b).status_code, 201)
        aviso = Notificacion.objects.create(usuario=self.responsable, titulo='Prueba', mensaje='Destino incoherente')
        destino = DestinoNotificacionDocumental(notificacion=aviso, asignacion=self.asignacion,
            solicitud_id=a, version=VersionDocumento.objects.get(solicitud_id=b))
        with self.assertRaises(ValidationError):
            destino.full_clean()
