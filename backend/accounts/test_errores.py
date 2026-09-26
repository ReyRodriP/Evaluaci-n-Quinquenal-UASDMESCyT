"""
Tests de error / negativos: fuerzan respuestas 4xx y 5xx de la API.
Si un endpoint devuelve 500 cuando deberia devolver 4xx, este suite lo detecta.
"""

import io

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from evaluation.models import Asignacion, Criterio, Indicador, Periodo
from evidence.models import Evidencia
from organization.models import Departamento, Facultad

User = get_user_model()


def _make_user(username="usuario", groups=None, is_superuser=False):
    if is_superuser:
        user = User.objects.create_superuser(
            username=username, email=f"{username}@test.com", password="claveSeguraTest1"
        )
    else:
        user = User.objects.create_user(username=username, email=f"{username}@test.com", password="claveSeguraTest1")
    if groups:
        user.groups.add(*groups)
    return user


def _token(user):
    return str(RefreshToken.for_user(user).access_token)


def _make_asignacion():
    facultad = Facultad.objects.create(nombre="F")
    dep = Departamento.objects.create(nombre="D", facultad=facultad)
    periodo = Periodo.objects.create(nombre="P", fecha_inicio="2025-01-01", fecha_fin="2025-12-31")
    criterio = Criterio.objects.create(nombre="C", periodo=periodo)
    indicador = Indicador.objects.create(nombre="I", criterio=criterio)
    return Asignacion.objects.create(indicador=indicador, departamento=dep, periodo=periodo)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class AutenticacionErroresTests(TestCase):
    """Fuerza errores de autenticacion y validacion."""

    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def test_login_credenciales_invalidas(self):
        r = self.client.post("/api/login", {"username": "noexiste", "password": "incorrecta"})
        self.assertEqual(r.status_code, 400)

    def test_login_sin_campos(self):
        r = self.client.post("/api/login", {})
        self.assertEqual(r.status_code, 400)

    def test_login_usuario_inactivo(self):
        user = _make_user("inactivo")
        user.is_active = False
        user.save()
        r = self.client.post("/api/login", {"username": "inactivo", "password": "claveSeguraTest1"})
        self.assertEqual(r.status_code, 403)

    def test_register_password_debil(self):
        r = self.client.post(
            "/api/register",
            {
                "username": "nuevo",
                "email": "nuevo@test.com",
                "password": "corta",
                "first_name": "A",
                "last_name": "B",
                "telefono": "8095550000",
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_register_password_numerica(self):
        r = self.client.post(
            "/api/register",
            {
                "username": "nuevo2",
                "email": "nuevo2@test.com",
                "password": "1234567890",
                "first_name": "A",
                "last_name": "B",
                "telefono": "8095550000",
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_register_email_invalido(self):
        r = self.client.post(
            "/api/register",
            {
                "username": "nuevo3",
                "email": "no-es-email",
                "password": "claveSeguraTest1",
                "first_name": "A",
                "last_name": "B",
                "telefono": "8095550000",
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_register_email_duplicado(self):
        _make_user("existente")
        User.objects.filter(username="existente").update(email="dup@test.com")
        r = self.client.post(
            "/api/register",
            {
                "username": "nuevo4",
                "email": "dup@test.com",
                "password": "claveSeguraTest1",
                "first_name": "A",
                "last_name": "B",
                "telefono": "8095550000",
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_change_password_actual_incorrecta(self):
        user = _make_user("cambia")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + _token(user))
        r = self.client.post(
            "/api/change_password", {"old_password": "incorrecta", "new_password": "nuevaClaveSegura1"}
        )
        self.assertEqual(r.status_code, 400)

    def test_change_password_debil(self):
        user = _make_user("cambia2")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + _token(user))
        r = self.client.post("/api/change_password", {"old_password": "claveSeguraTest1", "new_password": "corta"})
        self.assertEqual(r.status_code, 400)

    def test_reset_password_enlace_invalido(self):
        r = self.client.post(
            "/api/reset_password", {"uid": "NADA", "token": "NADA", "new_password": "claveSeguraTest1"}
        )
        self.assertEqual(r.status_code, 400)

    def test_reset_password_sin_campos(self):
        r = self.client.post("/api/reset_password", {})
        self.assertEqual(r.status_code, 400)

    def test_endpoints_protegidos_sin_token(self):
        protegidos = [
            "/api/facultades/",
            "/api/departamentos/",
            "/api/periodos/",
            "/api/criterios/",
            "/api/indicadores/",
            "/api/asignaciones/",
            "/api/evidencias/",
            "/api/usuarios/",
            "/api/roles/",
            "/api/perfiles/",
            "/api/notificaciones/",
            "/api/auditoria/",
            "/api/dashboard/resumen/",
            "/api/reportes/general/",
            "/api/me",
        ]
        for url in protegidos:
            with self.subTest(url=url):
                r = self.client.get(url)
                self.assertIn(r.status_code, [401, 403], f"{url} deberia exigir autenticacion, dio {r.status_code}")

    def test_login_lockout_por_intentos(self):
        _make_user("bloqueado")
        statuses = []
        for _ in range(6):
            r = self.client.post("/api/login", {"username": "bloqueado", "password": "incorrecta"})
            statuses.append(r.status_code)
        self.assertEqual(statuses[-1], 403, "Tras 5 intentos fallidos debe bloquearse la IP")


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class EvidenciasErroresTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _make_user(is_superuser=True)
        self.asignacion = _make_asignacion()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + _token(self.user))

    def test_crear_evidencia_sin_archivo_ok(self):
        # El diseno crea la evidencia primero; el archivo se adjunta en subir_version.
        r = self.client.post(
            "/api/evidencias/",
            {"titulo": "Ev", "descripcion": "D", "asignacion": self.asignacion.pk},
            format="json",
        )
        self.assertEqual(r.status_code, 201)
        ev = Evidencia.objects.get(titulo="Ev")
        self.client.post(f"/api/evidencias/{ev.id_evidencia}/subir_version/", {})
        return ev

    def test_subir_version_requiere_archivo(self):
        ev = self.test_crear_evidencia_sin_archivo_ok()
        r = self.client.post(f"/api/evidencias/{ev.id_evidencia}/subir_version/", {})
        self.assertEqual(r.status_code, 400)

    def test_subir_version_tipo_invalido(self):
        ev = self.test_crear_evidencia_sin_archivo_ok()
        fa = io.BytesIO(b"no soy un pdf")
        fa.name = "falso.pdf"
        fa.content_type = "text/html"
        r = self.client.post(f"/api/evidencias/{ev.id_evidencia}/subir_version/", {"archivo": fa}, format="multipart")
        self.assertIn(r.status_code, [400, 403])

    def test_descargar_version_inexistente(self):
        r = self.client.get("/api/versiones/999999/descargar/")
        self.assertEqual(r.status_code, 404)

    def test_descargar_version_sin_token(self):
        self.client.credentials()
        r = self.client.get("/api/versiones/999999/descargar/")
        self.assertEqual(r.status_code, 401)

    def test_perfil_foto_no_imagen(self):
        cad = io.BytesIO(b"no soy una imagen")
        cad.name = "photo.txt"
        r = self.client.patch("/api/profile", {"foto_perfil": cad}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_perfil_foto_imagen_valida(self):
        img = io.BytesIO()
        Image.new("RGB", (1, 1), color="red").save(img, format="JPEG")
        img.seek(0)
        img.name = "pic.jpg"
        r = self.client.patch("/api/profile", {"foto_perfil": img}, format="multipart")
        self.assertEqual(r.status_code, 200)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class SeguridadErroresTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = _make_user(is_superuser=True)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + _token(self.user))

    def test_busqueda_sql_injection_no_crash(self):
        r = self.client.get("/api/search/", {"q": "'; DROP TABLE accounts_user; --"})
        # El middleware anti-SQLi lo bloquea con 400 (nunca 500 ni ejecucion).
        self.assertIn(r.status_code, [200, 400])

    def test_busqueda_xss_no_crash(self):
        r = self.client.get("/api/search/", {"q": "<script>alert(1)</script>"})
        self.assertEqual(r.status_code, 200)

    def test_json_invalido(self):
        r = self.client.post("/api/facultades/", data="{malformed", content_type="application/json")
        self.assertIn(r.status_code, [400, 415])

    def test_payload_extra_grande(self):
        r = self.client.post(
            "/api/facultades/",
            {"nombre": "X" * 52 * 1024 * 1024},
            format="json",
        )
        self.assertIn(r.status_code, [400, 413, 429])

    def test_docs_requieren_autenticacion(self):
        self.client.credentials()
        r = self.client.get("/api/docs/")
        self.assertIn(r.status_code, [401, 403])


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class AutorizacionErroresTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _make_user(is_superuser=True)
        self.asignacion = _make_asignacion()

    def test_usuario_sin_permiso_no_accede_a_usuarios(self):
        simple = _make_user("simple")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + _token(simple))
        r = self.client.get("/api/usuarios/")
        self.assertIn(r.status_code, [401, 403])

    def test_superuser_accede_a_reportes(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + _token(self.admin))
        r = self.client.get("/api/reportes/general/")
        self.assertEqual(r.status_code, 200)
