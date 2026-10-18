"""Concurrencia real de la API de correspondencias.

TransactionTestCase + dos hilos con conexiones independientes a PostgreSQL,
sincronizados con threading.Barrier justo antes de la petición. No se simula
concurrencia con llamadas secuenciales. Si esta mecánica de hilos/conexiones
no resulta fiable en Windows, estas pruebas deben retirarse y documentarse
como límite del entorno.
"""

import threading

from django.db import connection, connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Usuario
from auditoria.models import Auditoria
from catalogo.models import VersionMarcoEvaluacion
from evaluation.models import Criterio, Periodo
from vinculacion.models import Correspondencia, EstadoCorrespondencia

from .test_models import _crear_cadena_marco

URL = "/api/vinculacion/correspondencias/"
BARRERA_TIMEOUT = 30
HILO_TIMEOUT = 60


class BaseConcurrencia(TransactionTestCase):
    """Datos creados por prueba (TransactionTestCase vacía las tablas tras cada prueba)."""

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            username="root_conc", email="root@x.org", password="x"
        )
        self.periodo = Periodo.objects.create(
            nombre="Periodo conc",
            fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate().replace(year=2027),
        )
        self.criterio = Criterio.objects.create(nombre="Criterio conc", periodo=self.periodo)
        self.version = VersionMarcoEvaluacion.objects.create(nombre="Marco Conc", slug="marco-conc")
        self.dim, self.estandar, self.ind_marco = _crear_cadena_marco(self.version)

    def _disparar_concurrente(self, *acciones):
        """Ejecuta una acción por hilo; todas liberadas a la vez por una barrera.

        Cada hilo abre su propia conexión a la BD antes de la barrera, crea su
        propio APIClient autenticado y cierra sus conexiones al terminar. Devuelve
        la lista de códigos de estado en el mismo orden de las acciones.
        """
        barrera = threading.Barrier(len(acciones), timeout=BARRERA_TIMEOUT)
        resultados = [None] * len(acciones)
        errores = [None] * len(acciones)

        def construir(indice, accion):
            def ejecutar():
                try:
                    connection.ensure_connection()
                    cliente = APIClient()
                    cliente.force_authenticate(user=self.admin)
                    barrera.wait()
                    resultados[indice] = accion(cliente).status_code
                except BaseException as exc:  # noqa: BLE001 - se relanza en el hilo principal
                    errores[indice] = exc
                finally:
                    connections.close_all()

            return ejecutar

        hilos = [
            threading.Thread(target=construir(i, accion), name=f"conc-{i}")
            for i, accion in enumerate(acciones)
        ]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join(timeout=HILO_TIMEOUT)
        bloqueados = [hilo.name for hilo in hilos if hilo.is_alive()]
        self.assertFalse(bloqueados, f"Hilos bloqueados sin finalizar: {bloqueados}")
        for exc in errores:
            if exc is not None:
                raise exc
        return resultados


class CreacionDuplicadaConcurrenteTests(BaseConcurrencia):
    """Dos POST simultáneos del mismo par origen-destino."""

    def test_una_sola_fila_y_una_sola_auditoria(self):
        payload = {
            "version_marco": self.version.pk,
            "criterio_op": self.criterio.pk,
            "estandar": self.estandar.pk,
        }

        def crear(cliente):
            return cliente.post(URL, payload, format="json")

        estados = self._disparar_concurrente(crear, crear)
        self.assertEqual(sorted(estados), [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        self.assertEqual(
            Correspondencia.objects.filter(criterio_op=self.criterio, estandar=self.estandar).count(),
            1,
        )
        self.assertEqual(
            Auditoria.objects.filter(accion="crear correspondencia", modelo="Correspondencia").count(),
            1,
        )


class ConfirmacionConcurrenteTests(BaseConcurrencia):
    """Dos POST simultáneos de confirmación sobre la misma propuesta."""

    def test_una_sola_transicion_y_una_sola_auditoria(self):
        corr = Correspondencia.crear_propuesta(
            actor=self.admin,
            version_marco=self.version,
            criterio_op=self.criterio,
            estandar=self.estandar,
        )
        url = f"{URL}{corr.pk}/confirmar/"

        def confirmar(cliente):
            return cliente.post(url, {}, format="json")

        estados = self._disparar_concurrente(confirmar, confirmar)
        self.assertEqual(sorted(estados), [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        corr.refresh_from_db()
        self.assertEqual(corr.estado, EstadoCorrespondencia.CONFIRMADA)
        self.assertEqual(
            Auditoria.objects.filter(
                accion="confirmar correspondencia",
                modelo="Correspondencia",
                registro_id=corr.pk,
            ).count(),
            1,
        )
