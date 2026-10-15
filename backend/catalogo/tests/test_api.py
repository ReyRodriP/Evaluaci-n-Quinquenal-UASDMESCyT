"""@file test_api.py
@brief Pruebas de los endpoints de solo lectura del catalogo EQ-SIDACES.
"""

import csv
import io

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from catalogo.models import (
    Componente,
    CriterioMarco,
    Dimension,
    Estandar,
    IndicadorMarco,
    VersionMarcoEvaluacion,
)
from catalogo.views import CABECERA_CSV

User = get_user_model()

RUTAS = ("versiones", "dimensiones", "componentes", "criterios", "estandares", "indicadores")


@override_settings(
    PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"],
)
class BaseCatalogoApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.version = VersionMarcoEvaluacion.objects.create(
            nombre="EQ-SIDACES-2019-Res27-2019",
            slug="eq-sidaces-2019-res27-2019",
            fuente="docs/Estándares Marco EQ-SIDACES (Versión Final).pdf",
            nota="Solo registros confirmados.",
        )
        cls.dim = Dimension.objects.create(
            version_marco=cls.version, codigo="VI", nombre="PERSONAL ACADÉMICO", orden=6
        )
        cls.comp = Componente.objects.create(
            version_marco=cls.version,
            dimension=cls.dim,
            codigo="6.1",
            codigo_completo="6.1",
            nombre="Plan de desarrollo del personal académico",
            orden=1,
        )
        cls.cri = CriterioMarco.objects.create(
            version_marco=cls.version,
            componente=cls.comp,
            codigo="6.1.1",
            codigo_completo="6.1.1",
            nombre="Plan de desarrollo del personal académico",
            orden=1,
        )
        cls.std = Estandar.objects.create(
            version_marco=cls.version,
            criterio_marco=cls.cri,
            codigo="6.1.1.1",
            codigo_completo="6.1.1.1",
            redaccion="La IES cuenta con un plan de desarrollo del personal académico.",
            orden=1,
        )
        cls.ind_sintetico = IndicadorMarco.objects.create(
            version_marco=cls.version,
            estandar=cls.std,
            codigo="6.1.1.1-IND-01",
            codigo_completo="6.1.1.1-IND-01",
            redaccion_oficial="El plan de desarrollo del personal académico existe.",
            orden=1,
        )

    def setUp(self):
        self.client = APIClient()
        self.usuario = User.objects.create_user(
            username="api_test", email="api_test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.usuario)


class CatalogoApiTests(BaseCatalogoApi):
    def test_requiere_autenticacion(self):
        anonimo = APIClient()
        for ruta in RUTAS:
            with self.subTest(ruta=ruta):
                respuesta = anonimo.get(f"/api/catalogo/{ruta}/")
                self.assertIn(
                    respuesta.status_code,
                    (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
                )

    def test_versiones_lista_y_conteos(self):
        respuesta = self.client.get("/api/catalogo/versiones/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos["count"], 1)
        item = datos["results"][0]
        self.assertEqual(item["slug"], self.version.slug)
        self.assertFalse(item["activo"])
        self.assertEqual(item["conteos"]["dimensiones"], 1)
        self.assertEqual(item["conteos"]["indicadores_marco"], 1)

    def test_dimensiones_filtradas_por_version_slug(self):
        respuesta = self.client.get(
            "/api/catalogo/dimensiones/", {"version": self.version.slug}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos["count"], 1)
        self.assertEqual(datos["results"][0]["codigo"], "VI")
        self.assertEqual(len(datos["results"][0]["componentes"]), 1)

    def test_dimensiones_version_inexistente_devuelve_400(self):
        respuesta = self.client.get("/api/catalogo/dimensiones/", {"version": "no-existe"})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("version", respuesta.json())

    def test_componentes_filtrados_por_dimension(self):
        respuesta = self.client.get(
            "/api/catalogo/componentes/", {"dimension": self.dim.pk}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos["count"], 1)
        item = datos["results"][0]
        self.assertEqual(item["codigo_completo"], "6.1")
        self.assertEqual(item["dimension"]["codigo"], "VI")
        self.assertEqual(item["estado_revision"], "confirmado")

    def test_filtro_dimension_invalido_devuelve_400(self):
        for valor in ("9999", "abc"):
            with self.subTest(valor=valor):
                respuesta = self.client.get(
                    "/api/catalogo/componentes/", {"dimension": valor}
                )
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("dimension", respuesta.json())

    def test_criterios_y_estandares_jerarquia(self):
        respuesta = self.client.get(
            "/api/catalogo/criterios/", {"componente": self.comp.pk}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.json()["count"], 1)
        respuesta = self.client.get(
            "/api/catalogo/estandares/", {"criterio": self.cri.pk}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos["count"], 1)
        self.assertEqual(datos["results"][0]["codigo_completo"], "6.1.1.1")
        self.assertEqual(datos["results"][0]["componente"]["codigo"], "6.1")

    def test_indicadores_filtrados_por_estandar(self):
        respuesta = self.client.get(
            "/api/catalogo/indicadores/", {"estandar": self.std.pk}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos["count"], 1)
        item = datos["results"][0]
        self.assertEqual(item["codigo"], "6.1.1.1-IND-01")
        self.assertTrue(item["codigo_sintetico"])
        self.assertIsNone(item["codigo_oficial"])
        self.assertEqual(item["estado_revision"], "confirmado")
        self.assertEqual(item["estandar_codigo"], "6.1.1.1")

    def test_codigo_no_sintetico_no_se_marca_como_sintetico(self):
        otro = IndicadorMarco.objects.create(
            version_marco=self.version,
            estandar=self.std,
            codigo="OTRO-CODIGO",
            codigo_completo="OTRO-CODIGO",
            redaccion_oficial="Indicador con codigo heredado.",
            orden=2,
        )
        respuesta = self.client.get(f"/api/catalogo/indicadores/{otro.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(respuesta.json()["codigo_sintetico"])

    def test_detalle_estandar_incluye_indicadores_y_breadcrumb(self):
        respuesta = self.client.get(f"/api/catalogo/estandares/{self.std.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos["dimension"]["codigo"], "VI")
        self.assertEqual(datos["componente"]["codigo"], "6.1")
        self.assertEqual(datos["criterio"]["codigo"], "6.1.1")
        self.assertEqual(len(datos["indicadores"]), 1)
        self.assertEqual(datos["indicadores"][0]["codigo"], "6.1.1.1-IND-01")

    def test_detalle_inexistente_devuelve_404(self):
        for ruta in ("versiones", "dimensiones", "componentes", "criterios", "estandares", "indicadores"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(f"/api/catalogo/{ruta}/99999/")
                self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_escrituras_no_permitidas(self):
        for ruta in ("versiones", "dimensiones", "componentes", "criterios", "estandares", "indicadores"):
            with self.subTest(ruta=ruta):
                respuesta = self.client.post(f"/api/catalogo/{ruta}/", {}, format="json")
                self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_no_modifica_datos(self):
        antes = {
            "versiones": VersionMarcoEvaluacion.objects.count(),
            "dimensiones": Dimension.objects.count(),
            "componentes": Componente.objects.count(),
            "criterios": CriterioMarco.objects.count(),
            "estandares": Estandar.objects.count(),
            "indicadores": IndicadorMarco.objects.count(),
        }
        self.client.get("/api/catalogo/versiones/")
        self.client.get("/api/catalogo/dimensiones/", {"version": self.version.slug})
        self.client.get(f"/api/catalogo/estandares/{self.std.pk}/")
        despues = {
            "versiones": VersionMarcoEvaluacion.objects.count(),
            "dimensiones": Dimension.objects.count(),
            "componentes": Componente.objects.count(),
            "criterios": CriterioMarco.objects.count(),
            "estandares": Estandar.objects.count(),
            "indicadores": IndicadorMarco.objects.count(),
        }
        self.assertEqual(antes, despues)

    def test_unicidad_version_y_activa_sin_alterar(self):
        respuesta = self.client.get(f"/api/catalogo/versiones/{self.version.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(respuesta.json()["activo"])
        self.assertEqual(VersionMarcoEvaluacion.objects.filter(activo=True).count(), 0)

    def test_lista_vacia_para_version_sin_dimensiones(self):
        otra = VersionMarcoEvaluacion.objects.create(
            nombre="Version vacia", slug="version-vacia"
        )
        respuesta = self.client.get("/api/catalogo/dimensiones/", {"version": otra.slug})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        datos = respuesta.json()
        self.assertEqual(datos["count"], 0)
        self.assertEqual(datos["results"], [])

    def test_recuperacion_tras_error_de_filtro(self):
        mala = self.client.get("/api/catalogo/dimensiones/", {"version": "no-existe"})
        self.assertEqual(mala.status_code, status.HTTP_400_BAD_REQUEST)
        buena = self.client.get(
            "/api/catalogo/dimensiones/", {"version": self.version.slug}
        )
        self.assertEqual(buena.status_code, status.HTTP_200_OK)
        self.assertEqual(buena.json()["count"], 1)


class CatalogoExportarTests(BaseCatalogoApi):
    RUTA = "/api/catalogo/exportar/"

    def _filas(self, respuesta):
        texto = respuesta.content.decode("utf-8-sig")
        return list(csv.reader(io.StringIO(texto)))

    def test_requiere_autenticacion(self):
        anonimo = APIClient()
        respuesta = anonimo.get(self.RUTA, {"version": self.version.slug})
        self.assertIn(
            respuesta.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_exporta_arbol_completo_en_orden_jerarquico(self):
        respuesta = self.client.get(self.RUTA, {"version": self.version.slug})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertTrue(respuesta["Content-Type"].startswith("text/csv"))
        self.assertTrue(respuesta.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn(
            f'filename="arbol_eq_sidaces_{self.version.slug}.csv"',
            respuesta["Content-Disposition"],
        )
        filas = self._filas(respuesta)
        self.assertEqual(filas[0], list(CABECERA_CSV))
        self.assertEqual(len(filas), 6)
        self.assertEqual(
            [fila[0] for fila in filas[1:]],
            ["dimension", "componente", "criterio", "estandar", "indicador"],
        )
        for fila in filas[1:]:
            self.assertEqual(fila[1], self.version.slug)
            self.assertEqual(fila[9], "confirmado")
        indicador = filas[-1]
        self.assertEqual(indicador[2], "VI")
        self.assertEqual(indicador[3], "6.1")
        self.assertEqual(indicador[4], "6.1.1")
        self.assertEqual(indicador[5], "6.1.1.1")
        self.assertEqual(indicador[6], "6.1.1.1-IND-01")
        self.assertEqual(indicador[8], "true")

    def test_version_requerida_devuelve_400(self):
        respuesta = self.client.get(self.RUTA)
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("version", respuesta.json())

    def test_version_inexistente_devuelve_400(self):
        respuesta = self.client.get(self.RUTA, {"version": "no-existe"})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("version", respuesta.json())

    def test_dimension_invalida_devuelve_400(self):
        for valor in ("abc", "9999"):
            with self.subTest(valor=valor):
                respuesta = self.client.get(
                    self.RUTA, {"version": self.version.slug, "dimension": valor}
                )
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("dimension", respuesta.json())

    def test_filtro_dimension_restringe_la_rama(self):
        otra = Dimension.objects.create(
            version_marco=self.version, codigo="I", nombre="OTRA", orden=1
        )
        completa = self._filas(
            self.client.get(self.RUTA, {"version": self.version.slug})
        )
        self.assertEqual(len(completa), 7)
        rama = self._filas(
            self.client.get(
                self.RUTA, {"version": self.version.slug, "dimension": self.dim.pk}
            )
        )
        self.assertEqual(len(rama), 6)
        self.assertTrue(all(fila[2] == "VI" for fila in rama[1:]))
        vacia = self._filas(
            self.client.get(
                self.RUTA, {"version": self.version.slug, "dimension": otra.pk}
            )
        )
        self.assertEqual(len(vacia), 2)
        self.assertEqual(vacia[1][0], "dimension")

    def test_post_no_permitido(self):
        respuesta = self.client.post(self.RUTA, {"version": self.version.slug}, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_no_modifica_datos(self):
        modelos = (
            VersionMarcoEvaluacion,
            Dimension,
            Componente,
            CriterioMarco,
            Estandar,
            IndicadorMarco,
        )
        antes = [modelo.objects.count() for modelo in modelos]
        self.client.get(self.RUTA, {"version": self.version.slug})
        despues = [modelo.objects.count() for modelo in modelos]
        self.assertEqual(antes, despues)

    def test_recuperacion_tras_error_de_filtro(self):
        mala = self.client.get(self.RUTA, {"version": "no-existe"})
        self.assertEqual(mala.status_code, status.HTTP_400_BAD_REQUEST)
        buena = self.client.get(self.RUTA, {"version": self.version.slug})
        self.assertEqual(buena.status_code, status.HTTP_200_OK)
