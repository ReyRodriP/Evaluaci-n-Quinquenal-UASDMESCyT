from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from .models import Facultad, Departamento, PerfilUsuario

User = get_user_model()


@override_settings(PASSWORD_HASHERS=[
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
])
class FacultadModelTests(TestCase):
    def setUp(self):
        self.facultad = Facultad.objects.create(
            nombre="Ingenieria",
            descripcion="Facultad de Ingenieria",
        )

    def test_crear_facultad(self):
        self.assertEqual(self.facultad.nombre, "Ingenieria")
        self.assertEqual(self.facultad.descripcion, "Facultad de Ingenieria")
        self.assertIsNotNone(self.facultad.fecha_creacion)

    def test_facultad_nombre_unique(self):
        with self.assertRaises(IntegrityError):
            Facultad.objects.create(nombre="Ingenieria", descripcion="Otra")

    def test_facultad_default_activo(self):
        self.assertTrue(self.facultad.activo)

    def test_str_representation(self):
        self.assertEqual(str(self.facultad), "Ingenieria")


@override_settings(PASSWORD_HASHERS=[
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
])
class DepartamentoModelTests(TestCase):
    def setUp(self):
        self.facultad = Facultad.objects.create(nombre="Ciencias")
        self.departamento = Departamento.objects.create(
            nombre="Matematicas",
            descripcion="Depto de Matematicas",
            facultad=self.facultad,
        )

    def test_crear_departamento(self):
        self.assertEqual(self.departamento.nombre, "Matematicas")
        self.assertEqual(self.departamento.descripcion, "Depto de Matematicas")
        self.assertIsNotNone(self.departamento.fecha_creacion)

    def test_departamento_pertenece_facultad(self):
        self.assertEqual(self.departamento.facultad, self.facultad)
        self.assertIn(self.departamento, self.facultad.departamentos.all())

    def test_str_representation(self):
        self.assertEqual(str(self.departamento), "Matematicas")


@override_settings(PASSWORD_HASHERS=[
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
])
class PerfilUsuarioModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="testuser@test.com", password="testpass123"
        )
        self.facultad = Facultad.objects.create(nombre="Medicina")
        self.departamento = Departamento.objects.create(
            nombre="Anatomia", facultad=self.facultad
        )
        self.perfil = PerfilUsuario.objects.create(
            usuario=self.user, departamento=self.departamento
        )

    def test_crear_perfil(self):
        self.assertEqual(self.perfil.usuario, self.user)
        self.assertEqual(self.perfil.departamento, self.departamento)

    def test_perfil_one_to_one(self):
        user2 = User.objects.create_user(
            username="testuser2", email="testuser2@test.com", password="testpass123"
        )
        PerfilUsuario.objects.create(usuario=user2, departamento=self.departamento)
        with self.assertRaises(IntegrityError):
            PerfilUsuario.objects.create(usuario=self.user, departamento=self.departamento)

    def test_str_representation(self):
        self.assertEqual(str(self.perfil), "testuser")


@override_settings(PASSWORD_HASHERS=[
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
])
class FacultadViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.facultad_data = {"nombre": "Derecho", "descripcion": "Facultad de Derecho"}

        self.admin_group, _ = Group.objects.get_or_create(name="Administrador General")
        self.admin_user = User.objects.create_user(
            username="admin_user", email="admin@test.com", password="testpass123"
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.consulta_group, _ = Group.objects.get_or_create(name="Consulta")
        self.consulta_user = User.objects.create_user(
            username="consulta_user", email="consulta@test.com", password="testpass123"
        )
        self.consulta_user.groups.add(self.consulta_group)
        self.consulta_token = Token.objects.create(user=self.consulta_user)

        self.facultad = Facultad.objects.create(
            nombre="Ciencias Economicas", descripcion="Facultad de Economia"
        )

    def test_list_facultades_requires_auth(self):
        response = self.client.get("/api/facultades/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_facultades_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        response = self.client.get("/api/facultades/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_facultad_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        response = self.client.post("/api/facultades/", self.facultad_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Facultad.objects.count(), 2)
        self.assertEqual(response.data["nombre"], "Derecho")

    def test_create_facultad_consulta_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.consulta_token.key}")
        response = self.client.post("/api/facultades/", self.facultad_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_facultad_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        update_data = {"nombre": "Ciencias Economicas Update", "descripcion": "Actualizado"}
        response = self.client.put(
            f"/api/facultades/{self.facultad.pk}/", update_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.facultad.refresh_from_db()
        self.assertEqual(self.facultad.nombre, "Ciencias Economicas Update")

    def test_delete_facultad_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        response = self.client.delete(f"/api/facultades/{self.facultad.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Facultad.objects.filter(pk=self.facultad.pk).exists())


@override_settings(PASSWORD_HASHERS=[
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
])
class DepartamentoViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.facultad = Facultad.objects.create(nombre="Filosofia")
        self.departamento_data = {
            "nombre": "Historia",
            "facultad": self.facultad.pk,
        }

        self.admin_group, _ = Group.objects.get_or_create(name="Administrador General")
        self.admin_user = User.objects.create_user(
            username="admin_dept", email="admin_dept@test.com", password="testpass123"
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_token = Token.objects.create(user=self.admin_user)

    def test_list_departamentos_requires_auth(self):
        response = self.client.get("/api/departamentos/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_departamento_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        response = self.client.post(
            "/api/departamentos/", self.departamento_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Departamento.objects.count(), 1)
        self.assertEqual(response.data["nombre"], "Historia")
        self.assertEqual(response.data["facultad"], self.facultad.pk)
