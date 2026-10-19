"""Pruebas de alcance organizacional: catálogo institucional vs datos operativos.

Bloquea la matriz vigente sin cambiarla:
- Roles internos ven el catálogo completo de Criterio/Indicador (referencia institucional).
- Evaluador Externo solo ve el catálogo ligado a asignaciones aprobadas de su ámbito.
- El detalle de catálogo es consistente con la lista para cada rol.
- La manipulación de IDs en detalle de Asignacion responde 404 fuera del alcance del rol.
"""

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Usuario
from evaluation.models import Asignacion, Criterio, EstadoAsignacion, Indicador, Periodo
from organization.models import AmbitoEvaluacion, PerfilUsuario, TipoUnidadOrganizacional, UnidadOrganizacional


class BaseAlcanceCatalogo(TestCase):
    """Usuarios de rol, unidades, periodo activo, catálogo y asignaciones base."""

    @classmethod
    def setUpTestData(cls):
        lectura = Permission.objects.filter(
            codename__in=["view_criterio", "view_indicador", "view_asignacion"]
        )
        cls.view_criterio = lectura.get(codename="view_criterio")
        cls.view_indicador = lectura.get(codename="view_indicador")
        cls.view_asignacion = lectura.get(codename="view_asignacion")

        cls.tecnico = Usuario.objects.create_user(username="tec_alc", email="tec@x.org", password="x")
        cls.tecnico.user_permissions.add(cls.view_criterio, cls.view_indicador, cls.view_asignacion)
        cls.tecnico.groups.add(Group.objects.create(name="Responsable Departamental"))

        cls.externo = Usuario.objects.create_user(username="ext_alc", email="ext@x.org", password="x")
        cls.externo.user_permissions.add(cls.view_criterio, cls.view_indicador, cls.view_asignacion)
        cls.externo.groups.add(Group.objects.create(name="Evaluador Externo"))

        cls.tipo = TipoUnidadOrganizacional.objects.create(nombre="Departamento Alcance")
        cls.unidad_a = UnidadOrganizacional.objects.create(nombre="Unidad Alc A", tipo=cls.tipo)
        cls.unidad_b = UnidadOrganizacional.objects.create(nombre="Unidad Alc B", tipo=cls.tipo)
        PerfilUsuario.objects.create(usuario=cls.tecnico, unidad_organizacional=cls.unidad_a)

        cls.periodo = Periodo.objects.create(
            nombre="Periodo Alcance",
            fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate().replace(year=2027),
        )
        AmbitoEvaluacion.objects.create(
            usuario=cls.externo, unidad_organizacional=cls.unidad_a, periodo=cls.periodo, activo=True
        )

        cls.criterio_a = Criterio.objects.create(nombre="Criterio Alc A", periodo=cls.periodo)
        cls.indicador_a = Indicador.objects.create(nombre="Indicador Alc A", criterio=cls.criterio_a)
        cls.asig_a = Asignacion.objects.create(
            indicador=cls.indicador_a,
            unidad_responsable=cls.unidad_a,
            periodo=cls.periodo,
            estado=EstadoAsignacion.APROBADO,
        )

        cls.criterio_b = Criterio.objects.create(nombre="Criterio Alc B", periodo=cls.periodo)
        cls.indicador_b = Indicador.objects.create(nombre="Indicador Alc B", criterio=cls.criterio_b)
        cls.asig_b = Asignacion.objects.create(
            indicador=cls.indicador_b,
            unidad_responsable=cls.unidad_b,
            periodo=cls.periodo,
            estado=EstadoAsignacion.PENDIENTE,
        )

    def cliente(self, usuario):
        client = APIClient()
        client.force_authenticate(user=usuario)
        return client

    def nombres_pagina(self, respuesta):
        return [item["nombre"] for item in respuesta.data["results"]]


class AlcanceCatalogoTests(BaseAlcanceCatalogo):
    def test_responsable_ve_catalogo_completo(self):
        respuesta = self.cliente(self.tecnico).get("/api/criterios/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.nombres_pagina(respuesta), ["Criterio Alc A", "Criterio Alc B"])
        respuesta = self.cliente(self.tecnico).get("/api/indicadores/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.nombres_pagina(respuesta), ["Indicador Alc A", "Indicador Alc B"])

    def test_responsable_catalogo_completo_pero_solo_su_unidad_en_asignaciones(self):
        respuesta = self.cliente(self.tecnico).get("/api/asignaciones/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["count"], 1)
        self.assertEqual(respuesta.data["results"][0]["id"], self.asig_a.pk)

    def test_externo_ve_solo_catalogo_ligado_a_sus_aprobados(self):
        respuesta = self.cliente(self.externo).get("/api/criterios/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.nombres_pagina(respuesta), ["Criterio Alc A"])
        respuesta = self.cliente(self.externo).get("/api/indicadores/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.nombres_pagina(respuesta), ["Indicador Alc A"])

    def test_responsable_abre_detalle_de_cualquier_criterio_e_indicador(self):
        for url in (
            f"/api/criterios/{self.criterio_b.pk}/",
            f"/api/indicadores/{self.indicador_b.pk}/",
        ):
            respuesta = self.cliente(self.tecnico).get(url)
            self.assertEqual(respuesta.status_code, status.HTTP_200_OK, url)

    def test_externo_detalle_en_alcance_200(self):
        for url in (
            f"/api/criterios/{self.criterio_a.pk}/",
            f"/api/indicadores/{self.indicador_a.pk}/",
        ):
            respuesta = self.cliente(self.externo).get(url)
            self.assertEqual(respuesta.status_code, status.HTTP_200_OK, url)

    def test_externo_detalle_fuera_de_alcance_404(self):
        for url in (
            f"/api/criterios/{self.criterio_b.pk}/",
            f"/api/indicadores/{self.indicador_b.pk}/",
        ):
            respuesta = self.cliente(self.externo).get(url)
            self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND, url)


class AlcanceAsignacionDetalleTests(BaseAlcanceCatalogo):
    def test_responsable_no_abre_asignacion_de_otra_unidad_por_id(self):
        respuesta = self.cliente(self.tecnico).get(f"/api/asignaciones/{self.asig_b.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_responsable_abre_asignacion_de_su_unidad(self):
        respuesta = self.cliente(self.tecnico).get(f"/api/asignaciones/{self.asig_a.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_externo_no_abre_asignacion_no_aprobada_por_id(self):
        respuesta = self.cliente(self.externo).get(f"/api/asignaciones/{self.asig_b.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_externo_abre_asignacion_aprobada_de_su_ambito(self):
        respuesta = self.cliente(self.externo).get(f"/api/asignaciones/{self.asig_a.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
