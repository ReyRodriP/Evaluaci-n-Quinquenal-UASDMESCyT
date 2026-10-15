#!/usr/bin/env python
"""Genera el archivo de trabajo de revision de los pendientes EQ-SIDACES.

Clasifica cada registro pendiente_revision por causa y, para las evidencias,
calcula una sugerencia de asociacion a indicador a partir de la alineacion de
vinetas en el layout del PDF (siempre marcada como inferida: la matriz no
contiene asociacion explicita por item).

Uso (desde la raiz del repositorio):

    pip install pypdf
    python scripts/revisar_eq_sidaces.py

    # con layout ya extraido (evita volver a leer el PDF):
    python scripts/revisar_eq_sidaces.py --layout ruta/al/layout.json

Salida:
    data/catalogo/eq_sidaces_revision.csv   (archivo NUEVO; no modifica los
    normalizados originales). utf-8 con BOM para abrirse directo en Excel.

Columnas de decision (vacias hasta que la revision las llene):
    decision              confirmar | corregir | pendiente
    texto_corregido       texto propuesto si decision=corregir
    padre_confirmado      clave del padre/indicador confirmado si aplica
    observaciones_revision comentarios del revisor
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import importlib.util

_MOD_PATH = Path(__file__).with_name("extraer_eq_sidaces.py")
_spec = importlib.util.spec_from_file_location("extraer_eq_sidaces", _MOD_PATH)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def categorizar(reg: dict) -> list[str]:
    cats: list[str] = []
    for o in reg.get("observaciones", []):
        if "sin codigo oficial en la fuente" in o:
            # observacion base de evidencias: no es una anomalia aparte
            continue
        if "codigo no corresponde" in o:
            c = "codigo_fuera_de_contexto"
        elif "celda de indicador sin vineta" in o:
            c = "indicador_sin_vineta"
        elif "impresa en la fila del estandar" in o:
            c = "indicador_reensamblado"
        elif "anomalia en la celda de evidencias" in o or "contaminacion del texto por la columna" in o:
            c = "texto_contaminado"
        elif "vineta sin texto" in o or "celda vacia" in o:
            c = "vineta_sin_texto"
        elif "palabra partida" in o:
            c = "palabra_partida"
        elif "asociacion evidencia->indicador" in o:
            c = "evidencia_sin_asociacion"
        else:
            c = "otras"
        if c not in cats:
            cats.append(c)
    return cats


def cargar_layout(ruta_layout: str, pdf: str | None) -> dict[str, str]:
    if ruta_layout:
        p = Path(ruta_layout)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    if not pdf:
        candidatos = sorted(Path("docs").glob("*.pdf"))
        if not candidatos:
            raise SystemExit("No se encontro el PDF en docs/ ni se indico --layout/--pdf")
        pdf = str(candidatos[0])
    print(f"Leyendo layout de {pdf} ...")
    return mod.extraer_paginas(Path(pdf))


def alineacion(paginas: dict[str, str]) -> tuple[dict, int, int]:
    """Devuelve sugerencias por fila, total viñetas indicador y evidencia."""
    sugerencia: dict[tuple[int, str], dict[int, tuple[int | None, str]]] = defaultdict(dict)
    previo = None
    fila = None
    ind_por_linea: dict[int, int] = {}
    evi_por_linea: list[tuple[int, int]] = []
    n_ind = n_evi = 0
    bullets_ind = bullets_evi = 0

    def cerrar_fila():
        nonlocal n_ind, n_evi, ind_por_linea, evi_por_linea
        if fila is not None:
            for ln, oe in evi_por_linea:
                if ln in ind_por_linea:
                    sugerencia[fila][oe] = (ind_por_linea[ln], "misma_linea")
                    continue
                ady = [o for o, l2 in ind_por_linea.items() if abs(ln - l2) == 1]
                if len(ady) == 1:
                    sugerencia[fila][oe] = (ady[0], "linea_adyacente")
                else:
                    sugerencia[fila][oe] = (None, "sin_correspondencia")
        n_ind = n_evi = 0
        ind_por_linea = {}
        evi_por_linea = []

    for clave_pag in sorted(paginas, key=int):
        pagina = int(clave_pag)
        lineas = paginas[clave_pag].splitlines()
        hi = mod.indice_cabecera(lineas)
        if hi is None:
            continue
        limites, origen = mod.limites_pagina(lineas, previo)
        if origen == "cabecera":
            limites = mod.limites_cabecera(lineas[hi])
            if limites is None:
                continue
        previo = limites
        b1, b2, b3 = limites
        for lineno, line in enumerate(lineas[hi + 1:], start=hi + 1):
            if not line.strip():
                continue
            c0, c1, c2, c3 = (x.strip() for x in mod.partir_linea(line, b1, b2, b3))
            if c1 and mod.RE_STD.match(c1):
                cerrar_fila()
                fila = (pagina, mod.RE_STD.match(c1).group(1))
            if c2.startswith("\u2022"):
                bullets_ind += 1
                if fila is not None:
                    n_ind += 1
                    ind_por_linea[lineno] = n_ind
            if c3 and c3[0] in "\u2212\u2013\u2014":
                bullets_evi += 1
                if fila is not None:
                    n_evi += 1
                    evi_por_linea.append((lineno, n_evi))
    cerrar_fila()
    return sugerencia, bullets_ind, bullets_evi


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--norm", default="data/catalogo/eq_sidaces_normalized.json")
    ap.add_argument("--layout", default="", help="JSON con el texto layout ya extraido")
    ap.add_argument("--pdf", default="", help="PDF oficial (si no hay --layout)")
    ap.add_argument("--out", default="data/catalogo/eq_sidaces_revision.csv")
    args = ap.parse_args()

    datos = json.loads(Path(args.norm).read_text(encoding="utf-8"))
    registros = datos["registros"]
    por_clave = {r["clave"]: r for r in registros}

    pendientes = [r for r in registros if r["estado"] == "pendiente_revision"]
    conteo_cat: Counter = Counter()
    combo: Counter = Counter()
    cats_por_clave = {}
    for r in pendientes:
        cats = categorizar(r)
        cats_por_clave[r["clave"]] = cats
        for c in cats:
            conteo_cat[c] += 1
        combo[tuple(sorted(cats))] += 1

    print("=== PENDIENTES POR CAUSA ===")
    print("pendientes unicos:", len(pendientes))
    for c, n in conteo_cat.most_common():
        print(f"  {c:32s} {n}")
    print("--- combinaciones por registro ---")
    for k, n in combo.most_common():
        print(f"  {n:5d}  {' + '.join(k)}")
    print("registros con >1 categoria:", sum(n for k, n in combo.items() if len(k) > 1))

    paginas = cargar_layout(args.layout, args.pdf or None)
    sugerencia, bullets_ind, bullets_evi = alineacion(paginas)
    print("=== VINETAS EN LAYOUT (recuento independiente) ===")
    print("viñetas indicador:", bullets_ind, "| viñetas evidencia:", bullets_evi)
    criterios = Counter(v[1] for d in sugerencia.values() for v in d.values())
    print("criterios de correspondencia (evidencias):", dict(criterios))

    std_por_pag_cod = {
        (r["origen"]["pdf_pagina"], r["codigo"]): r["clave"]
        for r in registros
        if r["nivel"] == "estandar"
    }
    hijos: dict[str, list] = defaultdict(list)
    for r in registros:
        if r["padre"]:
            hijos[r["padre"]].append(r)
    indicadores_por_std: dict[str, list] = defaultdict(list)
    for r in registros:
        if r["nivel"] == "indicador" and r["padre"]:
            indicadores_por_std[r["padre"]].append(r)
    for v in indicadores_por_std.values():
        v.sort(key=lambda x: x["orden"])

    def sugerido_para_evidencia(reg):
        std_reg = por_clave.get(reg["padre"])
        if std_reg is None:
            return "", ""
        fila = (std_reg["origen"]["pdf_pagina"], std_reg["codigo"])
        entrada = sugerencia.get(fila, {}).get(reg["orden"])
        if not entrada:
            return "", ""
        orden_ind, criterio = entrada
        if orden_ind is None:
            return "", criterio
        for ind in indicadores_por_std.get(std_reg["clave"], []):
            if ind["orden"] == orden_ind:
                return ind["clave"], criterio
        return "", criterio

    nivel_ord = {n: i for i, n in enumerate(
        ["dimension", "componente", "criterio", "estandar", "indicador", "evidencia"], start=1)}

    filas_csv = []
    for orden_rev, r in enumerate(sorted(
        pendientes,
        key=lambda x: (x["origen"]["pdf_pagina"], nivel_ord[x["nivel"]], x["orden"], x["clave"]),
    ), start=1):
        padre = por_clave.get(r["padre"]) if r["padre"] else None
        hermanos = [h for h in hijos.get(r["padre"], []) if h["clave"] != r["clave"]] if r["padre"] else []
        indicadores_std, sugerida, criterio = [], "", ""
        if r["nivel"] == "evidencia":
            indicadores_std = [i["clave"] for i in indicadores_por_std.get(r["padre"], [])]
            sugerida, criterio = sugerido_para_evidencia(r)
        filas_csv.append({
            "orden_revision": orden_rev,
            "pagina_pdf": r["origen"]["pdf_pagina"],
            "pagina_documento": r["origen"]["pagina_documento"],
            "clave": r["clave"],
            "nivel": r["nivel"],
            "codigo": r.get("codigo", ""),
            "padre_clave": r["padre"] or "",
            "padre_codigo": (padre.get("codigo", "") if padre else ""),
            "padre_texto": (padre.get("texto_original", "") if padre else ""),
            "hermanos": " | ".join(f"{h['clave']}: {h['texto_original'][:60]}" for h in hermanos),
            "texto_original": r.get("texto_original", ""),
            "motivos": " + ".join(cats_por_clave.get(r["clave"], [])),
            "observaciones_fuente": " || ".join(r.get("observaciones", [])),
            "indicadores_del_estandar": " | ".join(indicadores_std),
            "indicador_sugerido_linea": sugerida,
            "criterio_asociacion": criterio,
            "estado_actual": r["estado"],
            "decision": "",
            "texto_corregido": "",
            "padre_confirmado": "",
            "observaciones_revision": "",
        })

    with open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas_csv[0].keys()))
        w.writeheader()
        w.writerows(filas_csv)
    print("=== ARCHIVO DE TRABAJO ===")
    print("escrito:", args.out, "| filas:", len(filas_csv))
    print("criterios (evidencias):",
          dict(Counter(f["criterio_asociacion"] for f in filas_csv if f["nivel"] == "evidencia")))


if __name__ == "__main__":
    main()
