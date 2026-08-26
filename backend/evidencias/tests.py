from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from evaluation.models import Asignacion, Criterio, Indicador, Periodo
from organization.models import Departamento, Facultad

from .models import Evidencia

User = get_user_model()


def _make_asignacion():
    facultad = Facultad.objects.create(nombre="Facultad Test")
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
        self.user = User.objects.create_user(username="uploader", email="up@test.com", password="testpass123")
        self.asignacion = _make_asignacion()

    def test_crear(self):
        evidencia = Evidencia.objects.create(
            asignacion=self.asignacion,
            archivo="evidencias/test.pdf",
            nombre="Documento Test",
            tipo_archivo="application/pdf",
            tamano=1024,
            subido_por=self.user,
            descripcion="Un documento de prueba",
        )
        self.assertIsNotNone(evidencia.pk)
        self.assertEqual(evidencia.nombre, "Documento Test")
        self.assertEqual(evidencia.subido_por, self.user)

    def test_str(self):
        evidencia = Evidencia.objects.create(
            asignacion=self.asignacion,
            archivo="evidencias/test.pdf",
            nombre="Mi Archivo",
            tipo_archivo="application/pdf",
            tamano=2048,
            subido_por=self.user,
        )
        self.assertEqual(str(evidencia), "Mi Archivo")

    def test_version_default(self):
        evidencia = Evidencia.objects.create(
            asignacion=self.asignacion,
            archivo="evidencias/test.pdf",
            nombre="Doc",
            tipo_archivo="application/pdf",
            tamano=512,
            subido_por=self.user,
        )
        self.assertEqual(evidencia.version, 1)


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class EvidenciaViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="viewer", email="view@test.com", password="testpass123")
        self.token = Token.objects.create(user=self.user)

    def test_list_requires_auth(self):
        response = self.client.get("/api/evidencias/")
        self.assertEqual(response.status_code, 401)
