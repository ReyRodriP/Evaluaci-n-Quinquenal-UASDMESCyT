from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Departamento,
    Facultad,
    PerfilUsuario,
    TipoUnidadOrganizacional,
    UnidadOrganizacional,
)

User = get_user_model()


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
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


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
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


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class PerfilUsuarioModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="testuser@test.com", password="testpass123")
        self.facultad = Facultad.objects.create(nombre="Medicina")
        self.departamento = Departamento.objects.create(nombre="Anatomia", facultad=self.facultad)
        self.perfil = PerfilUsuario.objects.create(usuario=self.user, departamento=self.departamento)

    def test_crear_perfil(self):
        self.assertEqual(self.perfil.usuario, self.user)
        self.assertEqual(self.perfil.departamento, self.departamento)

    def test_perfil_one_to_one(self):
        user2 = User.objects.create_user(username="testuser2", email="testuser2@test.com", password="testpass123")
        PerfilUsuario.objects.create(usuario=user2, departamento=self.departamento)
        with self.assertRaises(IntegrityError):
            PerfilUsuario.objects.create(usuario=self.user, departamento=self.departamento)

    def test_str_representation(self):
        self.assertEqual(str(self.perfil), "testuser")


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class FacultadViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.facultad_data = {"nombre": "Derecho", "descripcion": "Facultad de Derecho"}

        self.admin_group, _ = Group.objects.get_or_create(name="Administrador General")
        from accounts.role_permissions import _re_syncing

        _re_syncing.add(self.admin_group.pk)
        try:
            self.admin_group.permissions.set(Permission.objects.all())
        finally:
            _re_syncing.discard(self.admin_group.pk)
        self.admin_user = User.objects.create_user(
            username="admin_user", email="admin@test.com", password="testpass123"
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_token = RefreshToken.for_user(self.admin_user).access_token

        self.consulta_group, _ = Group.objects.get_or_create(name="Consulta")
        self.consulta_user = User.objects.create_user(
            username="consulta_user", email="consulta@test.com", password="testpass123"
        )
        self.consulta_user.groups.add(self.consulta_group)
        self.consulta_token = RefreshToken.for_user(self.consulta_user).access_token

        self.facultad = Facultad.objects.create(nombre="Ciencias Economicas", descripcion="Facultad de Economia")

    def test_list_facultades_requires_auth(self):
        response = self.client.get("/api/facultades/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_facultades_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.get("/api/facultades/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_create_facultad_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.post("/api/facultades/", self.facultad_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Facultad.objects.count(), 2)
        self.assertEqual(response.data["nombre"], "Derecho")

    def test_create_facultad_consulta_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.consulta_token))
        response = self.client.post("/api/facultades/", self.facultad_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_facultad_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        update_data = {"nombre": "Ciencias Economicas Update", "descripcion": "Actualizado"}
        response = self.client.put(f"/api/facultades/{self.facultad.pk}/", update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.facultad.refresh_from_db()
        self.assertEqual(self.facultad.nombre, "Ciencias Economicas Update")

    def test_delete_facultad_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.delete(f"/api/facultades/{self.facultad.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Facultad.objects.filter(pk=self.facultad.pk).exists())


@override_settings(
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ]
)
class DepartamentoViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.facultad = Facultad.objects.create(nombre="Filosofia")
        self.departamento_data = {
            "nombre": "Historia",
            "facultad": self.facultad.pk,
        }

        self.admin_group, _ = Group.objects.get_or_create(name="Administrador General")
        from accounts.role_permissions import _re_syncing

        _re_syncing.add(self.admin_group.pk)
        try:
            self.admin_group.permissions.set(Permission.objects.all())
        finally:
            _re_syncing.discard(self.admin_group.pk)
        self.admin_user = User.objects.create_user(
            username="admin_dept", email="admin_dept@test.com", password="testpass123"
        )
        self.admin_user.groups.add(self.admin_group)
        self.admin_token = RefreshToken.for_user(self.admin_user).access_token

    def test_list_departamentos_requires_auth(self):
        response = self.client.get("/api/departamentos/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_departamento_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + str(self.admin_token))
        response = self.client.post("/api/departamentos/", self.departamento_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Departamento.objects.count(), 1)
        self.assertEqual(response.data["nombre"], "Historia")
        self.assertEqual(response.data["facultad"], self.facultad.pk)
        self.assertTrue(
            UnidadOrganizacional.objects.filter(departamento_legacy_id=response.data["id"]).exists()
        )


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class UnidadOrganizacionalViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username="admin_unidades",
            email="admin_unidades@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        self.tipo, _ = TipoUnidadOrganizacional.objects.get_or_create(nombre="Recinto")
        self.root = UnidadOrganizacional.objects.create(nombre="Sede", tipo=self.tipo)

    def test_crear_unidad_con_padre(self):
        response = self.client.post(
            "/api/unidades-organizacionales/",
            {
                "nombre": "Recinto Santiago",
                "descripcion": "Campus regional",
                "tipo": self.tipo.pk,
                "unidad_padre": self.root.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["unidad_padre"], self.root.pk)
        self.assertEqual(response.data["tipo_nombre"], "Recinto")

    def test_filtrar_unidades_por_padre_tipo_y_estado(self):
        child = UnidadOrganizacional.objects.create(
            nombre="Recinto Este",
            tipo=self.tipo,
            unidad_padre=self.root,
            activa=False,
        )
        response = self.client.get(
            f"/api/unidades-organizacionales/?unidad_padre={self.root.pk}&tipo={self.tipo.pk}&activa=false"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([unit["id"] for unit in response.data["results"]], [child.pk])

    def test_actualizar_unidad_no_permite_ciclos(self):
        child = UnidadOrganizacional.objects.create(
            nombre="Subunidad",
            tipo=self.tipo,
            unidad_padre=self.root,
        )
        response = self.client.patch(
            f"/api/unidades-organizacionales/{self.root.pk}/",
            {"unidad_padre": child.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("unidad_padre", response.data)

    def test_actualizar_unidad_permite_quitar_padre(self):
        child = UnidadOrganizacional.objects.create(
            nombre="Subunidad",
            tipo=self.tipo,
            unidad_padre=self.root,
        )
        response = self.client.patch(
            f"/api/unidades-organizacionales/{child.pk}/",
            {"unidad_padre": None},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        child.refresh_from_db()
        self.assertIsNone(child.unidad_padre_id)
