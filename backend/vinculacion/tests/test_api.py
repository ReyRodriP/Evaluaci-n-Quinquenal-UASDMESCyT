"""Pruebas de la API REST de vinculacion.

Cobertura: 401/403/404/405/400, alcance por rol y ámbito, creación de
propuestas, sellos del servidor, transiciones, duplicados vivos, conflicto de
unicidad controlado, filtros de versión sin conmutar a la activa, uso de los
métodos de dominio en las rutas de escritura y ausencia de asignación de
permisos a grupos.
"""

from unittest import mock

from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Usuario
from auditoria.models import Auditoria
from catalogo.models import Componente, CriterioMarco, Dimension, Estandar, IndicadorMarco, VersionMarcoEvaluacion
from evaluation.models import Asignacion, Criterio, EstadoAsignacion, Indicador, Periodo
from organization.models import AmbitoEvaluacion, PerfilUsuario, TipoUnidadOrganizacional, UnidadOrganizacional
from vinculacion.models import Correspondencia, EstadoCorrespondencia
from vinculacion.validaciones import validar_destino_en_version

from .test_models import _crear_cadena_marco

URL = "/api/vinculacion/correspondencias/"


class BaseApiVinculacion(TestCase):
    """Usuarios por rol, unidades, marco de dos versiones y correspondencias base."""

    @classmethod
    def setUpTestData(cls):
        permisos = Permission.objects.filter(codename__in=["view_correspondencia", "add_correspondencia", "change_correspondencia"])
        cls.permiso_view = permisos.get(codename="view_correspondencia")
        cls.permiso_add = permisos.get(codename="add_correspondencia")
        cls.permiso_change = permisos.get(codename="change_correspondencia")

        cls.admin = Usuario.objects.create_user(username="admin_api", email="admin@x.org", password="x")
        cls.admin.user_permissions.add(cls.permiso_view, cls.permiso_add, cls.permiso_change)
        cls.admin.groups.add(Group.objects.create(name="Administrador General"))

        cls.coord = Usuario.objects.create_user(username="coord_api", email="coord@x.org", password="x")
        cls.coord.user_permissions.add(cls.permiso_view, cls.permiso_add, cls.permiso_change)
        cls.coord.groups.add(Group.objects.create(name="Coordinador Quinquenal"))

        cls.tecnico = Usuario.objects.create_user(username="tecnico_api", email="tec@x.org", password="x")
        cls.tecnico.user_permissions.add(cls.permiso_view)
        cls.tecnico.groups.add(Group.objects.create(name="Responsable Departamental"))

        cls.externo = Usuario.objects.create_user(username="externo_api", email="ext@x.org", password="x")
        cls.externo.user_permissions.add(cls.permiso_view)
        cls.externo.groups.add(Group.objects.create(name="Evaluador Externo"))

        cls.sin_permiso = Usuario.objects.create_user(username="sinperm_api", email="sp@x.org", password="x")

        cls.tipo = TipoUnidadOrganizacional.objects.create(nombre="Departamento API")
        cls.unidad_a = UnidadOrganizacional.objects.create(nombre="Unidad A", tipo=cls.tipo)
        cls.unidad_b = UnidadOrganizacional.objects.create(nombre="Unidad B", tipo=cls.tipo)
        PerfilUsuario.objects.create(usuario=cls.tecnico, unidad_organizacional=cls.unidad_a)

        cls.periodo = Periodo.objects.create(
            nombre="Periodo API",
            fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate().replace(year=2027),
        )
        AmbitoEvaluacion.objects.create(
            usuario=cls.externo, unidad_organizacional=cls.unidad_a, periodo=cls.periodo, activo=True
        )

        cls.criterio_a = Criterio.objects.create(nombre="Criterio A", periodo=cls.periodo)
        cls.indicador_a = Indicador.objects.create(nombre="Indicador A", criterio=cls.criterio_a)
        Asignacion.objects.create(
            indicador=cls.indicador_a,
            unidad_responsable=cls.unidad_a,
            periodo=cls.periodo,
            estado=EstadoAsignacion.APROBADO,
        )
        cls.criterio_b = Criterio.objects.create(nombre="Criterio B", periodo=cls.periodo)
        cls.indicador_b = Indicador.objects.create(nombre="Indicador B", criterio=cls.criterio_b)
        Asignacion.objects.create(
            indicador=cls.indicador_b,
            unidad_responsable=cls.unidad_b,
            periodo=cls.periodo,
            estado=EstadoAsignacion.APROBADO,
        )

        cls.version_a = VersionMarcoEvaluacion.objects.create(nombre="Marco A", slug="marco-a")
        cls.version_b = VersionMarcoEvaluacion.objects.create(nombre="Marco B", slug="marco-b")
        cls.dim_a, cls.std_a, cls.ind_marco_a = _crear_cadena_marco(cls.version_a)
        cls.dim_a2, cls.std_a2, cls.ind_marco_a2 = _crear_cadena_marco(cls.version_a, codigo="II", nombre="Dim II")
        cls.dim_b, cls.std_b, cls.ind_marco_b = _crear_cadena_marco(cls.version_b)

        cls.corr_a = Correspondencia.crear_propuesta(
            actor=cls.admin, version_marco=cls.version_a, criterio_op=cls.criterio_a, estandar=cls.std_a
        )
        cls.corr_b = Correspondencia.crear_propuesta(
            actor=cls.admin, version_marco=cls.version_a, criterio_op=cls.criterio_b, estandar=cls.std_a2
        )

    def cliente(self, usuario=None):
        client = APIClient()
        if usuario is not None:
            client.force_authenticate(user=usuario)
        return client

    def resultados(self, response):
        return response.data.get("results", response.data)

    def payload_creacion(self, **kwargs):
        datos = {"version_marco": self.version_a.pk, "criterio_op": self.criterio_a.pk, "estandar": self.std_a.pk}
        datos.update(kwargs)
        return datos

    def obtener_corr_a(self):
        """Refresca corr_a desde la BD (setUpTestData deja instancias en memoria)."""
        return Correspondencia.objects.get(pk=self.corr_a.pk)


class PermisosBaseTests(BaseApiVinculacion):
    def test_anonimo_401(self):
        respuesta = self.cliente().get(URL)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_autenticado_sin_permiso_403(self):
        respuesta = self.cliente(self.sin_permiso).get(URL)
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_grupos_sin_permisos_de_vinculacion(self):
        codenames = ["view_correspondencia", "add_correspondencia", "change_correspondencia", "delete_correspondencia"]
        asignados = Group.objects.filter(permissions__codename__in=codenames)
        self.assertEqual(asignados.count(), 0)

    def test_escritura_tecnico_403(self):
        respuesta = self.cliente(self.tecnico).post(URL, self.payload_creacion(estandar=self.std_a2.pk), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_escritura_externo_403(self):
        respuesta = self.cliente(self.externo).post(URL, self.payload_creacion(estandar=self.std_a2.pk), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


class LecturaTests(BaseApiVinculacion):
    def test_admin_lista_y_detalla(self):
        client = self.cliente(self.admin)
        lista = client.get(URL)
        self.assertEqual(lista.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self.resultados(lista)), 2)
        detalle = client.get(f"{URL}{self.corr_a.pk}/")
        self.assertEqual(detalle.status_code, status.HTTP_200_OK)
        self.assertEqual(detalle.data["origen"]["nivel"], "criterio")
        self.assertEqual(detalle.data["destino"]["nivel"], "estandar")

    def test_tecnico_ve_solo_su_unidad(self):
        lista = self.cliente(self.tecnico).get(URL)
        ids = {fila["id"] for fila in self.resultados(lista)}
        self.assertEqual(ids, {self.corr_a.pk})

    def test_tecnico_detalla_fuera_de_alcance_404(self):
        respuesta = self.cliente(self.tecnico).get(f"{URL}{self.corr_b.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_externo_ve_solo_aprobado_de_su_ambito(self):
        lista = self.cliente(self.externo).get(URL)
        ids = {fila["id"] for fila in self.resultados(lista)}
        self.assertEqual(ids, {self.corr_a.pk})

    def test_filtro_por_version_usa_version_de_la_fila(self):
        client = self.cliente(self.admin)
        corr_b = Correspondencia.crear_propuesta(
            actor=self.admin, version_marco=self.version_b, criterio_op=self.criterio_a, estandar=self.std_b
        )
        lista = client.get(f"{URL}?version=marco-a")
        ids = {fila["id"] for fila in self.resultados(lista)}
        self.assertIn(self.corr_a.pk, ids)
        self.assertNotIn(corr_b.pk, ids)
        lista_b = client.get(f"{URL}?version={self.version_b.pk}")
        ids_b = {fila["id"] for fila in self.resultados(lista_b)}
        self.assertEqual(ids_b, {corr_b.pk})

    def test_filtros_estado_y_origen(self):
        client = self.cliente(self.admin)
        self.obtener_corr_a().confirmar(self.admin)
        lista = client.get(f"{URL}?estado=confirmada")
        ids = {fila["id"] for fila in self.resultados(lista)}
        self.assertEqual(ids, {self.corr_a.pk})
        lista_criterio = client.get(f"{URL}?criterio_op={self.criterio_a.pk}")
        ids_criterio = {fila["id"] for fila in self.resultados(lista_criterio)}
        self.assertEqual(ids_criterio, {self.corr_a.pk})

    def test_filtros_invalidos_400(self):
        client = self.cliente(self.admin)
        self.assertEqual(client.get(f"{URL}?version=inexistente").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(client.get(f"{URL}?estado=raro").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(client.get(f"{URL}?criterio_op=abc").status_code, status.HTTP_400_BAD_REQUEST)

    def test_contexto_criterio_e_indicador(self):
        client = self.cliente(self.admin)
        contexto_c = client.get(f"/api/vinculacion/contexto/criterio/{self.criterio_a.pk}/")
        self.assertEqual(contexto_c.status_code, status.HTTP_200_OK)
        self.assertEqual(len(contexto_c.data["correspondencias"]), 1)
        contexto_i = client.get(f"/api/vinculacion/contexto/indicador/{self.indicador_a.pk}/")
        self.assertEqual(contexto_i.status_code, status.HTTP_200_OK)
        self.assertEqual(contexto_i.data["origen"]["nivel"], "indicador")

    def test_contexto_inexistente_404(self):
        respuesta = self.cliente(self.admin).get("/api/vinculacion/contexto/criterio/999999/")
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_contexto_fuera_de_alcance_404(self):
        respuesta = self.cliente(self.tecnico).get(f"/api/vinculacion/contexto/criterio/{self.criterio_b.pk}/")
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)


class CreacionTests(BaseApiVinculacion):
    def test_crear_propuesta_admin_201(self):
        respuesta = self.cliente(self.admin).post(URL, self.payload_creacion(estandar=self.std_a2.pk), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["estado"], EstadoCorrespondencia.PROPUESTA)
        self.assertEqual(respuesta.data["creado_por"], "admin_api")
        self.assertIsNone(respuesta.data["confirmado_por"])

    def test_crear_propuesta_coordinador_201(self):
        respuesta = self.cliente(self.coord).post(URL, self.payload_creacion(estandar=self.std_a2.pk), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_crear_destino_otra_version_400(self):
        respuesta = self.cliente(self.admin).post(
            URL, self.payload_creacion(estandar=None, indicador_marco=self.ind_marco_b.pk), format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_origen_o_destino_inexistente_400(self):
        client = self.cliente(self.admin)
        self.assertEqual(
            client.post(URL, self.payload_creacion(criterio_op=999999), format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            client.post(URL, self.payload_creacion(estandar=999999), format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_crear_combinaciones_invalidas_400(self):
        client = self.cliente(self.admin)
        self.assertEqual(
            client.post(URL, self.payload_creacion(criterio_op=None, indicador_op=None), format="json").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            client.post(
                URL,
                self.payload_creacion(indicador_op=self.indicador_a.pk),
                format="json",
            ).status_code,
            status.HTTP_400_BAD_REQUEST,  # doble origen: criterio_op + indicador_op
        )
        self.assertEqual(
            client.post(URL, self.payload_creacion(dimension=self.dim_a.pk), format="json").status_code,
            status.HTTP_400_BAD_REQUEST,  # doble destino: estandar + dimension
        )

    def test_crear_duplicado_vivo_400(self):
        client = self.cliente(self.admin)
        self.assertEqual(client.post(URL, self.payload_creacion(), format="json").status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_tras_rechazo_201(self):
        client = self.cliente(self.admin)
        self.obtener_corr_a().rechazar(self.admin, "No corresponde")
        respuesta = client.post(URL, self.payload_creacion(), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_sellos_manipulados_ignorados(self):
        datos = self.payload_creacion(
            estandar=self.std_a2.pk,
            estado="confirmada",
            creado_por="otro",
            confirmado_por="hack",
            fecha_confirmacion="2020-01-01T00:00:00Z",
            rechazado_por="hack",
        )
        respuesta = self.cliente(self.admin).post(URL, datos, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["estado"], EstadoCorrespondencia.PROPUESTA)
        self.assertEqual(respuesta.data["creado_por"], "admin_api")
        self.assertIsNone(respuesta.data["confirmado_por"])
        self.assertIsNone(respuesta.data["fecha_confirmacion"])

    def test_conflicto_unicidad_controlado_400(self):
        client = self.cliente(self.admin)
        with mock.patch.object(Correspondencia, "full_clean", return_value=None):
            with mock.patch.object(Correspondencia, "save", side_effect=IntegrityError("unicidad")):
                respuesta = client.post(URL, self.payload_creacion(), format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)


class TransicionesApiTests(BaseApiVinculacion):
    def test_confirmar_200(self):
        respuesta = self.cliente(self.admin).post(f"{URL}{self.corr_a.pk}/confirmar/", {}, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["estado"], EstadoCorrespondencia.CONFIRMADA)
        self.assertEqual(respuesta.data["confirmado_por"], "admin_api")
        self.assertIsNotNone(respuesta.data["fecha_confirmacion"])

    def test_rechazar_con_comentario_200(self):
        respuesta = self.cliente(self.admin).post(
            f"{URL}{self.corr_a.pk}/rechazar/", {"comentario": "No aplica"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["estado"], EstadoCorrespondencia.RECHAZADA)

    def test_rechazar_sin_comentario_400(self):
        respuesta = self.cliente(self.admin).post(f"{URL}{self.corr_a.pk}/rechazar/", {}, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_desconfirmar_con_comentario_200(self):
        self.obtener_corr_a().confirmar(self.admin)
        respuesta = self.cliente(self.admin).post(
            f"{URL}{self.corr_a.pk}/desconfirmar/", {"comentario": "Revisión"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["estado"], EstadoCorrespondencia.PROPUESTA)
        self.assertIsNone(respuesta.data["confirmado_por"])

    def test_desconfirmar_sin_comentario_400(self):
        self.obtener_corr_a().confirmar(self.admin)
        respuesta = self.cliente(self.admin).post(f"{URL}{self.corr_a.pk}/desconfirmar/", {}, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transiciones_invalidas_400(self):
        client = self.cliente(self.admin)
        corr = self.obtener_corr_a()
        corr.confirmar(self.admin)
        self.assertEqual(client.post(f"{URL}{self.corr_a.pk}/rechazar/", {"comentario": "x"}, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        corr = self.obtener_corr_a()
        corr.desconfirmar(self.admin, "revisión")
        corr = self.obtener_corr_a()
        corr.rechazar(self.admin, "no")
        self.assertEqual(client.post(f"{URL}{self.corr_a.pk}/confirmar/", {}, format="json").status_code, status.HTTP_400_BAD_REQUEST)

    def test_transicion_auditoria_registrada(self):
        self.cliente(self.admin).post(f"{URL}{self.corr_a.pk}/confirmar/", {}, format="json")
        acciones = Auditoria.objects.filter(modelo="Correspondencia", registro_id=self.corr_a.pk).values_list(
            "accion", flat=True
        )
        self.assertIn("confirmar correspondencia", acciones)

    def test_metodos_de_dominio_en_rutas_de_escritura(self):
        client = self.cliente(self.admin)
        with mock.patch.object(Correspondencia, "crear_propuesta", wraps=Correspondencia.crear_propuesta) as espia_crear:
            client.post(URL, self.payload_creacion(estandar=self.std_a2.pk), format="json")
            espia_crear.assert_called_once()
        with mock.patch.object(Correspondencia, "confirmar", autospec=True, wraps=Correspondencia.confirmar) as espia_confirmar:
            client.post(f"{URL}{self.corr_a.pk}/confirmar/", {}, format="json")
            espia_confirmar.assert_called_once()
        with mock.patch.object(Correspondencia, "rechazar", autospec=True, wraps=Correspondencia.rechazar) as espia_rechazar:
            client.post(f"{URL}{self.corr_b.pk}/rechazar/", {"comentario": "x"}, format="json")
            espia_rechazar.assert_called_once()

    def test_metodos_http_restringidos(self):
        client = self.cliente(self.admin)
        self.assertEqual(client.patch(f"{URL}{self.corr_a.pk}/", {"estado": "confirmada"}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(client.put(f"{URL}{self.corr_a.pk}/", {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(client.delete(f"{URL}{self.corr_a.pk}/").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ValidacionCentralTests(BaseApiVinculacion):
    def test_serializador_invoca_validacion_de_version(self):
        from rest_framework.exceptions import ValidationError as DRFValidationError

        from vinculacion.serializers import CorrespondenciaCreacionSerializer

        serializer = CorrespondenciaCreacionSerializer(
            data={
                "version_marco": self.version_a.pk,
                "criterio_op": self.criterio_a.pk,
                "indicador_marco": self.ind_marco_b.pk,
            }
        )
        with self.assertRaises(DRFValidationError):
            serializer.is_valid(raise_exception=True)

    def test_helper_reutilizable_directo(self):
        with self.assertRaises(Exception):
            validar_destino_en_version(self.version_a.pk, estandar=self.std_b)


class IndicadorMultiUnidadTests(BaseApiVinculacion):
    """Un indicador con asignaciones en distintas unidades solo da contexto autorizado.

    La decisión de acceso se toma sobre la asignación (unidad + período + estado
    según el rol), nunca sobre el indicador aislado.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.criterio_multi = Criterio.objects.create(nombre="Criterio Multi", periodo=cls.periodo)
        cls.indicador_multi = Indicador.objects.create(nombre="Indicador Multi", criterio=cls.criterio_multi)
        Asignacion.objects.create(
            indicador=cls.indicador_multi,
            unidad_responsable=cls.unidad_a,
            periodo=cls.periodo,
            estado=EstadoAsignacion.APROBADO,
        )
        Asignacion.objects.create(
            indicador=cls.indicador_multi,
            unidad_responsable=cls.unidad_b,
            periodo=cls.periodo,
            estado=EstadoAsignacion.PENDIENTE,
        )
        cls.corr_multi = Correspondencia.crear_propuesta(
            actor=cls.admin,
            version_marco=cls.version_a,
            criterio_op=None,
            indicador_op=cls.indicador_multi,
            estandar=cls.std_a2,
        )

    def test_contexto_multi_para_unidad_propia(self):
        respuesta = self.cliente(self.tecnico).get(
            f"/api/vinculacion/contexto/indicador/{self.indicador_multi.pk}/"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data["correspondencias"]), 1)

    def test_contexto_multi_para_externo_aprobado_en_ambito(self):
        respuesta = self.cliente(self.externo).get(
            f"/api/vinculacion/contexto/indicador/{self.indicador_multi.pk}/"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_contexto_multi_unidad_b_y_oculto_en_unidad_a(self):
        usuario_b = Usuario.objects.create_user(username="tec_b_api", email="tecb@x.org", password="x")
        usuario_b.groups.add(Group.objects.get(name="Responsable Departamental"))
        usuario_b.user_permissions.add(self.permiso_view)
        PerfilUsuario.objects.create(usuario=usuario_b, unidad_organizacional=self.unidad_b)
        client = self.cliente(usuario_b)
        contexto = client.get(f"/api/vinculacion/contexto/indicador/{self.indicador_multi.pk}/")
        self.assertEqual(contexto.status_code, status.HTTP_200_OK)
        self.assertEqual(len(contexto.data["correspondencias"]), 1)
        # El resto (orígenes con asignaciones solo en la unidad A) queda oculto;
        # corr_b sí es visible para unidad B (su origen tiene asignación allí).
        lista = client.get(URL)
        ids = {fila["id"] for fila in self.resultados(lista)}
        self.assertEqual(ids, {self.corr_b.pk, self.corr_multi.pk})
        oculto = client.get(f"/api/vinculacion/contexto/indicador/{self.indicador_a.pk}/")
        self.assertEqual(oculto.status_code, status.HTTP_404_NOT_FOUND)
