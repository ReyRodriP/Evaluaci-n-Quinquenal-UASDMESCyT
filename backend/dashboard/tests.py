from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from evaluation.models import Asignacion, Criterio, EstadoAsignacion, Indicador, Periodo
from organization.models import Departamento, Facultad

User = get_user_model()


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class DashboardResumenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/dashboard/resumen/"
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )
        self.group = Group.objects.create(name="Administrador General")
        self.admin_user.groups.add(self.group)

        self.facultad = Facultad.objects.create(nombre="Facultad Ciencias")
        self.departamento = Departamento.objects.create(
            nombre="Depto Matematicas",
            facultad=self.facultad,
        )
        self.periodo = Periodo.objects.create(
            nombre="Periodo 2025",
            fecha_inicio="2025-01-01",
            fecha_fin="2025-12-31",
        )
        self.criterio = Criterio.objects.create(
            nombre="Criterio 1",
            periodo=self.periodo,
        )
        self.indicador = Indicador.objects.create(
            nombre="Indicador 1",
            criterio=self.criterio,
            obligatorio=True,
        )
        self.asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            departamento=self.departamento,
            periodo=self.periodo,
            estado=EstadoAsignacion.PENDIENTE,
        )

    def test_resumen_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_resumen_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_resumen_returns_expected_keys(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data
        expected_keys = {
            "departamentos",
            "indicadores",
            "asignaciones",
            "pendientes",
            "en_progreso",
            "observadas",
            "aprobadas",
            "rechazadas",
        }
        self.assertEqual(set(data.keys()), expected_keys)
        self.assertEqual(data["departamentos"], 1)
        self.assertEqual(data["indicadores"], 1)
        self.assertEqual(data["asignaciones"], 1)
        self.assertEqual(data["pendientes"], 1)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class DashboardDepartamentoTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.group = Group.objects.create(name="Administrador General")
        self.user.groups.add(self.group)

        self.facultad = Facultad.objects.create(nombre="Facultad Ciencias")
        self.departamento = Departamento.objects.create(
            nombre="Depto Matematicas",
            facultad=self.facultad,
        )

    def test_departamento_requires_auth(self):
        url = f"/api/dashboard/departamento/{self.departamento.pk}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_departamento_not_found(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/dashboard/departamento/99999/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class DashboardAvanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.group = Group.objects.create(name="Administrador General")
        self.user.groups.add(self.group)

        self.facultad = Facultad.objects.create(nombre="Facultad Ciencias")
        self.departamento = Departamento.objects.create(
            nombre="Depto Matematicas",
            facultad=self.facultad,
        )

    def test_avance_requires_auth(self):
        response = self.client.get("/api/dashboard/avance/")
        self.assertEqual(response.status_code, 401)

    def test_avance_returns_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/dashboard/avance/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
