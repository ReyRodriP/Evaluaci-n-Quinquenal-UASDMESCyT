"""Pruebas de búsqueda de orígenes operativos (?search=) en /api/criterios/ y /api/indicadores/.

El parámetro 'search' es aditivo: sin él el listado no cambia (cubierto por
test_alcance). Estas pruebas bloquean que:
- filtra por nombre (parcial e insensitive) para localizar orígenes sin recorrer páginas;
- respeta el alcance por rol (Evaluador Externo no ve lo que su ámbito no le permite);
- el parámetro desconocido/ignorado no rompe el listado normal.
"""

from rest_framework import status

from evaluation.test_alcance import BaseAlcanceCatalogo


class BusquedaOrigenOperativoTests(BaseAlcanceCatalogo):
    def test_criterios_filtra_por_nombre_parcial(self):
        # Frase entrecomillada: DRF la evalúa como un solo término.
        respuesta = self.cliente(self.tecnico).get("/api/criterios/", {"search": '"Alc A"'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.nombres_pagina(respuesta), ["Criterio Alc A"])

    def test_indicadores_filtra_por_nombre_parcial_insensitive(self):
        respuesta = self.cliente(self.tecnico).get("/api/indicadores/", {"search": "ALC b"})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.nombres_pagina(respuesta), ["Indicador Alc B"])

    def test_search_sin_coincidencias_devuelve_vacio_y_no_error(self):
        respuesta = self.cliente(self.tecnico).get("/api/criterios/", {"search": "inexistente xyz"})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["count"], 0)
        self.assertEqual(respuesta.data["results"], [])

    def test_sin_search_conserva_el_listado_completo(self):
        respuesta = self.cliente(self.tecnico).get("/api/criterios/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.nombres_pagina(respuesta), ["Criterio Alc A", "Criterio Alc B"])

    def test_search_respetando_alcance_del_evaluador_externo(self):
        respuesta = self.cliente(self.externo).get("/api/criterios/", {"search": "Alc B"})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["count"], 0)

        respuesta = self.cliente(self.externo).get("/api/indicadores/", {"search": "Alc A"})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.nombres_pagina(respuesta), ["Indicador Alc A"])
