from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from evaluation.models import Asignacion, Criterio, EstadoAsignacion, Indicador, Periodo
from organization.models import Departamento, Facultad, TipoUnidadOrganizacional, UnidadOrganizacional

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
        tipo, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Departamento")
        self.unidad = UnidadOrganizacional.objects.create(
            nombre=self.departamento.nombre,
            tipo=tipo,
            departamento_legacy=self.departamento,
        )
        self.periodo = Periodo.objects.create(
            nombre="Periodo 2025",
            fecha_inicio=timezone.localdate() - timedelta(days=1),
            fecha_fin=timezone.localdate() + timedelta(days=30),
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
            unidad_responsable=self.unidad,
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

    def test_reporte_general_active_default_and_historical_selection(self):
        periodo_historico = Periodo.objects.create(
            nombre="Periodo histórico",
            fecha_inicio=timezone.localdate() - timedelta(days=400),
            fecha_fin=timezone.localdate() - timedelta(days=30),
            activo=False,
        )
        criterio = Criterio.objects.create(nombre="Criterio histórico", periodo=periodo_historico)
        indicador = Indicador.objects.create(nombre="Indicador histórico", criterio=criterio, obligatorio=True)
        Asignacion.objects.create(
            indicador=indicador,
            unidad_responsable=self.unidad,
            periodo=periodo_historico,
            estado=EstadoAsignacion.APROBADO,
        )
        self.client.force_authenticate(user=self.admin_user)

        activo = self.client.get(self.url)
        historico = self.client.get(self.url, {"periodo": periodo_historico.pk})

        self.assertEqual(activo.data["periodo"], self.periodo.nombre)
        self.assertEqual(activo.data["total_asignaciones"], 1)
        self.assertEqual(historico.data["periodo"], periodo_historico.nombre)
        self.assertEqual(historico.data["total_asignaciones"], 1)
        self.assertEqual(historico.data["aprobadas"], 1)
