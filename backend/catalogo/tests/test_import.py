import json
import os
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalogo.models import (
    Componente,
    CriterioMarco,
    Dimension,
    Estandar,
    EvidenciaIndicativa,
    IndicadorMarco,
    VersionMarcoEvaluacion,
)

VERSION = "VER-TEST"


def _reg(**kwargs):
    base = {
        "clave": "",
        "nivel": "",
        "codigo": "",
        "texto_original": "",
        "padre": None,
        "orden": 1,
        "nivel_jerarquico": 0,
        "version_marco": VERSION,
        "origen": {"pdf_pagina": 1, "pagina_documento": 1},
        "estado": "confirmado",
        "observaciones": [],
    }
    base.update(kwargs)
    return base


def dataset_base():
    """Jerarquia sintetica valida: dim->comp->cri->std, 2 indicadores, 1 evidencia
    mas un estandar pendiente con su indicador (para probar omisiones)."""
    registros = [
        _reg(clave="dim:1", nivel="dimension", codigo="I", texto_original="Dimension I",
             nivel_jerarquico=1),
        _reg(clave="comp:1.1", nivel="componente", codigo="1.1", texto_original="Componente 1.1",
             padre="dim:1", nivel_jerarquico=2,
             origen={"pdf_pagina": 1, "pagina_documento": 1, "definicion": "Definicion del componente"}),
        _reg(clave="cri:1.1.1", nivel="criterio", codigo="1.1.1", texto_original="Criterio 1.1.1",
             padre="comp:1.1", nivel_jerarquico=3),
        _reg(clave="std:1.1.1.1", nivel="estandar", codigo="1.1.1.1",
             texto_original="Estandar 1.1.1.1", padre="cri:1.1.1", nivel_jerarquico=4),
        _reg(clave="ind:1.1.1.1#1", nivel="indicador", texto_original="Indicador uno",
             padre="std:1.1.1.1", orden=1, nivel_jerarquico=5),
        _reg(clave="ind:1.1.1.1#2", nivel="indicador", texto_original="Indicador dos",
             padre="std:1.1.1.1", orden=2, nivel_jerarquico=5),
        _reg(clave="evi:ind:1.1.1.1#1#1", nivel="evidencia", texto_original="Evidencia uno",
             padre="ind:1.1.1.1#1", orden=1, nivel_jerarquico=6),
        _reg(clave="std:1.1.1.2", nivel="estandar", codigo="1.1.1.2",
             texto_original="Estandar pendiente", padre="cri:1.1.1", nivel_jerarquico=4,
             estado="pendiente_revision", observaciones=["discrepancia de conteo; revisar"]),
        _reg(clave="ind:1.1.1.2#1", nivel="indicador", texto_original="Hijo de pendiente",
             padre="std:1.1.1.2", orden=1, nivel_jerarquico=5),
    ]
    conteos = {"dimension": 1, "componente": 1, "criterio": 1, "estandar": 2, "indicador": 3,
               "evidencia": 1}
    meta = {
        "conteos_extraidos": conteos,
        "conteos_referencia": dict(conteos),
        "incidencias": [],
        "notas_extraccion": ["dataset sintetico de pruebas"],
    }
    return {"meta": meta, "registros": registros}


class ImportEqSidacesTest(TestCase):
    def escribir_json(self, datos, sufijo=".json"):
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=sufijo, encoding="utf-8")
        json.dump(datos, f, ensure_ascii=False)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def escribir_csv(self, columnas, filas):
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", encoding="utf-8",
                                        newline="")
        f.write(",".join(columnas) + "\n")
        for fila in filas:
            f.write(",".join(str(x) for x in fila) + "\n")
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def comandar(self, path, **kwargs):
        kwargs.setdefault("file", path)
        kwargs.setdefault("marco_version", VERSION)
        call_command("import_eq_sidaces", **kwargs)

    # ------------------------------------------------------------------
    # validacion de archivo
    # ------------------------------------------------------------------

    def test_check_valido_no_toca_bd(self):
        path = self.escribir_json(dataset_base())
        self.comandar(path, check=True)
        self.assertEqual(VersionMarcoEvaluacion.objects.count(), 0)
        self.assertEqual(Dimension.objects.count(), 0)

    def test_check_falta_campo(self):
        datos = dataset_base()
        del datos["registros"][0]["nivel"]
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True)

    def test_check_clave_duplicada(self):
        datos = dataset_base()
        datos["registros"].append(dict(datos["registros"][3]))
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True)

    def test_check_padre_inexistente(self):
        datos = dataset_base()
        datos["registros"][4]["padre"] = "std:9.9.9.9"
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True)

    def test_check_nivel_padre_incorrecto(self):
        datos = dataset_base()
        datos["registros"][4]["padre"] = "cri:1.1.1"
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True)

    def test_check_prefijo_componente_incoherente(self):
        datos = dataset_base()
        datos["registros"][1]["codigo"] = "9.9"
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True)

    def test_check_prefijo_criterio_incoherente(self):
        datos = dataset_base()
        datos["registros"][2]["codigo"] = "2.1.1"
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True)

    def test_check_version_no_coincide(self):
        path = self.escribir_json(dataset_base())
        with self.assertRaises(CommandError):
            self.comandar(path, check=True, marco_version="OTRA-VERSION")

    def test_check_orden_invalido(self):
        datos = dataset_base()
        datos["registros"][4]["orden"] = 0
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True)

    def test_check_evidencia_confirmada_sin_indicador_como_padre(self):
        datos = dataset_base()
        datos["registros"][6]["padre"] = "std:1.1.1.1"
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True)

    def test_check_requiere_exactamente_un_modo(self):
        path = self.escribir_json(dataset_base())
        with self.assertRaises(CommandError):
            self.comandar(path)
        with self.assertRaises(CommandError):
            self.comandar(path, check=True, dry_run=True)

    def test_check_csv(self):
        path = self.escribir_csv(
            ["clave", "nivel", "codigo", "texto_original", "padre", "orden",
             "nivel_jerarquico", "version_marco", "estado"],
            [["dim:1", "dimension", "I", "Dimension I", "", 1, 1, VERSION, "confirmado"]],
        )
        self.comandar(path, check=True)
        self.assertEqual(VersionMarcoEvaluacion.objects.count(), 0)

    def test_check_discrepancias_solo_reporta(self):
        datos = dataset_base()
        datos["meta"]["conteos_referencia"]["estandar"] = 5
        path = self.escribir_json(datos)
        self.comandar(path, check=True)

    # ------------------------------------------------------------------
    # dry-run y apply
    # ------------------------------------------------------------------

    def test_dry_run_no_escribe(self):
        path = self.escribir_json(dataset_base())
        self.comandar(path, dry_run=True)
        self.assertEqual(VersionMarcoEvaluacion.objects.count(), 0)
        self.assertEqual(Dimension.objects.count(), 0)
        self.assertEqual(IndicadorMarco.objects.count(), 0)

    def test_apply_importa_solo_confirmados(self):
        path = self.escribir_json(dataset_base())
        self.comandar(path, apply=True, allow_synthetic_codes=True)

        self.assertEqual(VersionMarcoEvaluacion.objects.count(), 1)
        self.assertEqual(Dimension.objects.count(), 1)
        self.assertEqual(Componente.objects.count(), 1)
        self.assertEqual(CriterioMarco.objects.count(), 1)
        self.assertEqual(Estandar.objects.count(), 1)  # el pendiente no se importa
        self.assertEqual(IndicadorMarco.objects.count(), 2)  # el hijo de pendiente se omite
        self.assertEqual(EvidenciaIndicativa.objects.count(), 1)

        comp = Componente.objects.get()
        self.assertEqual(comp.definicion, "Definicion del componente")
        cri = CriterioMarco.objects.get()
        self.assertEqual(cri.definicion, "")

        inds = IndicadorMarco.objects.order_by("codigo_completo")
        self.assertEqual([i.codigo_completo for i in inds],
                         ["1.1.1.1-IND-01", "1.1.1.1-IND-02"])
        self.assertTrue(all(i.activo for i in inds))
        evi = EvidenciaIndicativa.objects.get()
        self.assertEqual(evi.indicador_marco, inds[0])
        self.assertIsNone(evi.obligatoria)

    def test_apply_sin_allow_synthetic_codes_falla(self):
        path = self.escribir_json(dataset_base())
        with self.assertRaises(CommandError):
            self.comandar(path, apply=True)
        self.assertEqual(VersionMarcoEvaluacion.objects.count(), 0)

    def test_discrepancias_bloquean_sin_ack(self):
        datos = dataset_base()
        datos["meta"]["conteos_referencia"]["indicador"] = 99
        path = self.escribir_json(datos)
        with self.assertRaises(CommandError):
            self.comandar(path, dry_run=True)
        self.assertEqual(VersionMarcoEvaluacion.objects.count(), 0)

    def test_discrepancias_con_ack_permiten_apply(self):
        datos = dataset_base()
        datos["meta"]["conteos_referencia"]["indicador"] = 99
        path = self.escribir_json(datos)
        self.comandar(path, apply=True, allow_synthetic_codes=True, ack_discrepancias=True)
        self.assertEqual(Dimension.objects.count(), 1)

    def test_apply_idempotente(self):
        path = self.escribir_json(dataset_base())
        self.comandar(path, apply=True, allow_synthetic_codes=True)
        self.comandar(path, apply=True, allow_synthetic_codes=True)
        self.assertEqual(VersionMarcoEvaluacion.objects.count(), 1)
        self.assertEqual(IndicadorMarco.objects.count(), 2)
