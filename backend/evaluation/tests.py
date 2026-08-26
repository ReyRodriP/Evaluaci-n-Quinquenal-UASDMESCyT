from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from organization.models import Departamento, Facultad

from .models import (
    Asignacion,
    Criterio,
    EstadoAsignacion,
    HistorialEstado,
    Indicador,
    Periodo,
)

User = get_user_model()


# ===========================================================================
# 1. PeriodoModelTests
# ===========================================================================
class PeriodoModelTests(TestCase):
    def test_crear_periodo(self):
        periodo = Periodo.objects.create(
            nombre="Evaluacion 2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )
        self.assertEqual(periodo.nombre, "Evaluacion 2026")
        self.assertEqual(periodo.fecha_inicio, date(2026, 1, 1))
        self.assertEqual(periodo.fecha_fin, date(2026, 12, 31))

    def test_str_representation(self):
        periodo = Periodo.objects.create(
            nombre="Periodo Test",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )
        self.assertEqual(str(periodo), "Periodo Test")

    def test_periodo_default_activo(self):
        periodo = Periodo.objects.create(
            nombre="SinActivo",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )
        self.assertTrue(periodo.activo)


# ===========================================================================
# 2. CriterioModelTests
# ===========================================================================
class CriterioModelTests(TestCase):
    def setUp(self):
        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )

    def test_crear_criterio(self):
        criterio = Criterio.objects.create(
            nombre="Calidad",
            descripcion="Criterio de calidad",
        )
        self.assertEqual(criterio.nombre, "Calidad")
        self.assertTrue(criterio.activo)

    def test_criterio_con_periodo(self):
        criterio = Criterio.objects.create(
            nombre="Pertinencia",
            descripcion="Criterio pertinente",
            periodo=self.periodo,
        )
        self.assertEqual(criterio.periodo, self.periodo)
        self.assertIn(criterio, self.periodo.criterios.all())

    def test_str_representation(self):
        criterio = Criterio.objects.create(
            nombre="Impacto",
            periodo=self.periodo,
        )
        self.assertEqual(str(criterio), "Impacto")


# ===========================================================================
# 3. IndicadorModelTests
# ===========================================================================
class IndicadorModelTests(TestCase):
    def setUp(self):
        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )
        self.criterio = Criterio.objects.create(
            nombre="C1",
            periodo=self.periodo,
        )

    def test_crear_indicador(self):
        indicador = Indicador.objects.create(
            nombre="Ind-A",
            descripcion="Desc",
            criterio=self.criterio,
        )
        self.assertEqual(indicador.nombre, "Ind-A")
        self.assertEqual(indicador.criterio, self.criterio)
        self.assertTrue(indicador.activo)

    def test_indicador_obligatorio_default(self):
        indicador = Indicador.objects.create(
            nombre="Ind-B",
            criterio=self.criterio,
        )
        self.assertFalse(indicador.obligatorio)

    def test_str_representation(self):
        indicador = Indicador.objects.create(
            nombre="Ind-Test",
            criterio=self.criterio,
        )
        self.assertEqual(str(indicador), "Ind-Test")


# ===========================================================================
# 4. AsignacionModelTests
# ===========================================================================
class AsignacionModelTests(TestCase):
    def setUp(self):
        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )
        self.criterio = Criterio.objects.create(
            nombre="C1",
            periodo=self.periodo,
        )
        self.indicador = Indicador.objects.create(
            nombre="I1",
            criterio=self.criterio,
        )
        self.facultad = Facultad.objects.create(nombre="Facultad X")
        self.departamento = Departamento.objects.create(
            nombre="Depto Y",
            facultad=self.facultad,
        )

    def test_crear_asignacion(self):
        asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            departamento=self.departamento,
            periodo=self.periodo,
        )
        self.assertEqual(asignacion.indicador, self.indicador)
        self.assertEqual(asignacion.departamento, self.departamento)
        self.assertEqual(asignacion.periodo, self.periodo)

    def test_asignacion_estado_default(self):
        asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            departamento=self.departamento,
            periodo=self.periodo,
        )
        self.assertEqual(asignacion.estado, EstadoAsignacion.PENDIENTE)

    def test_asignacion_unique_together(self):
        Asignacion.objects.create(
            indicador=self.indicador,
            departamento=self.departamento,
            periodo=self.periodo,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Asignacion.objects.create(
                indicador=self.indicador,
                departamento=self.departamento,
                periodo=self.periodo,
            )
        self.assertEqual(Asignacion.objects.count(), 1)

    def test_str_representation(self):
        asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            departamento=self.departamento,
            periodo=self.periodo,
        )
        expected = f"{self.indicador} - {self.departamento} ({self.periodo})"
        self.assertEqual(str(asignacion), expected)


# ===========================================================================
# 5. HistorialEstadoModelTests
# ===========================================================================
class HistorialEstadoModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user_h",
            password="pass123",
            email="h@test.com",
        )
        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )
        self.criterio = Criterio.objects.create(
            nombre="C1",
            periodo=self.periodo,
        )
        self.indicador = Indicador.objects.create(
            nombre="I1",
            criterio=self.criterio,
        )
        self.facultad = Facultad.objects.create(nombre="Facultad X")
        self.departamento = Departamento.objects.create(
            nombre="Depto Y",
            facultad=self.facultad,
        )
        self.asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            departamento=self.departamento,
            periodo=self.periodo,
        )

    def test_crear_historial(self):
        historial = HistorialEstado.objects.create(
            asignacion=self.asignacion,
            estado_anterior=EstadoAsignacion.PENDIENTE,
            estado_nuevo=EstadoAsignacion.EN_PROGRESO,
            usuario=self.user,
            comentario="Se envia a revision",
        )
        self.assertEqual(historial.asignacion, self.asignacion)
        self.assertEqual(historial.estado_anterior, EstadoAsignacion.PENDIENTE)
        self.assertEqual(historial.estado_nuevo, EstadoAsignacion.EN_PROGRESO)
        self.assertEqual(historial.usuario, self.user)
        self.assertIsNotNone(historial.fecha)

    def test_historial_orden_fecha(self):
        h1 = HistorialEstado.objects.create(
            asignacion=self.asignacion,
            estado_anterior=EstadoAsignacion.PENDIENTE,
            estado_nuevo=EstadoAsignacion.EN_PROGRESO,
            usuario=self.user,
        )
        h2 = HistorialEstado.objects.create(
            asignacion=self.asignacion,
            estado_anterior=EstadoAsignacion.EN_PROGRESO,
            estado_nuevo=EstadoAsignacion.APROBADO,
            usuario=self.user,
        )
        historial = list(HistorialEstado.objects.filter(asignacion=self.asignacion))
        self.assertEqual(historial[0], h2)
        self.assertEqual(historial[1], h1)

    def test_str_representation(self):
        historial = HistorialEstado.objects.create(
            asignacion=self.asignacion,
            estado_anterior=EstadoAsignacion.PENDIENTE,
            estado_nuevo=EstadoAsignacion.EN_PROGRESO,
            usuario=self.user,
        )
        expected = f"{self.asignacion} {EstadoAsignacion.PENDIENTE} → {EstadoAsignacion.EN_PROGRESO}"
        self.assertEqual(str(historial), expected)


# ===========================================================================
# 6. PeriodoViewSetTests
# ===========================================================================
class PeriodoViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_group, _ = Group.objects.get_or_create(
            name="Administrador General",
        )
        self.consulta_group, _ = Group.objects.get_or_create(
            name="Consulta",
        )

        self.admin_user = User.objects.create_user(
            username="admin_p",
            password="admin123",
            email="admin_p@test.com",
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.consulta_user = User.objects.create_user(
            username="consulta_p",
            password="consulta123",
            email="consulta_p@test.com",
        )
        self.consulta_user.groups.add(self.consulta_group)
        self.consulta_token = Token.objects.create(user=self.consulta_user)

        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )

    def test_list_periodos_requires_auth(self):
        response = self.client.get("/api/periodos/")
        self.assertEqual(response.status_code, 401)

    def test_list_periodos_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.admin_token.key,
        )
        response = self.client.get("/api/periodos/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_periodo_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.admin_token.key,
        )
        payload = {
            "nombre": "Nuevo Periodo",
            "fecha_inicio": "2027-01-01",
            "fecha_fin": "2027-06-30",
            "activo": True,
        }
        response = self.client.post("/api/periodos/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Periodo.objects.filter(nombre="Nuevo Periodo").exists(),
        )

    def test_create_periodo_consulta_denied(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.consulta_token.key,
        )
        payload = {
            "nombre": "Denegado",
            "fecha_inicio": "2027-01-01",
            "fecha_fin": "2027-06-30",
        }
        response = self.client.post("/api/periodos/", payload, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Periodo.objects.filter(nombre="Denegado").exists(),
        )


# ===========================================================================
# 7. AsignacionViewSetTests
# ===========================================================================
class AsignacionViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_group, _ = Group.objects.get_or_create(
            name="Administrador General",
        )

        self.admin_user = User.objects.create_user(
            username="admin_a",
            password="admin123",
            email="admin_a@test.com",
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.facultad = Facultad.objects.create(nombre="Facultad X")
        self.departamento = Departamento.objects.create(
            nombre="Depto Y",
            facultad=self.facultad,
        )
        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        )
        self.criterio = Criterio.objects.create(
            nombre="C1",
            periodo=self.periodo,
        )
        self.indicador = Indicador.objects.create(
            nombre="I1",
            criterio=self.criterio,
        )

    def test_list_asignaciones_requires_auth(self):
        response = self.client.get("/api/asignaciones/")
        self.assertEqual(response.status_code, 401)

    def test_create_asignacion_admin(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.admin_token.key,
        )
        payload = {
            "indicador": self.indicador.pk,
            "departamento": self.departamento.pk,
            "periodo": self.periodo.pk,
        }
        response = self.client.post(
            "/api/asignaciones/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Asignacion.objects.filter(
                indicador=self.indicador,
                departamento=self.departamento,
                periodo=self.periodo,
            ).exists(),
        )
