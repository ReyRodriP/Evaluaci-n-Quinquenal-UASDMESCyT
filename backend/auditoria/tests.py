from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Auditoria

User = get_user_model()


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class AuditoriaModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="auditor", email="aud@test.com", password="testpass123")

    def test_crear(self):
        auditoria = Auditoria.objects.create(
            usuario=self.user,
            accion="Crear registro",
            modelo="Evidencia",
            registro_id=1,
            descripcion="Se creó una evidencia de prueba",
        )
        self.assertIsNotNone(auditoria.pk)
        self.assertEqual(auditoria.accion, "Crear registro")
        self.assertEqual(auditoria.usuario, self.user)
        self.assertEqual(auditoria.modelo, "Evidencia")
        self.assertEqual(auditoria.registro_id, 1)

    def test_str(self):
        auditoria = Auditoria.objects.create(
            usuario=self.user, accion="Eliminar", modelo="Evidencia", descripcion="Eliminación de prueba"
        )
        self.assertIn("Eliminar", str(auditoria))
        self.assertIn(str(auditoria.fecha), str(auditoria))

    def test_orden_fecha(self):
        now = timezone.now()
        a1 = Auditoria.objects.create(
            usuario=self.user, accion="Primera", modelo="Test", descripcion="Primera acción", fecha=now
        )
        a2 = Auditoria.objects.create(
            usuario=self.user, accion="Segunda", modelo="Test", descripcion="Segunda acción", fecha=now
        )
        auditorias = list(Auditoria.objects.values_list("accion", flat=True))
        self.assertEqual(auditorias[0], "Segunda")
        self.assertEqual(auditorias[1], "Primera")


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class AuditoriaViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser(
            username="admin_aud", email="admin_aud@test.com", password="testpass123"
        )
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.regular_user = User.objects.create_user(username="regular", email="reg@test.com", password="testpass123")
        self.regular_token = Token.objects.create(user=self.regular_user)

    def test_list_requires_auth(self):
        response = self.client.get("/api/auditoria/")
        self.assertEqual(response.status_code, 401)

    def test_list_admin(self):
        Auditoria.objects.create(
            usuario=self.admin_user, accion="Test", modelo="Evidencia", descripcion="Test admin access"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        response = self.client.get("/api/auditoria/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["results"]), 1)
