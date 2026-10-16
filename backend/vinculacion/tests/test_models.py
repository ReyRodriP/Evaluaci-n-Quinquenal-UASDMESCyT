"""Pruebas de modelos y servicios de dominio de la app vinculacion.

Cobertura: restricciones de origen/destino exactos, unicidad de pares vivos,
re-propuesta tras rechazo, múltiples destinos por indicador operativo,
coherencia de versión, máquina de transiciones, sellos, auditoría y ausencia
de efectos sobre los módulos operativos.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import Usuario
from auditoria.models import Auditoria
from catalogo.models import (
    Componente,
    CriterioMarco,
    Dimension,
    Estandar,
    IndicadorMarco,
    VersionMarcoEvaluacion,
)
from evaluation.models import Asignacion, Criterio, Indicador, Periodo
from vinculacion.models import (
    Correspondencia,
    EstadoCorrespondencia,
    ProcedenciaCorrespondencia,
)
from vinculacion.validaciones import validar_destino_en_version


def _crear_cadena_marco(version, *, codigo="I", nombre="Dimensión I"):
    """Crea una cadena mínima Dimension → Componente → CriterioMarco → Estandar → IndicadorMarco."""
    dimension = Dimension.objects.create(version_marco=version, codigo=codigo, nombre=nombre)
    componente = Componente.objects.create(
        version_marco=version, dimension=dimension, codigo="1", codigo_completo=f"{codigo}.1", nombre="Componente"
    )
    criterio_marco = CriterioMarco.objects.create(
        version_marco=version,
        componente=componente,
        codigo="1",
        codigo_completo=f"{codigo}.1.1",
        nombre="Criterio del marco",
    )
    estandar = Estandar.objects.create(
        version_marco=version,
        criterio_marco=criterio_marco,
        codigo="1",
        codigo_completo=f"{codigo}.1.1.1",
        redaccion="Redacción del estándar",
    )
    indicador_marco = IndicadorMarco.objects.create(
        version_marco=version,
        estandar=estandar,
        codigo="1",
        codigo_completo=f"{codigo}.1.1.1-IND-01",
        redaccion_oficial="Redacción del indicador",
    )
    return dimension, estandar, indicador_marco


class BaseVinculacion(TestCase):
    """Datos aislados: usuarios operativos y dos versiones del marco."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(username="coordinador", email="coord@example.org", password="x")
        cls.otro_usuario = Usuario.objects.create_user(username="tecnico", email="tecnico@example.org", password="x")

        cls.periodo = Periodo.objects.create(
            nombre="Periodo de prueba", fecha_inicio=timezone.localdate(), fecha_fin=timezone.localdate().replace(year=2027)
        )
        cls.criterio_op = Criterio.objects.create(nombre="Criterio operativo", periodo=cls.periodo)
        cls.indicador_op = Indicador.objects.create(nombre="Indicador operativo", criterio=cls.criterio_op)

        cls.version_a = VersionMarcoEvaluacion.objects.create(nombre="Marco A", slug="marco-a")
        cls.version_b = VersionMarcoEvaluacion.objects.create(nombre="Marco B", slug="marco-b")
        cls.dim_a, cls.std_a, cls.ind_marco_a = _crear_cadena_marco(cls.version_a)
        cls.dim_a2, cls.std_a2, cls.ind_marco_a2 = _crear_cadena_marco(
            cls.version_a, codigo="II", nombre="Dimensión II"
        )
        cls.dim_b, cls.std_b, cls.ind_marco_b = _crear_cadena_marco(cls.version_b)

    def crear(self, **kwargs):
        defaults = {"actor": self.usuario, "version_marco": self.version_a, "criterio_op": self.criterio_op, "estandar": self.std_a}
        defaults.update(kwargs)
        return Correspondencia.crear_propuesta(**defaults)

    def create_directo(self, **kwargs):
        """Inserta sin full_clean para ejercitar las restricciones de la BD."""
        defaults = {"version_marco": self.version_a, "criterio_op": self.criterio_op, "estandar": self.std_a}
        defaults.update(kwargs)
        return Correspondencia.objects.create(**defaults)

    def assert_integridad(self, **kwargs):
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                self.create_directo(**kwargs)


class OrigenDestinoExactoTests(BaseVinculacion):
    def test_origen_criterio_valido(self):
        corr = self.crear()
        self.assertEqual(corr.estado, EstadoCorrespondencia.PROPUESTA)

    def test_origen_indicador_valido(self):
        corr = self.crear(criterio_op=None, indicador_op=self.indicador_op)
        self.assertEqual(corr.indicador_op, self.indicador_op)

    def test_destino_dimension_valido(self):
        corr = self.crear(estandar=None, dimension=self.dim_a)
        self.assertEqual(corr.dimension, self.dim_a)

    def test_destino_indicador_marco_valido(self):
        corr = self.crear(estandar=None, indicador_marco=self.ind_marco_a)
        self.assertEqual(corr.indicador_marco, self.ind_marco_a)

    def test_origen_doble_rechazado_bd(self):
        self.assert_integridad(criterio_op=self.criterio_op, indicador_op=self.indicador_op)

    def test_origen_ninguno_rechazado_bd(self):
        self.assert_integridad(criterio_op=None, indicador_op=None)

    def test_destino_doble_rechazado_bd(self):
        self.assert_integridad(estandar=self.std_a, dimension=self.dim_a)

    def test_destino_ninguno_rechazado_bd(self):
        self.assert_integridad(estandar=None, dimension=None, indicador_marco=None)

    def test_crear_propuesta_sin_origen_lanza_validationerror(self):
        with self.assertRaises(ValidationError):
            self.crear(criterio_op=None, indicador_op=None)

    def test_crear_propuesta_sin_destino_lanza_validationerror(self):
        with self.assertRaises(ValidationError):
            self.crear(estandar=None)


class UnicidadParesVivosTests(BaseVinculacion):
    def test_duplicado_vivo_bloqueado(self):
        self.crear()
        self.assert_integridad()

    def test_duplicado_tras_confirmar_bloqueado(self):
        corr = self.crear()
        corr.confirmar(self.usuario)
        self.assert_integridad()

    def test_repropuesta_tras_rechazo_permitida(self):
        corr = self.crear()
        corr.rechazar(self.usuario, "No corresponde")
        segunda = self.crear()
        self.assertEqual(segunda.estado, EstadoCorrespondencia.PROPUESTA)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_directo()

    def test_mismo_indicador_operativo_con_varios_destinos(self):
        self.crear(criterio_op=None, indicador_op=self.indicador_op, estandar=self.std_a)
        self.crear(criterio_op=None, indicador_op=self.indicador_op, estandar=self.std_a2)
        self.crear(criterio_op=None, indicador_op=self.indicador_op, estandar=None, dimension=self.dim_a)
        self.crear(
            criterio_op=None,
            indicador_op=self.indicador_op,
            estandar=None,
            indicador_marco=self.ind_marco_a,
        )
        self.assertEqual(
            Correspondencia.objects.filter(indicador_op=self.indicador_op).count(), 4
        )


class CoherenciaVersionTests(BaseVinculacion):
    def test_destino_de_otra_version_rechazado(self):
        with self.assertRaises(ValidationError):
            self.crear(version_marco=self.version_a, estandar=self.std_b)

    def test_destino_de_otra_version_rechazado_en_directo(self):
        # La validación es de aplicación: objects.create con destino ajeno a la
        # versión no viola restricción de BD (documentado), pero clean() lo bloquea.
        corr = self.create_directo(version_marco=self.version_a, estandar=self.std_b)
        with self.assertRaises(ValidationError):
            corr.full_clean()

    def test_validador_helper_coincide(self):
        resultado = validar_destino_en_version(self.version_a, estandar=self.std_a)
        self.assertEqual(resultado, self.std_a)

    def test_validador_helper_discrepancia(self):
        with self.assertRaises(ValidationError):
            validar_destino_en_version(self.version_a, indicador_marco=self.ind_marco_b)

    def test_validador_helper_destino_multiple(self):
        with self.assertRaises(ValidationError):
            validar_destino_en_version(self.version_a, dimension=self.dim_a, estandar=self.std_a)


class TransicionesTests(BaseVinculacion):
    def test_propuesta_a_confirmada(self):
        corr = self.crear()
        corr.confirmar(self.usuario, "Alineado con el marco")
        corr.refresh_from_db()
        self.assertEqual(corr.estado, EstadoCorrespondencia.CONFIRMADA)
        self.assertEqual(corr.confirmado_por, self.usuario)
        self.assertIsNotNone(corr.fecha_confirmacion)
        self.assertIsNone(corr.rechazado_por)
        self.assertIsNone(corr.fecha_rechazo)

    def test_confirmar_sin_actor(self):
        corr = self.crear()
        with self.assertRaises(ValidationError):
            corr.confirmar(None)

    def test_confirmar_desde_confirmada(self):
        corr = self.crear()
        corr.confirmar(self.usuario)
        with self.assertRaises(ValidationError):
            corr.confirmar(self.usuario)

    def test_propuesta_a_rechazada_con_comentario(self):
        corr = self.crear()
        corr.rechazar(self.usuario, "Fuera de alcance")
        corr.refresh_from_db()
        self.assertEqual(corr.estado, EstadoCorrespondencia.RECHAZADA)
        self.assertEqual(corr.rechazado_por, self.usuario)
        self.assertIsNotNone(corr.fecha_rechazo)
        self.assertIsNone(corr.confirmado_por)
        self.assertIsNone(corr.fecha_confirmacion)

    def test_rechazar_sin_comentario(self):
        corr = self.crear()
        with self.assertRaises(ValidationError):
            corr.rechazar(self.usuario, "")
        with self.assertRaises(ValidationError):
            corr.rechazar(self.usuario, "   ")

    def test_rechazada_es_terminal(self):
        corr = self.crear()
        corr.rechazar(self.usuario, "No aplica")
        with self.assertRaises(ValidationError):
            corr.confirmar(self.usuario)
        with self.assertRaises(ValidationError):
            corr.rechazar(self.usuario, "Otro")

    def test_desconfirmar_a_propuesta(self):
        corr = self.crear()
        corr.confirmar(self.usuario)
        corr.desconfirmar(self.usuario, "Revisión adicional requerida")
        corr.refresh_from_db()
        self.assertEqual(corr.estado, EstadoCorrespondencia.PROPUESTA)
        self.assertIsNone(corr.confirmado_por)
        self.assertIsNone(corr.fecha_confirmacion)
        self.assertEqual(corr.comentario, "Revisión adicional requerida")

    def test_desconfirmar_sin_comentario(self):
        corr = self.crear()
        corr.confirmar(self.usuario)
        with self.assertRaises(ValidationError):
            corr.desconfirmar(self.usuario, "")

    def test_desconfirmar_desde_propuesta(self):
        corr = self.crear()
        with self.assertRaises(ValidationError):
            corr.desconfirmar(self.usuario, "N/A")

    def test_cambio_estado_directo_bloqueado(self):
        corr = self.crear()
        corr.estado = EstadoCorrespondencia.CONFIRMADA
        with self.assertRaises(ValidationError):
            corr.save()

    def test_cambio_par_directo_bloqueado(self):
        corr = self.crear()
        corr.estandar = self.std_a2
        with self.assertRaises(ValidationError):
            corr.save()


class SellosYAuditoriaTests(BaseVinculacion):
    def test_sello_confirmada_sin_fecha_bloqueado_bd(self):
        self.assert_integridad(estado=EstadoCorrespondencia.CONFIRMADA, fecha_confirmacion=None)

    def test_sello_rechazada_sin_comentario_bloqueado_bd(self):
        self.assert_integridad(
            estado=EstadoCorrespondencia.RECHAZADA,
            fecha_rechazo=timezone.now(),
            comentario="",
        )

    def test_sello_propuesta_con_sellos_bloqueado_bd(self):
        self.assert_integridad(
            estado=EstadoCorrespondencia.PROPUESTA,
            fecha_confirmacion=timezone.now(),
        )

    def test_auditoria_de_creacion(self):
        corr = self.crear()
        entrada = Auditoria.objects.get(modelo="Correspondencia", registro_id=corr.pk)
        self.assertEqual(entrada.usuario, self.usuario)
        self.assertIn("propuesta", entrada.descripcion)

    def test_auditoria_de_transiciones(self):
        corr = self.crear()
        corr.confirmar(self.usuario, "OK")
        corr.desconfirmar(self.usuario, "Revisar")
        entradas = Auditoria.objects.filter(modelo="Correspondencia", registro_id=corr.pk)
        self.assertEqual(entradas.count(), 3)
        descripciones = " | ".join(entradas.values_list("descripcion", flat=True))
        self.assertIn("«propuesta» → «confirmada»", descripciones)
        self.assertIn("«confirmada» → «propuesta»", descripciones)
        self.assertTrue(all(entrada.usuario == self.usuario for entrada in entradas))

    def test_procedencia_derivada_no_autoconfirma(self):
        corr = self.crear(procedencia=ProcedenciaCorrespondencia.DERIVADA)
        self.assertEqual(corr.estado, EstadoCorrespondencia.PROPUESTA)


class SinEfectosOperativosTests(BaseVinculacion):
    def test_conteos_operativos_inmutables(self):
        conteos_previos = {
            "criterios": Criterio.objects.count(),
            "indicadores": Indicador.objects.count(),
            "asignaciones": Asignacion.objects.count(),
            "dimensiones": Dimension.objects.count(),
            "estandares": Estandar.objects.count(),
            "indicadores_marco": IndicadorMarco.objects.count(),
        }
        corr = self.crear()
        corr.confirmar(self.usuario)
        corr.desconfirmar(self.usuario, "Revisión")
        corr.rechazar(self.usuario, "No aplica") if corr.estado == EstadoCorrespondencia.PROPUESTA else None
        self.assertEqual(conteos_previos["criterios"], Criterio.objects.count())
        self.assertEqual(conteos_previos["indicadores"], Indicador.objects.count())
        self.assertEqual(conteos_previos["asignaciones"], Asignacion.objects.count())
        self.assertEqual(conteos_previos["dimensiones"], Dimension.objects.count())
        self.assertEqual(conteos_previos["estandares"], Estandar.objects.count())
        self.assertEqual(conteos_previos["indicadores_marco"], IndicadorMarco.objects.count())
        self.assertEqual(Criterio.objects.get(pk=self.criterio_op.pk).nombre, "Criterio operativo")
        self.assertTrue(all(a.modelo == "Correspondencia" for a in Auditoria.objects.all()))
