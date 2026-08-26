import io
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

User = get_user_model()


class PasswordRecoveryTests(TestCase):
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_forgot_password_sends_email_for_registered_user(self):
        user_model = get_user_model()
        user_model.objects.create_user(username="jane", email="jane@example.com", password="oldpassword123")

        response = self.client.post(
            "/api/forgot_password", {"email": "jane@example.com"}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Restablecimiento", mail.outbox[0].subject)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_forgot_password_is_generic_for_unknown_email(self):
        response = self.client.post(
            "/api/forgot_password", {"email": "missing@example.com"}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_forgot_password_does_not_crash_when_email_delivery_fails(self):
        user_model = get_user_model()
        user_model.objects.create_user(username="jane2", email="jane2@example.com", password="oldpassword123")

        with patch("accounts.views.send_mail", side_effect=Exception("SMTP error")):
            response = self.client.post(
                "/api/forgot_password", {"email": "jane2@example.com"}, content_type="application/json"
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("recuperar tu contraseña", response.json()["message"])

    def test_reset_password_accepts_valid_uid_and_token(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="john", email="john@example.com", password="oldpassword123")

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        response = self.client.post(
            "/api/reset_password",
            {"uid": uid, "token": token, "new_password": "newpassword123!"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpassword123!"))


class ObjectivesTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_group, _ = Group.objects.get_or_create(name="Administrador General")
        self.consulta_group, _ = Group.objects.get_or_create(name="Consulta")

        all_permissions = Permission.objects.all()
        self.admin_group.permissions.set(all_permissions)
        self.consulta_group.permissions.clear()

        self.admin_user = User.objects.create_user(username="admin", password="admin123", email="admin@test.com")
        self.admin_user.groups.add(self.admin_group)

        self.consulta_user = User.objects.create_user(
            username="consulta", password="consulta123", email="consulta@test.com"
        )
        self.consulta_user.groups.add(self.consulta_group)

        self.admin_token = Token.objects.create(user=self.admin_user)
        self.consulta_token = Token.objects.create(user=self.consulta_user)

    # --- Objective 1: group_ids not allowed in register/profile ---
    def test_register_rejects_group_ids(self):
        response = self.client.post(
            "/api/register",
            {"username": "newuser", "email": "new@test.com", "password": "pass123", "group_ids": [self.admin_group.id]},
        )
        self.assertNotIn("group_ids", response.data.get("user", {}))
        user = User.objects.get(username="newuser")
        self.assertEqual(user.groups.count(), 0)

    def test_profile_rejects_group_ids(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        self.client.put("/api/profile", {"group_ids": [self.consulta_group.id]})
        user = User.objects.get(id=self.admin_user.id)
        self.assertEqual(user.groups.first().name, "Administrador General")

    # --- Objective 2: permisos endpoint ---
    def test_permisos_endpoint_structure(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        response = self.client.get(f"/api/usuarios/{self.admin_user.id}/permisos/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", response.data)
        self.assertIn("username", response.data)
        self.assertIn("rol", response.data)
        self.assertIn("permisos", response.data)
        self.assertEqual(response.data["id"], self.admin_user.id)
        self.assertEqual(response.data["username"], "admin")
        self.assertEqual(response.data["rol"], "Administrador General")
        self.assertGreater(len(response.data["permisos"]), 0)

    def test_permisos_endpoint_consulta(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        response = self.client.get(f"/api/usuarios/{self.consulta_user.id}/permisos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rol"], "Consulta")
        self.assertEqual(len(response.data["permisos"]), 0)

    # --- Objective 3: Seed permissions ---
    def test_admin_has_all_permissions(self):
        total = Permission.objects.count()
        self.assertEqual(self.admin_group.permissions.count(), total)

    def test_consulta_has_no_permissions(self):
        self.assertEqual(self.consulta_group.permissions.count(), 0)

    # --- Objective 4: CRUD protection ---
    def test_consulta_user_cannot_access_facultades(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.consulta_token.key)
        response = self.client.get("/api/facultades/")
        self.assertEqual(response.status_code, 403)

    def test_admin_user_can_access_facultades(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        response = self.client.get("/api/facultades/")
        self.assertEqual(response.status_code, 200)

    def test_consulta_user_cannot_access_periodos(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.consulta_token.key)
        response = self.client.get("/api/periodos/")
        self.assertEqual(response.status_code, 403)

    def test_admin_user_can_access_periodos(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        response = self.client.get("/api/periodos/")
        self.assertEqual(response.status_code, 200)

    def test_consulta_user_cannot_access_usuarios(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.consulta_token.key)
        response = self.client.get("/api/usuarios/")
        self.assertEqual(response.status_code, 403)

    def test_consulta_user_cannot_create_facultad(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.consulta_token.key)
        response = self.client.post("/api/facultades/", {"nombre": "Test", "descripcion": "test"})
        self.assertEqual(response.status_code, 403)

    def test_profile_endpoint_updates_user_data(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        response = self.client.patch(
            "/api/profile", {"first_name": "Ana", "last_name": "Pérez", "telefono": "8095551234"}
        )

        self.assertEqual(response.status_code, 200)
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.first_name, "Ana")
        self.assertEqual(self.admin_user.last_name, "Pérez")
        self.assertEqual(self.admin_user.telefono, "8095551234")

    def test_change_password_endpoint_updates_password(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        response = self.client.post(
            "/api/change_password", {"old_password": "admin123", "new_password": "newpassword123!"}
        )

        self.assertEqual(response.status_code, 200)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password("newpassword123!"))

    def test_profile_endpoint_accepts_profile_image(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.admin_token.key)
        img_buffer = io.BytesIO()
        img = Image.new("RGB", (1, 1), color="red")
        img.save(img_buffer, format="JPEG")
        img_buffer.seek(0)

        image = SimpleUploadedFile("avatar.jpg", img_buffer.read(), content_type="image/jpeg")

        response = self.client.patch("/api/profile", {"foto_perfil": image}, format="multipart")

        self.assertEqual(response.status_code, 200)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.foto_perfil)

    def test_unauthenticated_user_blocked(self):
        response = self.client.get("/api/facultades/")
        self.assertEqual(response.status_code, 401)


class SecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")
        self.active_user = User.objects.create_user(
            username="activeuser", password="activepass123", email="active@example.com", is_active=True
        )
        self.inactive_user = User.objects.create_user(
            username="inactiveuser", password="inactivepass123", email="inactive@example.com", is_active=False
        )

    def test_login_rate_limiting(self):
        for i in range(5):
            response = self.client.post("/api/login", {"username": "testuser", "password": "wrongpassword"})
        response = self.client.post("/api/login", {"username": "testuser", "password": "wrongpassword"})
        self.assertEqual(response.status_code, 403)

    def test_register_rejects_short_password(self):
        response = self.client.post(
            "/api/register", {"username": "newuser", "email": "new@example.com", "password": "abc"}
        )
        self.assertEqual(response.status_code, 400)

    def test_register_rejects_invalid_email(self):
        response = self.client.post(
            "/api/register", {"username": "newuser", "email": "notanemail", "password": "validpass123"}
        )
        self.assertEqual(response.status_code, 400)

    def test_register_rejects_special_chars_username(self):
        response = self.client.post(
            "/api/register", {"username": "user@name!", "email": "new@example.com", "password": "validpass123"}
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_access_returns_401(self):
        response = self.client.get("/api/usuarios/")
        self.assertEqual(response.status_code, 401)

    def test_superuser_can_access_anything(self):
        superuser = User.objects.create_superuser(username="admin", password="adminpass123", email="admin@example.com")
        token = Token.objects.create(user=superuser)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.get("/api/usuarios/")
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_delete_self(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        with self.assertRaises(Exception):
            self.client.delete(f"/api/usuarios/{self.user.id}/")
        self.assertTrue(User.objects.filter(id=self.user.id).exists())

    def test_login_inactive_user(self):
        response = self.client.post("/api/login", {"username": "inactiveuser", "password": "inactivepass123"})
        self.assertEqual(response.status_code, 403)

    def test_change_password_wrong_old_password(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        response = self.client.post(
            "/api/change_password", {"old_password": "wrongoldpassword", "new_password": "newpassword123!"}
        )
        self.assertEqual(response.status_code, 400)

    def test_forgot_password_invalid_email_format(self):
        response = self.client.post("/api/forgot_password", {"email": "bad"})
        self.assertEqual(response.status_code, 400)

    def test_profile_read_only_fields(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        original_username = self.user.username
        self.client.patch("/api/profile", {"username": "hackedname"})
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, original_username)


class TokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tokentest", password="tokenpass123", email="token@example.com")

    def test_token_created_on_login(self):
        self.client.post("/api/login", {"username": "tokentest", "password": "tokenpass123"})
        self.assertTrue(Token.objects.filter(user=self.user).exists())

    def test_token_reused_on_second_login(self):
        self.client.post("/api/login", {"username": "tokentest", "password": "tokenpass123"})
        first_token = Token.objects.get(user=self.user)
        self.client.post("/api/login", {"username": "tokentest", "password": "tokenpass123"})
        second_token = Token.objects.get(user=self.user)
        self.assertEqual(first_token.key, second_token.key)

    def test_token_deleted_on_logout(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        self.client.post("/api/logout")
        self.assertFalse(Token.objects.filter(user=self.user).exists())
