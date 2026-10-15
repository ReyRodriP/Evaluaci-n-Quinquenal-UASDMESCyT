from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .test_api import CatalogoApiTests


class DiagTests(TestCase):
    def test_diag(self):
        CatalogoApiTests.setUpTestData()
        u = get_user_model().objects.create_user("diag", "d@x.com", "x")
        c = APIClient()
        c.force_authenticate(u)
        v = CatalogoApiTests.version.slug
        for url in (
            "/api/catalogo/versiones/",
            "/api/catalogo/dimensiones/",
            f"/api/catalogo/dimensiones/?version={v}",
            "/api/catalogo/dimensiones/?version=no-existe",
            "/api/catalogo/dimensiones/99999/",
        ):
            r = c.get(url)
            print("DIAG", url, "->", r.status_code, r.content.decode()[:200])
