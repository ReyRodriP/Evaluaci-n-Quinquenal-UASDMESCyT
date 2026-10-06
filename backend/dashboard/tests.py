from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from evidence.models import Evidencia
from evaluation.models import Asignacion, Criterio, EstadoAsignacion, Indicador, Periodo
from organization.models import Departamento, Facultad, PerfilUsuario, TipoUnidadOrganizacional, UnidadOrganizacional

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
            "periodo",
            "departamentos",
            "unidades",
            "indicadores",
            "asignaciones",
            "evidencias",
            "sin_evidencia",
            "cobertura_porcentaje",
            "cumplimiento_porcentaje",
            "pendientes",
            "en_progreso",
            "observadas",
            "aprobadas",
            "rechazadas",
            "completadas",
        }
        self.assertEqual(set(data.keys()), expected_keys)
        self.assertEqual(data["departamentos"], 1)
        self.assertEqual(data["unidades"], 1)
        self.assertEqual(data["indicadores"], 1)
        self.assertEqual(data["asignaciones"], 1)
        self.assertEqual(data["evidencias"], 0)
        self.assertEqual(data["sin_evidencia"], 1)
        self.assertEqual(data["cobertura_porcentaje"], 0)
        self.assertEqual(data["cumplimiento_porcentaje"], 0)
        self.assertEqual(data["evidencias"], 0)
        self.assertEqual(data["sin_evidencia"], 1)
        self.assertEqual(data["cobertura_porcentaje"], 0)
        self.assertEqual(data["cumplimiento_porcentaje"], 0)
        self.assertEqual(data["pendientes"], 1)

    def test_resumen_separa_cobertura_de_cumplimiento(self):
        Evidencia.objects.create(
            titulo="Evidencia cargada",
            descripcion="Aún está pendiente de aprobación",
            asignacion=self.asignacion,
        )
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["evidencias"], 1)
        self.assertEqual(response.data["cobertura_porcentaje"], 100)
        self.assertEqual(response.data["aprobadas"], 0)
        self.assertEqual(response.data["cumplimiento_porcentaje"], 0)

    def test_dashboard_unit_filter_includes_descendants_and_state(self):
        tipo_facultad, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Facultad")
        unidad_facultad = UnidadOrganizacional.objects.create(
            nombre="Unidad raíz de prueba",
            tipo=tipo_facultad,
        )
        self.unidad.unidad_padre = unidad_facultad
        self.unidad.save(update_fields=["unidad_padre"])
        Evidencia.objects.create(
            titulo="Evidencia bajo el departamento",
            descripcion="Cobertura del descendiente",
            asignacion=self.asignacion,
        )
        unidad_sin_asignaciones = UnidadOrganizacional.objects.create(
            nombre="Otra unidad",
            tipo=tipo_facultad,
        )
        periodo_extra = Periodo.objects.create(
            nombre="Período no consultado",
            fecha_inicio=timezone.localdate() - timedelta(days=400),
            fecha_fin=timezone.localdate() - timedelta(days=30),
            activo=False,
        )
        criterio_extra = Criterio.objects.create(nombre="Otro criterio", periodo=periodo_extra)
        indicador_extra = Indicador.objects.create(nombre="Otro indicador", criterio=criterio_extra)
        Asignacion.objects.create(
            indicador=indicador_extra,
            unidad_responsable=unidad_sin_asignaciones,
            periodo=periodo_extra,
            estado=EstadoAsignacion.APROBADO,
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            self.url,
            {"unidad": unidad_facultad.pk, "estado": EstadoAsignacion.PENDIENTE},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["asignaciones"], 1)
        self.assertEqual(response.data["evidencias"], 1)
        self.assertEqual(response.data["cobertura_porcentaje"], 100)
        self.assertEqual(response.data["cumplimiento_porcentaje"], 0)

    def test_resumen_can_select_historical_period(self):
        periodo_historico = Periodo.objects.create(
            nombre="Periodo anterior",
            fecha_inicio=timezone.localdate() - timedelta(days=400),
            fecha_fin=timezone.localdate() - timedelta(days=30),
            activo=False,
        )
        criterio_historico = Criterio.objects.create(nombre="Criterio anterior", periodo=periodo_historico)
        indicador_historico = Indicador.objects.create(
            nombre="Indicador anterior",
            criterio=criterio_historico,
            obligatorio=True,
        )
        Asignacion.objects.create(
            indicador=indicador_historico,
            unidad_responsable=self.unidad,
            periodo=periodo_historico,
            estado=EstadoAsignacion.APROBADO,
        )

        self.client.force_authenticate(user=self.admin_user)
        activo = self.client.get(self.url)
        historico = self.client.get(self.url, {"periodo": periodo_historico.pk})

        self.assertEqual(activo.data["periodo"]["id"], self.periodo.pk)
        self.assertEqual(activo.data["asignaciones"], 1)
        self.assertEqual(historico.data["periodo"]["id"], periodo_historico.pk)
        self.assertEqual(historico.data["asignaciones"], 1)
        self.assertEqual(historico.data["aprobadas"], 1)

    def test_revisor_dashboard_y_pendientes_respetan_su_unidad(self):
        self.asignacion.estado = EstadoAsignacion.EN_PROGRESO
        self.asignacion.save(update_fields=["estado"])
        otra_facultad = Facultad.objects.create(nombre="Facultad Fuera de ámbito")
        otro_departamento = Departamento.objects.create(nombre="Otro departamento", facultad=otra_facultad)
        otra_unidad = UnidadOrganizacional.objects.create(
            nombre=otro_departamento.nombre,
            tipo=self.unidad.tipo,
            departamento_legacy=otro_departamento,
        )
        otro_criterio = Criterio.objects.create(nombre="Criterio externo", periodo=self.periodo)
        otro_indicador = Indicador.objects.create(nombre="Indicador externo", criterio=otro_criterio)
        asignacion_fuera = Asignacion.objects.create(
            indicador=otro_indicador,
            unidad_responsable=otra_unidad,
            periodo=self.periodo,
            estado=EstadoAsignacion.EN_PROGRESO,
        )

        revisor = User.objects.create_user(
            username="revisor_dashboard",
            email="revisor_dashboard@example.com",
            password="revisorpass123",
        )
        revisor.groups.add(Group.objects.create(name="Revisor Institucional"))
        PerfilUsuario.objects.create(usuario=revisor, unidad_organizacional=self.unidad)
        self.client.force_authenticate(user=revisor)

        resumen = self.client.get(self.url)
        pendientes = self.client.get("/api/dashboard/pendientes/")

        self.assertEqual(resumen.status_code, 200)
        self.assertEqual(resumen.data["asignaciones"], 1)
        self.assertEqual(resumen.data["unidades"], 1)
        self.assertEqual(pendientes.status_code, 200)
        self.assertEqual([row["asignacion_id"] for row in pendientes.data], [self.asignacion.pk])
        self.assertNotIn(asignacion_fuera.pk, [row["asignacion_id"] for row in pendientes.data])


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
