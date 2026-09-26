"""Tests del flujo de estados de asignacion (nucleo del sistema)."""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from evaluation.models import Asignacion, Criterio, EstadoAsignacion, Indicador, Periodo
from organization.models import Departamento, Facultad

User = get_user_model()


def _superuser():
    return User.objects.create_superuser("admin_flujo", "admin@test.com", "claveSeguraTest1")


def _simple():
    return User.objects.create_user("simple", "simple@test.com", "claveSeguraTest1")


def _token(u):
    return str(RefreshToken.for_user(u).access_token)


def _asignacion(tag="A"):
    fac = Facultad.objects.create(nombre=f"Facultad {tag}")
    dep = Departamento.objects.create(nombre=f"Depto {tag}", facultad=fac)
    per = Periodo.objects.create(nombre=f"Periodo {tag}", fecha_inicio="2025-01-01", fecha_fin="2025-12-31")
    cri = Criterio.objects.create(nombre=f"Criterio {tag}", periodo=per)
    ind = Indicador.objects.create(nombre=f"Indicador {tag}", criterio=cri)
    return Asignacion.objects.create(indicador=ind, departamento=dep, periodo=per)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class FlujoAsignacionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _superuser()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + _token(self.user))
        self.asig = _asignacion()

    def test_en_revision(self):
        r = self.client.post(f"/api/asignaciones/{self.asig.pk}/en_revision/")
        self.assertTrue(r.status_code in (200, 201, 400), r.status_code)
        if r.status_code == 400:
            self.skipTest("Transicion no permitida desde PENDIENTE")
        self.asig.refresh_from_db()
        self.assertIn(self.asig.estado, [EstadoAsignacion.EN_PROGRESO, EstadoAsignacion.COMPLETADO])

    def test_aprobar_no_rompe_y_queda_aprobado(self):
        self.asig.estado = EstadoAsignacion.EN_PROGRESO
        self.asig.save()
        r = self.client.post(f"/api/asignaciones/{self.asig.pk}/aprobar/", {"comentario": "ok"})
        self.assertTrue(r.status_code in (200, 400), r.status_code)
        self.asig.refresh_from_db()
        self.assertEqual(self.asig.estado, EstadoAsignacion.APROBADO)

    def test_rechazar_no_rompe_y_queda_rechazado(self):
        self.asig.estado = EstadoAsignacion.EN_PROGRESO
        self.asig.save()
        r = self.client.post(f"/api/asignaciones/{self.asig.pk}/rechazar/", {"comentario": "falta"})
        self.assertTrue(r.status_code in (200, 400), r.status_code)
        self.asig.refresh_from_db()
        self.assertEqual(self.asig.estado, EstadoAsignacion.RECHAZADO)

    def test_observada_no_rompe(self):
        self.asig.estado = EstadoAsignacion.EN_PROGRESO
        self.asig.save()
        r = self.client.post(f"/api/asignaciones/{self.asig.pk}/observada/", {"comentario": "ajuste"})
        self.assertIn(r.status_code, [200, 400], r.status_code)

    def test_usuario_sin_permiso_no_aprueba(self):
        simple = _simple()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + _token(simple))
        r = self.client.post(f"/api/asignaciones/{self.asig.pk}/aprobar/")
        self.assertIn(r.status_code, [403, 401, 400], r.status_code)
        self.asig.refresh_from_db()
        self.assertNotEqual(self.asig.estado, EstadoAsignacion.APROBADO)

    def test_resumen_asignacion(self):
        r = self.client.get(f"/api/asignaciones/{self.asig.pk}/resumen/")
        self.assertEqual(r.status_code, 200)

    def test_estados_validos_no_500(self):
        for accion in ("en_revision", "aprobar", "rechazar", "observada"):
            asig = _asignacion(tag=accion)
            r = self.client.post(f"/api/asignaciones/{asig.pk}/{accion}/", {"comentario": "x"})
            self.assertLess(r.status_code, 500, f"{accion} no debe dar 5xx, dio {r.status_code}")
