from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from evaluation.models import Asignacion, Criterio, EstadoAsignacion, Indicador, Periodo
from organization.models import Departamento, Facultad

User = get_user_model()


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class ReportesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/reportes/general/"
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

    def test_reporte_general_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_reporte_general_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn("periodo", data)
        self.assertIn("total_departamentos", data)
        self.assertIn("total_indicadores", data)
        self.assertIn("total_asignaciones", data)
        self.assertIn("pendientes", data)
        self.assertIn("aprobadas", data)
