from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from evaluation.models import Criterio, Indicador, Periodo
from organization.models import Departamento, Facultad

User = get_user_model()


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class SearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/search/"
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
        self.periodo = Periodo.objects.create(
            nombre="Periodo 2025",
            fecha_inicio="2025-01-01",
            fecha_fin="2025-12-31",
        )
        self.criterio = Criterio.objects.create(
            nombre="Criterio Investigacion",
            periodo=self.periodo,
        )
        self.indicador = Indicador.objects.create(
            nombre="Indicador Publicaciones",
            criterio=self.criterio,
            activo=True,
        )

    def test_search_requires_auth(self):
        response = self.client.get(self.url, {"q": "test"})
        self.assertEqual(response.status_code, 401)

    def test_search_returns_results(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {"q": "Publicaciones"})
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn("indicadores", data)
        self.assertIn("departamentos", data)
        self.assertIn("facultades", data)
        self.assertIn("criterios", data)
        self.assertIn("usuarios", data)
        self.assertGreater(len(data["indicadores"]), 0)

    def test_search_empty_query(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {"q": ""})
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["indicadores"], [])
        self.assertEqual(data["departamentos"], [])
        self.assertEqual(data["facultades"], [])
        self.assertEqual(data["criterios"], [])
        self.assertEqual(data["usuarios"], [])
