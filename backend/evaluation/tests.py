from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auditoria.models import Auditoria
from organization.models import (
    Departamento,
    Facultad,
    PerfilUsuario,
    TipoUnidadOrganizacional,
    UnidadOrganizacional,
)

from .models import (
    Asignacion,
    Criterio,
    EstadoAsignacion,
    HistorialEstado,
    Indicador,
    Periodo,
)

User = get_user_model()


def _unidad_para_departamento(departamento):
    tipo, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Departamento")
    unidad, _ = UnidadOrganizacional.objects.get_or_create(
        departamento_legacy=departamento,
        defaults={"nombre": departamento.nombre, "tipo": tipo},
    )
    return unidad


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

    def test_finalizar_periodos_vencidos(self):
        hoy = timezone.localdate()
        vencido = Periodo.objects.create(
            nombre="Vencido",
            fecha_inicio=hoy - timedelta(days=10),
            fecha_fin=hoy - timedelta(days=1),
        )
        vigente_hasta_hoy = Periodo.objects.create(
            nombre="Vigente hoy",
            fecha_inicio=hoy - timedelta(days=1),
            fecha_fin=hoy,
            activo=False,
        )

        from .services import finalizar_periodos_vencidos

        self.assertEqual(finalizar_periodos_vencidos(), 1)
        vencido.refresh_from_db()
        vigente_hasta_hoy.refresh_from_db()
        self.assertFalse(vencido.activo)
        self.assertFalse(vigente_hasta_hoy.activo)
        self.assertTrue(
            Auditoria.objects.filter(
                modelo="Periodo",
                registro_id=vencido.pk,
                accion="Finalizar automáticamente",
            ).exists()
        )

    def test_periodo_rechaza_rango_de_fechas_invalido(self):
        periodo = Periodo(
            nombre="Fechas inválidas",
            fecha_inicio=date(2026, 6, 30),
            fecha_fin=date(2026, 1, 1),
        )
        with self.assertRaises(IntegrityError):
            periodo.save()


# ===========================================================================
# 2. CriterioModelTests
# ===========================================================================
class CriterioModelTests(TestCase):
    def setUp(self):
        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=timezone.localdate() - timedelta(days=1),
            fecha_fin=timezone.localdate() + timedelta(days=30),
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
            fecha_inicio=timezone.localdate() - timedelta(days=1),
            fecha_fin=timezone.localdate() + timedelta(days=30),
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
        _unidad_para_departamento(self.departamento)

    def test_crear_asignacion(self):
        asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            unidad_responsable=_unidad_para_departamento(self.departamento),
            periodo=self.periodo,
        )
        self.assertEqual(asignacion.indicador, self.indicador)
        self.assertEqual(asignacion.unidad_responsable.departamento_legacy, self.departamento)
        self.assertEqual(asignacion.periodo, self.periodo)

    def test_asignacion_estado_default(self):
        asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            unidad_responsable=_unidad_para_departamento(self.departamento),
            periodo=self.periodo,
        )
        self.assertEqual(asignacion.estado, EstadoAsignacion.PENDIENTE)

    def test_asignacion_unique_together(self):
        Asignacion.objects.create(
            indicador=self.indicador,
            unidad_responsable=_unidad_para_departamento(self.departamento),
            periodo=self.periodo,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Asignacion.objects.create(
                indicador=self.indicador,
                unidad_responsable=_unidad_para_departamento(self.departamento),
                periodo=self.periodo,
            )
        self.assertEqual(Asignacion.objects.count(), 1)

    def test_str_representation(self):
        asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            unidad_responsable=_unidad_para_departamento(self.departamento),
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
            unidad_responsable=_unidad_para_departamento(self.departamento),
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
        from accounts.role_permissions import _re_syncing

        _re_syncing.add(self.admin_group.pk)
        try:
            self.admin_group.permissions.set(Permission.objects.all())
        finally:
            _re_syncing.discard(self.admin_group.pk)
        self.consulta_group, _ = Group.objects.get_or_create(
            name="Consulta",
        )

        self.admin_user = User.objects.create_user(
            username="admin_p",
            password="admin123",
            email="admin_p@test.com",
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_token = RefreshToken.for_user(self.admin_user).access_token

        self.consulta_user = User.objects.create_user(
            username="consulta_p",
            password="consulta123",
            email="consulta_p@test.com",
        )
        self.consulta_user.groups.add(self.consulta_group)
        self.consulta_token = RefreshToken.for_user(self.consulta_user).access_token

        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=timezone.localdate() - timedelta(days=1),
            fecha_fin=timezone.localdate() + timedelta(days=30),
        )

    def test_list_periodos_requires_auth(self):
        response = self.client.get("/api/periodos/")
        self.assertEqual(response.status_code, 401)

    def test_list_periodos_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.get("/api/periodos/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_periodo_activo(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.get("/api/periodos/activo/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.periodo.pk)

    def test_get_periodo_activo_when_none_exists(self):
        self.periodo.activo = False
        self.periodo.save()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.get("/api/periodos/activo/")
        self.assertEqual(response.status_code, 404)

    def test_get_periodo_activo_expires_period_after_end_date(self):
        self.periodo.fecha_inicio = timezone.localdate() - timedelta(days=2)
        self.periodo.fecha_fin = timezone.localdate() - timedelta(days=1)
        self.periodo.save()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.get("/api/periodos/activo/")
        self.assertEqual(response.status_code, 404)
        self.periodo.refresh_from_db()
        self.assertFalse(self.periodo.activo)

    def test_create_periodo_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        payload = {
            "nombre": "Nuevo Periodo",
            "fecha_inicio": "2027-01-01",
            "fecha_fin": "2027-06-30",
            "activo": False,
        }
        response = self.client.post("/api/periodos/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        periodo = Periodo.objects.get(nombre="Nuevo Periodo")
        self.assertFalse(periodo.activo)
        self.assertTrue(
            Auditoria.objects.filter(modelo="Periodo", registro_id=periodo.pk, accion="Crear período").exists()
        )

    def test_update_periodo_admin_is_audited(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.patch(
            f"/api/periodos/{self.periodo.pk}/",
            {"nombre": "P1 actualizado"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        auditoria = Auditoria.objects.get(modelo="Periodo", registro_id=self.periodo.pk, accion="Actualizar período")
        self.assertIn("nombre", auditoria.descripcion)

    def test_expired_period_can_be_extended_and_reactivated(self):
        hoy = timezone.localdate()
        self.periodo.fecha_inicio = hoy - timedelta(days=2)
        self.periodo.fecha_fin = hoy - timedelta(days=1)
        self.periodo.save()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))

        vencido = self.client.get("/api/periodos/activo/")
        actualizado = self.client.patch(
            f"/api/periodos/{self.periodo.pk}/",
            {"fecha_fin": (hoy + timedelta(days=30)).isoformat(), "activo": True},
            format="json",
        )

        self.assertEqual(vencido.status_code, 404)
        self.assertEqual(actualizado.status_code, 200, actualizado.data)
        self.assertTrue(actualizado.data["activo"])
        self.assertTrue(
            Auditoria.objects.filter(
                modelo="Periodo",
                registro_id=self.periodo.pk,
                accion="Finalizar automáticamente",
            ).exists()
        )
        self.assertTrue(
            Auditoria.objects.filter(
                modelo="Periodo",
                registro_id=self.periodo.pk,
                accion="Actualizar período",
            ).exists()
        )

    def test_create_active_period_when_another_is_active_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        payload = {
            "nombre": "Segundo activo",
            "fecha_inicio": "2027-01-01",
            "fecha_fin": "2027-06-30",
            "activo": True,
        }
        response = self.client.post("/api/periodos/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("activo", response.data)

    def test_create_period_with_invalid_date_range_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        payload = {
            "nombre": "Rango inválido",
            "fecha_inicio": "2027-06-30",
            "fecha_fin": "2027-01-01",
            "activo": False,
        }
        response = self.client.post("/api/periodos/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("fecha_fin", response.data)

    def test_create_periodo_consulta_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.consulta_token))
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
        from accounts.role_permissions import _re_syncing

        _re_syncing.add(self.admin_group.pk)
        try:
            self.admin_group.permissions.set(Permission.objects.all())
        finally:
            _re_syncing.discard(self.admin_group.pk)

        self.admin_user = User.objects.create_user(
            username="admin_a",
            password="admin123",
            email="admin_a@test.com",
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_token = RefreshToken.for_user(self.admin_user).access_token

        self.facultad = Facultad.objects.create(nombre="Facultad X")
        self.departamento = Departamento.objects.create(
            nombre="Depto Y",
            facultad=self.facultad,
        )
        self.unidad = _unidad_para_departamento(self.departamento)
        self.periodo = Periodo.objects.create(
            nombre="P1",
            fecha_inicio=timezone.localdate() - timedelta(days=1),
            fecha_fin=timezone.localdate() + timedelta(days=30),
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
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
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
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(
            Asignacion.objects.filter(
                indicador=self.indicador,
                unidad_responsable=_unidad_para_departamento(self.departamento),
                periodo=self.periodo,
            ).exists(),
        )

    def test_list_asignaciones_can_query_historical_period(self):
        self.periodo.activo = False
        self.periodo.save()
        asignacion = Asignacion.objects.create(
            indicador=self.indicador,
            unidad_responsable=self.unidad,
            periodo=self.periodo,
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.get(f"/api/asignaciones/?periodo={self.periodo.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["results"]], [asignacion.pk])

    def test_create_asignacion_for_historical_period_is_denied(self):
        self.periodo.activo = False
        self.periodo.save()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.post(
            "/api/asignaciones/",
            {
                "indicador": self.indicador.pk,
                "unidad_responsable": self.unidad.pk,
                "periodo": self.periodo.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_responsable_puede_asignar_a_unidad_sin_departamento(self):
        tipo, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Direccion")
        unidad = UnidadOrganizacional.objects.create(nombre="Recursos Humanos", tipo=tipo)
        responsable = User.objects.create_user(
            username="responsable_rrhh",
            email="responsable_rrhh@test.com",
            password="claveSeguraTest1",
        )
        responsable.user_permissions.add(
            Permission.objects.get(content_type__app_label="evaluation", codename="view_asignacion"),
            Permission.objects.get(content_type__app_label="evaluation", codename="add_asignacion"),
        )
        PerfilUsuario.objects.create(usuario=responsable, unidad_organizacional=unidad)
        self.client.force_authenticate(user=responsable)

        response = self.client.post(
            "/api/asignaciones/",
            {
                "indicador": self.indicador.pk,
                "unidad_responsable": unidad.pk,
                "periodo": self.periodo.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["unidad_responsable"], unidad.pk)
        self.assertTrue(Asignacion.objects.filter(unidad_responsable=unidad).exists())
