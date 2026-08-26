from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from evaluation.models import Asignacion, Criterio, Indicador, Periodo
from organization.models import Departamento, Facultad

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
    periodo = Periodo.objects.create(nombre="Periodo 2025", fecha_inicio="2025-01-01", fecha_fin="2025-12-31")
    criterio = Criterio.objects.create(nombre="Criterio Test", periodo=periodo)
    indicador = Indicador.objects.create(nombre="Indicador Test", criterio=criterio)
    return Asignacion.objects.create(indicador=indicador, departamento=departamento, periodo=periodo)


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
        self.assertEqual(str(obs), "Observación #1 - Versión 1")


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class EvidenciaViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.asignacion = _make_asignacion()

        self.admin_user = _make_user("admin", "admin@test.com", is_superuser=True)
        self.token = Token.objects.create(user=self.admin_user)

    def test_list_requires_auth(self):
        response = self.client.get("/api/evidencias/")
        self.assertEqual(response.status_code, 401)

    def test_create_evidencia(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.post(
            "/api/evidencias/",
            {"titulo": "Nueva Evidencia", "descripcion": "Descripción", "asignacion": self.asignacion.pk},
            format="json",
        )
        self.assertIn(response.status_code, [200, 201])
        self.assertTrue(Evidencia.objects.filter(titulo="Nueva Evidencia").exists())
