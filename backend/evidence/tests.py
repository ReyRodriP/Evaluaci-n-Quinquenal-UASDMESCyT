import csv
import io
import os
import tempfile
import zipfile
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auditoria.models import Auditoria
from evaluation.models import (
    Asignacion,
    Criterio,
    EstadoAsignacion,
    HistorialEstado,
    Indicador,
    Periodo,
)
from organization.models import (
    AmbitoEvaluacion,
    Departamento,
    Facultad,
    PerfilUsuario,
    TipoUnidadOrganizacional,
    UnidadOrganizacional,
)

from .models import EstadoEvidencia, Evidencia, Observacion, VersionEvidencia

User = get_user_model()


def _make_user(username, email, groups=None, is_superuser=False):
    if is_superuser:
        user = User.objects.create_superuser(username=username, email=email, password="testpass123")
    else:
        user = User.objects.create_user(username=username, email=email, password="testpass123")
    if groups:
        user.groups.add(*groups)
    return user


def _make_asignacion(departamento=None):
    facultad = Facultad.objects.create(nombre="Facultad Test")
    if not departamento:
        departamento = Departamento.objects.create(nombre="Depto Test", facultad=facultad)
    tipo, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Departamento")
    unidad = UnidadOrganizacional.objects.create(
        nombre=departamento.nombre,
        tipo=tipo,
        departamento_legacy=departamento,
    )
    hoy = timezone.localdate()
    periodo = Periodo.objects.create(
        nombre="Período de prueba",
        fecha_inicio=hoy - timedelta(days=1),
        fecha_fin=hoy + timedelta(days=30),
    )
    criterio = Criterio.objects.create(nombre="Criterio Test", periodo=periodo)
    indicador = Indicador.objects.create(nombre="Indicador Test", criterio=criterio)
    return Asignacion.objects.create(indicador=indicador, unidad_responsable=unidad, periodo=periodo)


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class EvidenciaModelTests(TestCase):
    def setUp(self):
        self.asignacion = _make_asignacion()

    def test_crear(self):
        evidencia = Evidencia.objects.create(
            titulo="Evidencia Test", descripcion="Descripción de prueba", asignacion=self.asignacion
        )
        self.assertIsNotNone(evidencia.id_evidencia)
        self.assertEqual(evidencia.titulo, "Evidencia Test")
        self.assertEqual(evidencia.asignacion, self.asignacion)

    def test_estado_default(self):
        evidencia = Evidencia.objects.create(titulo="Test", descripcion="Test", asignacion=self.asignacion)
        self.assertEqual(evidencia.estado, EstadoEvidencia.ACTIVA)

    def test_str(self):
        evidencia = Evidencia.objects.create(titulo="Mi Evidencia", descripcion="Test", asignacion=self.asignacion)
        self.assertEqual(str(evidencia), "Mi Evidencia")


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class VersionEvidenciaModelTests(TestCase):
    def setUp(self):
        self.asignacion = _make_asignacion()
        self.evidencia = Evidencia.objects.create(titulo="Evidencia V", descripcion="Test", asignacion=self.asignacion)

    def test_crear(self):
        version = VersionEvidencia.objects.create(
            evidencia=self.evidencia, archivo="evidencias/test.pdf", comentario="Primera versión"
        )
        self.assertIsNotNone(version.id_version)
        self.assertEqual(version.evidencia, self.evidencia)
        self.assertEqual(version.comentario, "Primera versión")

    def test_str(self):
        version = VersionEvidencia.objects.create(evidencia=self.evidencia, archivo="evidencias/test.pdf")
        self.assertEqual(str(version), "Evidencia V - v1")

    def test_version_default(self):
        version = VersionEvidencia.objects.create(evidencia=self.evidencia, archivo="evidencias/test.pdf")
        self.assertEqual(version.version, 1)


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class ObservacionModelTests(TestCase):
    def setUp(self):
        self.asignacion = _make_asignacion()
        self.evidencia = Evidencia.objects.create(titulo="Evidencia O", descripcion="Test", asignacion=self.asignacion)
        self.version = VersionEvidencia.objects.create(evidencia=self.evidencia, archivo="evidencias/test.pdf")
        self.user = _make_user("observador", "obs@test.com")

    def test_crear(self):
        obs = Observacion.objects.create(version=self.version, usuario=self.user, comentario="Observación de prueba")
        self.assertIsNotNone(obs.id)
        self.assertEqual(obs.comentario, "Observación de prueba")
        self.assertEqual(obs.usuario, self.user)

    def test_activo_default(self):
        obs = Observacion.objects.create(version=self.version, usuario=self.user, comentario="Test")
        self.assertTrue(obs.activo)

    def test_str(self):
        obs = Observacion.objects.create(version=self.version, usuario=self.user, comentario="Test")
        self.assertEqual(str(obs), f"Observación #{obs.id} - Versión 1")


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class EvidenciaViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.asignacion = _make_asignacion()
        self.media_temp = tempfile.TemporaryDirectory()
        media_override = override_settings(MEDIA_ROOT=self.media_temp.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.addCleanup(self.media_temp.cleanup)

        self.admin_user = _make_user("admin", "admin@test.com", is_superuser=True)
        self.token = RefreshToken.for_user(self.admin_user).access_token

    def test_bulk_download_builds_zip_and_manifest(self):
        evidencia = Evidencia.objects.create(
            titulo="Informe de investigación",
            descripcion="Documento aprobado",
            asignacion=self.asignacion,
        )
        version = VersionEvidencia.objects.create(
            evidencia=evidencia,
            archivo=SimpleUploadedFile("informe final.pdf", b"contenido pdf de prueba"),
            version=1,
        )
        self.addCleanup(version.archivo.delete, save=False)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.token))

        response = self.client.post(
            "/api/evidencias/descargas-masivas/",
            {"evidencias": [evidencia.pk, evidencia.pk]},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        archive = zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content)))
        names = archive.namelist()
        self.assertEqual(len([name for name in names if name.endswith(".pdf")]), 1)
        self.assertIn("manifest.csv", names)
        rows = list(csv.DictReader(io.StringIO(archive.read("manifest.csv").decode("utf-8-sig"))))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["evidencia_id"], str(evidencia.pk))
        self.assertEqual(rows[0]["version"], "1")
        self.assertTrue(
            Auditoria.objects.filter(
                usuario=self.admin_user,
                accion="Descarga masiva",
                registro_id__isnull=True,
            ).exists()
        )

    def test_bulk_download_rejects_unauthorized_ids_and_oversized_selection(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.token))
        unauthorized = self.client.post(
            "/api/evidencias/descargas-masivas/",
            {"evidencias": [self.asignacion.pk, 999999]},
            format="json",
        )
        too_many = self.client.post(
            "/api/evidencias/descargas-masivas/",
            {"evidencias": list(range(1, 102))},
            format="json",
        )

        self.assertEqual(unauthorized.status_code, 404)
        self.assertEqual(too_many.status_code, 413)

    def test_revisor_asignado_a_uasd_ve_evidencias_de_facultades_hijas(self):
        self.asignacion.estado = EstadoAsignacion.APROBADO
        self.asignacion.save()
        evidencia = Evidencia.objects.create(
            titulo="Evidencia universitaria aprobada",
            descripcion="Debe llegar al revisor de UASD",
            asignacion=self.asignacion,
        )

        universidad_tipo, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Universidad")
        facultad_tipo, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Facultad")
        universidad = UnidadOrganizacional.objects.create(nombre="UASD", tipo=universidad_tipo)
        facultad = UnidadOrganizacional.objects.create(
            nombre=self.asignacion.unidad_responsable.departamento_legacy.facultad.nombre,
            tipo=facultad_tipo,
            unidad_padre=universidad,
        )
        self.asignacion.unidad_responsable.unidad_padre = facultad
        self.asignacion.unidad_responsable.save(update_fields=["unidad_padre"])

        revisor = _make_user("revisor_uasd", "revisor_uasd@test.com")
        grupo, _ = Group.objects.get_or_create(name="Revisor Institucional")
        revisor.groups.add(grupo)
        revisor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label__in=["evidence", "organization"],
                codename__in=["view_evidencia", "view_facultad"],
            )
        )
        PerfilUsuario.objects.create(usuario=revisor, unidad_organizacional=universidad)
        self.client.force_authenticate(user=revisor)

        evidencias = self.client.get("/api/evidencias/")
        facultades = self.client.get("/api/facultades/")

        self.assertEqual(evidencias.status_code, 200)
        self.assertEqual([row["id_evidencia"] for row in evidencias.data["results"]], [evidencia.pk])
        self.assertEqual(facultades.status_code, 200)
        self.assertIn(
            self.asignacion.unidad_responsable.departamento_legacy.facultad.pk,
            [row["id"] for row in facultades.data["results"]],
        )

    def test_list_requires_auth(self):
        response = self.client.get("/api/evidencias/")
        self.assertEqual(response.status_code, 401)

    def test_create_evidencia(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.token))
        response = self.client.post(
            "/api/evidencias/",
            {"titulo": "Nueva Evidencia", "descripcion": "Descripción", "asignacion": self.asignacion.pk},
            format="json",
        )
        self.assertIn(response.status_code, [200, 201])
        self.assertTrue(Evidencia.objects.filter(titulo="Nueva Evidencia").exists())

    def test_create_evidencia_for_inactive_period_denied(self):
        self.asignacion.periodo.activo = False
        self.asignacion.periodo.save()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.token))
        response = self.client.post(
            "/api/evidencias/",
            {
                "titulo": "Fuera de período",
                "descripcion": "No debe guardarse",
                "asignacion": self.asignacion.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Evidencia.objects.filter(titulo="Fuera de período").exists())

    def test_historical_evidence_is_readable_but_cannot_receive_version(self):
        evidencia = Evidencia.objects.create(
            titulo="Histórica",
            descripcion="Consulta histórica",
            asignacion=self.asignacion,
        )
        self.asignacion.periodo.activo = False
        self.asignacion.periodo.save()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.token))

        listado = self.client.get(f"/api/evidencias/?periodo={self.asignacion.periodo_id}")
        detalle = self.client.get(
            f"/api/evidencias/{evidencia.pk}/detalle/?periodo={self.asignacion.periodo_id}"
        )
        subir = self.client.post(f"/api/evidencias/{evidencia.pk}/subir_version/")

        self.assertEqual(listado.status_code, 200)
        self.assertEqual(len(listado.data["results"]), 1)
        self.assertEqual(detalle.status_code, 200)
        self.assertFalse(detalle.data["puede_subir_version"])
        self.assertEqual(subir.status_code, 400)

    def test_external_evaluator_sees_only_approved_evidence_in_assigned_scope(self):
        self.asignacion.estado = EstadoAsignacion.APROBADO
        self.asignacion.save()
        evidencia_aprobada = Evidencia.objects.create(
            titulo="Aprobada autorizada",
            descripcion="Dentro del alcance",
            asignacion=self.asignacion,
        )

        indicador_pendiente = Indicador.objects.create(
            nombre="Indicador pendiente",
            criterio=self.asignacion.indicador.criterio,
        )
        asignacion_pendiente = Asignacion.objects.create(
            indicador=indicador_pendiente,
            unidad_responsable=self.asignacion.unidad_responsable,
            periodo=self.asignacion.periodo,
            estado=EstadoAsignacion.PENDIENTE,
        )
        evidencia_pendiente = Evidencia.objects.create(
            titulo="Pendiente",
            descripcion="No visible",
            asignacion=asignacion_pendiente,
        )

        tipo = TipoUnidadOrganizacional.objects.get_or_create(nombre="Unidad externa test")[0]
        unidad_no_autorizada = UnidadOrganizacional.objects.create(nombre="Otra unidad", tipo=tipo)
        asignacion_otra_unidad = Asignacion.objects.create(
            indicador=self.asignacion.indicador,
            unidad_responsable=unidad_no_autorizada,
            periodo=self.asignacion.periodo,
            estado=EstadoAsignacion.APROBADO,
        )
        evidencia_otra_unidad = Evidencia.objects.create(
            titulo="Otra unidad",
            descripcion="No visible",
            asignacion=asignacion_otra_unidad,
        )

        periodo_no_autorizado = Periodo.objects.create(
            nombre="Segundo período autorizado",
            fecha_inicio=timezone.localdate() - timedelta(days=400),
            fecha_fin=timezone.localdate() - timedelta(days=30),
            activo=False,
        )
        criterio = Criterio.objects.create(nombre="Criterio histórico", periodo=periodo_no_autorizado)
        indicador = Indicador.objects.create(nombre="Indicador histórico", criterio=criterio)
        asignacion_otro_periodo = Asignacion.objects.create(
            indicador=indicador,
            unidad_responsable=self.asignacion.unidad_responsable,
            periodo=periodo_no_autorizado,
            estado=EstadoAsignacion.APROBADO,
        )
        evidencia_otro_periodo = Evidencia.objects.create(
            titulo="Otro período",
            descripcion="No visible",
            asignacion=asignacion_otro_periodo,
        )
        asignacion_segundo_ambito = Asignacion.objects.create(
            indicador=indicador,
            unidad_responsable=unidad_no_autorizada,
            periodo=periodo_no_autorizado,
            estado=EstadoAsignacion.APROBADO,
        )
        evidencia_segundo_ambito = Evidencia.objects.create(
            titulo="Segundo ámbito autorizado",
            descripcion="Visible por su ámbito propio",
            asignacion=asignacion_segundo_ambito,
        )
        version_antigua = VersionEvidencia.objects.create(
            evidencia=evidencia_aprobada,
            archivo="evidencias/aprobada-antigua.pdf",
            version=1,
        )
        version_autorizada = VersionEvidencia.objects.create(
            evidencia=evidencia_aprobada,
            archivo="evidencias/aprobada.pdf",
            version=2,
        )
        version_segundo_ambito = VersionEvidencia.objects.create(
            evidencia=evidencia_segundo_ambito,
            archivo="evidencias/segundo-ambito.pdf",
        )
        VersionEvidencia.objects.create(evidencia=evidencia_pendiente, archivo="evidencias/pendiente.pdf")
        VersionEvidencia.objects.create(evidencia=evidencia_otra_unidad, archivo="evidencias/otra-unidad.pdf")
        VersionEvidencia.objects.create(evidencia=evidencia_otro_periodo, archivo="evidencias/otro-periodo.pdf")

        evaluador = _make_user("evaluador_externo", "evaluador@test.com")
        grupo, _ = Group.objects.get_or_create(name="Evaluador Externo")
        evaluador.groups.add(grupo)
        evaluador.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label__in=["evidence", "evaluation"],
                codename__in=["view_evidencia", "view_versionevidencia", "view_observacion", "view_asignacion", "view_periodo"],
            )
        )
        perfil = PerfilUsuario.objects.create(
            usuario=evaluador,
            unidad_organizacional=self.asignacion.unidad_responsable,
        )
        AmbitoEvaluacion.objects.create(
            usuario=evaluador,
            unidad_organizacional=self.asignacion.unidad_responsable,
            periodo=self.asignacion.periodo,
        )
        AmbitoEvaluacion.objects.create(
            usuario=evaluador,
            unidad_organizacional=unidad_no_autorizada,
            periodo=periodo_no_autorizado,
        )
        Observacion.objects.create(
            version=version_autorizada,
            usuario=self.admin_user,
            comentario="Nota interna no visible al evaluador.",
        )
        self.client.force_authenticate(user=evaluador)

        response = self.client.get("/api/evidencias/")
        denied_detail = self.client.get(f"/api/evidencias/{evidencia_pendiente.pk}/detalle/?periodo={self.asignacion.periodo_id}")
        periods = self.client.get("/api/periodos/")
        dashboard_advance = self.client.get("/api/dashboard/avance/")
        versions = self.client.get("/api/versiones/")
        assignments = self.client.get("/api/asignaciones/")
        criteria = self.client.get("/api/criterios/")
        indicators = self.client.get("/api/indicadores/")
        detail = self.client.get(f"/api/evidencias/{evidencia_aprobada.pk}/detalle/?periodo={self.asignacion.periodo_id}")
        old_version = self.client.get(f"/api/versiones/{version_antigua.pk}/")
        observations = self.client.get("/api/observaciones/")
        bulk_denied = self.client.post(
            "/api/evidencias/descargas-masivas/",
            {"evidencias": [evidencia_aprobada.pk, evidencia_pendiente.pk]},
            format="json",
        )
        bulk_allowed = self.client.post(
            "/api/evidencias/descargas-masivas/",
            {"evidencias": [evidencia_aprobada.pk]},
            format="json",
        )
        create_observation = self.client.post(
            "/api/observaciones/",
            {"version": version_autorizada.pk, "comentario": "No autorizado"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["id_evidencia"] for row in response.data["results"]},
            {evidencia_aprobada.pk, evidencia_segundo_ambito.pk},
        )
        self.assertEqual(denied_detail.status_code, 404)
        self.assertEqual(dashboard_advance.status_code, 200)
        self.assertEqual(
            {row["id"] for row in periods.data["results"]},
            {self.asignacion.periodo_id, periodo_no_autorizado.pk},
        )
        self.assertEqual(
            {row["id_version"] for row in versions.data["results"]},
            {version_autorizada.pk, version_segundo_ambito.pk},
        )
        self.assertEqual(
            {row["id"] for row in assignments.data["results"]},
            {self.asignacion.pk, asignacion_segundo_ambito.pk},
        )
        indicadores_visibles = {row["id"] for row in indicators.data["results"]}
        self.assertEqual(
            indicadores_visibles,
            {self.asignacion.indicador_id, indicador.pk},
        )
        indicadores_anidados = {
            indicador_anidado["id"]
            for criterio_visible in criteria.data["results"]
            for indicador_anidado in criterio_visible["indicadores"]
        }
        self.assertEqual(indicadores_anidados, indicadores_visibles)
        self.assertEqual(len(detail.data["versiones"]), 1)
        self.assertEqual(detail.data["versiones"][0]["observaciones"], [])
        self.assertIsNone(detail.data["ultima_observacion"])
        self.assertEqual(detail.data["historial_estados"], [])
        self.assertEqual(old_version.status_code, 404)
        self.assertEqual(observations.data["results"], [])
        self.assertEqual(create_observation.status_code, 403)
        self.assertEqual(bulk_denied.status_code, 404)
        self.assertEqual(bulk_allowed.status_code, 200)
        bulk_zip = zipfile.ZipFile(io.BytesIO(b"".join(bulk_allowed.streaming_content)))
        self.assertIn("manifest.csv", bulk_zip.namelist())
        self.assertIn("errors.csv", bulk_zip.namelist())


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class SubirVersionValidacionTests(TestCase):
    """Pruebas de validación de archivos en todas las rutas de subida/edición."""

    def setUp(self):
        self.client = APIClient()
        self.asignacion = _make_asignacion()
        self.evidencia = Evidencia.objects.create(
            titulo="Evidencia Validación",
            descripcion="Para pruebas de validación",
            asignacion=self.asignacion,
        )
        self.media_temp = tempfile.TemporaryDirectory()
        media_override = override_settings(MEDIA_ROOT=self.media_temp.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.addCleanup(self.media_temp.cleanup)

        self.admin_user = _make_user("admin_val", "admin_val@test.com", is_superuser=True)
        self.token = RefreshToken.for_user(self.admin_user).access_token
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.token))

    def _archivos_en_media(self):
        with os.scandir(self.media_temp.name) as entries:
            return [e.name for e in entries]

    def _ultima_version_payload(self, response):
        """@brief Extrae el payload de una respuesta DRF valida"""
        return response.data

    def test_subir_version_valida_crea_version_y_cambia_estado(self):
        archivo = SimpleUploadedFile("informe.pdf", b"%PDF-1.4 contenido", content_type="application/pdf")
        response = self.client.post(
            f"/api/evidencias/{self.evidencia.pk}/subir_version/",
            {"archivo": archivo, "comentario": "Carga válida"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(VersionEvidencia.objects.filter(evidencia=self.evidencia).count(), 1)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.EN_PROGRESO)
        self.assertTrue(HistorialEstado.objects.filter(asignacion=self.asignacion).exists())

    def test_subir_version_extension_invalida_rechaza(self):
        archivo = SimpleUploadedFile("malware.exe", b"MZ", content_type="application/octet-stream")
        response = self.client.post(
            f"/api/evidencias/{self.evidencia.pk}/subir_version/",
            {"archivo": archivo},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(VersionEvidencia.objects.filter(evidencia=self.evidencia).count(), 0)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.PENDIENTE)
        self.assertFalse(HistorialEstado.objects.filter(asignacion=self.asignacion).exists())
        self.assertEqual(self._archivos_en_media(), [])

    def test_subir_version_archivo_vacio_rechaza(self):
        archivo = SimpleUploadedFile("vacio.pdf", b"", content_type="application/pdf")
        response = self.client.post(
            f"/api/evidencias/{self.evidencia.pk}/subir_version/",
            {"archivo": archivo},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(VersionEvidencia.objects.filter(evidencia=self.evidencia).count(), 0)
        self.assertEqual(self._archivos_en_media(), [])

    def test_subir_version_tamano_excesivo_rechaza(self):
        archivo = SimpleUploadedFile("grande.pdf", b"X" * 1024, content_type="application/pdf")
        with mock.patch("evidence.validators.MAX_FILE_SIZE_BYTES", 10):
            response = self.client.post(
                f"/api/evidencias/{self.evidencia.pk}/subir_version/",
                {"archivo": archivo},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(VersionEvidencia.objects.filter(evidencia=self.evidencia).count(), 0)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.PENDIENTE)
        self.assertEqual(self._archivos_en_media(), [])

    def test_subir_version_content_type_invalido_rechaza(self):
        archivo = SimpleUploadedFile("doc.pdf", b"contenido", content_type="application/x-msdownload")
        response = self.client.post(
            f"/api/evidencias/{self.evidencia.pk}/subir_version/",
            {"archivo": archivo},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(VersionEvidencia.objects.filter(evidencia=self.evidencia).count(), 0)
        self.assertEqual(self._archivos_en_media(), [])

    def test_editar_version_valida_aplica_cambios(self):
        archivo = SimpleUploadedFile("original.pdf", b"contenido original", content_type="application/pdf")
        version = VersionEvidencia.objects.create(
            evidencia=self.evidencia, archivo=archivo, version=1, subido_por=self.admin_user
        )
        nuevo = SimpleUploadedFile("editado.pdf", b"contenido editado", content_type="application/pdf")

        response = self.client.patch(
            f"/api/evidencias/{self.evidencia.pk}/editar_version/",
            {"archivo": nuevo, "comentario": "Comentario actualizado"},
        )

        self.assertEqual(response.status_code, 200)
        version.refresh_from_db()
        self.assertEqual(version.comentario, "Comentario actualizado")
        self.assertIn("editado", version.archivo.name)

    def test_editar_version_archivo_invalido_rechaza(self):
        archivo = SimpleUploadedFile("original.pdf", b"contenido original", content_type="application/pdf")
        version = VersionEvidencia.objects.create(
            evidencia=self.evidencia, archivo=archivo, version=1, subido_por=self.admin_user
        )
        malicioso = SimpleUploadedFile("malware.exe", b"MZ", content_type="application/octet-stream")

        response = self.client.patch(
            f"/api/evidencias/{self.evidencia.pk}/editar_version/",
            {"archivo": malicioso},
        )

        self.assertEqual(response.status_code, 400)
        version.refresh_from_db()
        self.assertIn("original", version.archivo.name)
        self.assertNotIn("malware", version.archivo.name)


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class ObservacionEstadoTests(TestCase):
    """Pruebas de la máquina de estados en la creación de observaciones."""

    def setUp(self):
        self.client = APIClient()
        self.asignacion = _make_asignacion()
        self.evidencia = Evidencia.objects.create(
            titulo="Evidencia Estado",
            descripcion="Para pruebas de estado",
            asignacion=self.asignacion,
        )
        self.version = VersionEvidencia.objects.create(
            evidencia=self.evidencia,
            archivo=SimpleUploadedFile("v1.pdf", b"contenido", content_type="application/pdf"),
            version=1,
        )
        self.admin_user = _make_user("admin_est", "admin_est@test.com", is_superuser=True)
        self.token = RefreshToken.for_user(self.admin_user).access_token
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.token))

    def _post_observacion(self):
        return self.client.post(
            "/api/observaciones/",
            {"version": self.version.pk, "comentario": "Observación de prueba"},
            format="json",
        )

    def test_observacion_sobre_aprobada_rechaza_y_no_efectos(self):
        self.asignacion.estado = EstadoAsignacion.APROBADO
        self.asignacion.save()
        auditorias_previas = Auditoria.objects.count()

        response = self._post_observacion()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Observacion.objects.filter(version=self.version).count(), 0)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.APROBADO)
        self.assertFalse(HistorialEstado.objects.filter(asignacion=self.asignacion).exists())
        self.assertEqual(Auditoria.objects.count(), auditorias_previas)

    def test_observacion_sobre_en_progreso_cambia_estado(self):
        self.asignacion.estado = EstadoAsignacion.EN_PROGRESO
        self.asignacion.save()

        response = self._post_observacion()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Observacion.objects.filter(version=self.version).count(), 1)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.OBSERVADA)
        historial = HistorialEstado.objects.get(asignacion=self.asignacion)
        self.assertEqual(historial.estado_anterior, EstadoAsignacion.EN_PROGRESO)
        self.assertEqual(historial.estado_nuevo, EstadoAsignacion.OBSERVADA)

    def test_observacion_sobre_rechazada_rechaza(self):
        self.asignacion.estado = EstadoAsignacion.RECHAZADO
        self.asignacion.save()

        response = self._post_observacion()

        self.assertEqual(response.status_code, 400)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.RECHAZADO)

    def test_observacion_sobre_observada_admite_adicionales_sin_duplicar_historial(self):
        self.asignacion.estado = EstadoAsignacion.OBSERVADA
        self.asignacion.save()

        response = self._post_observacion()

        self.assertEqual(response.status_code, 201)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.OBSERVADA)
        self.assertEqual(HistorialEstado.objects.filter(asignacion=self.asignacion).count(), 0)

    def test_observacion_sobre_pendiente_cambia_estado(self):
        self.asignacion.estado = EstadoAsignacion.PENDIENTE
        self.asignacion.save()

        response = self._post_observacion()

        self.assertEqual(response.status_code, 201)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.OBSERVADA)

    def test_atomicidad_fallo_auditoria_no_deja_efectos_parciales(self):
        self.asignacion.estado = EstadoAsignacion.EN_PROGRESO
        self.asignacion.save()

        with mock.patch(
            "evidence.views.registrar_auditoria", side_effect=RuntimeError("fallo simulado")
        ):
            with self.assertRaises(RuntimeError):
                self._post_observacion()

        self.assertEqual(Observacion.objects.filter(version=self.version).count(), 0)
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, EstadoAsignacion.EN_PROGRESO)
        self.assertFalse(HistorialEstado.objects.filter(asignacion=self.asignacion).exists())

    def test_detalle_puede_observar_refleja_maquina(self):
        self.asignacion.estado = EstadoAsignacion.APROBADO
        self.asignacion.save()
        detalle_aprobado = self.client.get(f"/api/evidencias/{self.evidencia.pk}/detalle/")

        self.asignacion.estado = EstadoAsignacion.EN_PROGRESO
        self.asignacion.save()
        detalle_en_progreso = self.client.get(f"/api/evidencias/{self.evidencia.pk}/detalle/")

        self.assertFalse(detalle_aprobado.data["puede_observar"])
        self.assertTrue(detalle_en_progreso.data["puede_observar"])
