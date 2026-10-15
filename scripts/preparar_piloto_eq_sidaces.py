#!/usr/bin/env python3
"""Prepara el dataset piloto del catálogo normalizado EQ-SIDACES.

Selecciona una rama jerárquica completa (dimensión por defecto: dim:VI),
conserva únicamente registros confirmados con la cadena entera de ancestros
confirmada, excluye las evidencias indicativas (procedencia de su asociación
con indicadores aún no resuelta: ver docs/decisiones_eq_sidaces.md D8) y
genera un archivo separado con validaciones de integridad, unicidad y
trazabilidad. No modifica los archivos de origen.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

NIVEL_DE_PADRE = {
    "componente": ("dimension", "dim:"),
    "criterio": ("componente", "comp:"),
    "estandar": ("criterio", "cri:"),
    "indicador": ("estandar", "std:"),
}
NIVELES_MATRIZ = ("dimension", "componente", "criterio", "estandar", "indicador")
NIVEL_JERARQUICO = {
    "dimension": 1,
    "componente": 2,
    "criterio": 3,
    "estandar": 4,
    "indicador": 5,
}


def sha256_archivo(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar(path: Path):
    with open(path, encoding="utf-8") as fh:
        datos = json.load(fh)
    registros = datos.get("registros")
    if not isinstance(registros, list):
        raise SystemExit(f"{path}: no contiene la lista 'registros'")
    return datos, registros


def ancestros(registro, por_clave):
    cadena = []
    actual = registro
    while actual.get("padre"):
        padre = por_clave.get(actual["padre"])
        if padre is None:
            raise SystemExit(
                f"Padre inexistente en el dataset de origen: {actual['clave']} -> {actual['padre']}"
            )
        cadena.append(padre)
        actual = padre
    return cadena


def seleccionar(registros, dimension):
    por_clave = {r["clave"]: r for r in registros}
    incluidos, excluidos = [], Counter()
    detalle_excluidos = []
    for r in registros:
        cadena = [r] + ancestros(r, por_clave)
        raiz = cadena[-1]
        if raiz["clave"] != dimension:
            excluidos["fuera_dimension"] += 1
            continue
        if r["nivel"] == "evidencia":
            excluidos["politica_evidencia"] += 1
            detalle_excluidos.append((r["clave"], "politica_evidencia"))
            continue
        if r["estado"] != "confirmado":
            excluidos["pendiente"] += 1
            detalle_excluidos.append((r["clave"], "pendiente"))
            continue
        if any(a["estado"] != "confirmado" for a in cadena[1:]):
            excluidos["ascendencia_pendiente"] += 1
            detalle_excluidos.append((r["clave"], "ascendencia_pendiente"))
            continue
        incluidos.append(r)
    return incluidos, excluidos, detalle_excluidos


def validar(incluidos, meta_piloto, version_origen):
    errores = []
    claves = set()
    por_clave = {}
    for r in incluidos:
        clave = r.get("clave")
        if not clave:
            errores.append("registro sin clave")
            continue
        if clave in claves:
            errores.append(f"clave duplicada: {clave}")
        claves.add(clave)
        por_clave[clave] = r

    for r in incluidos:
        clave = r.get("clave", "?")
        if r.get("nivel") not in NIVELES_MATRIZ:
            errores.append(f"{clave}: nivel inesperado '{r.get('nivel')}'")
        if r.get("estado") != "confirmado":
            errores.append(f"{clave}: estado '{r.get('estado')}' (solo se admiten confirmados)")
        if not (r.get("texto_original") or "").strip():
            errores.append(f"{clave}: texto_original vacío")
        if not isinstance(r.get("orden"), int) or r["orden"] < 1:
            errores.append(f"{clave}: orden inválido ({r.get('orden')!r})")
        if r.get("version_marco") != version_origen:
            errores.append(f"{clave}: version_marco '{r.get('version_marco')}' != origen")
        esperado = NIVEL_JERARQUICO.get(r.get("nivel"))
        if esperado is not None and r.get("nivel_jerarquico") != esperado:
            errores.append(f"{clave}: nivel_jerarquico {r.get('nivel_jerarquico')} != {esperado}")
        origen = r.get("origen") or {}
        if not isinstance(origen.get("pdf_pagina"), int) or origen["pdf_pagina"] < 1:
            errores.append(f"{clave}: origen.pdf_pagina ausente o inválido")
        if not isinstance(origen.get("pagina_documento"), int) or origen["pagina_documento"] < 1:
            errores.append(f"{clave}: origen.pagina_documento ausente o inválido")
        padre = r.get("padre")
        if r["nivel"] == "dimension":
            if padre is not None:
                errores.append(f"{clave}: dimensión con padre no nulo")
            continue
        if not padre:
            errores.append(f"{clave}: sin padre")
            continue
        if padre not in por_clave:
            errores.append(f"{clave}: padre '{padre}' ausente del subconjunto")
            continue
        nivel_padre, prefijo = NIVEL_DE_PADRE[r["nivel"]]
        p = por_clave[padre]
        if p["nivel"] != nivel_padre or not p["clave"].startswith(prefijo):
            errores.append(f"{clave}: padre '{padre}' no es {nivel_padre} con prefijo {prefijo}")

    raices = [r["clave"] for r in incluidos if r["nivel"] == "dimension"]
    if len(raices) != 1:
        errores.append(f"se esperaba exactamente una dimensión, hay {len(raices)}")

    if meta_piloto.get("version_marco") != version_origen:
        errores.append("meta_piloto.version_marco no coincide con el dataset de origen")
    if meta_piloto.get("aprobado_institucionalmente") is not False:
        errores.append("meta_piloto debe declarar aprobado_institucionalmente=false")

    return errores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in",
        dest="entrada",
        default="data/catalogo/eq_sidaces_normalized.json",
        help="Dataset normalizado de origen (JSON)",
    )
    parser.add_argument(
        "--out",
        dest="salida",
        default="data/catalogo/eq_sidaces_piloto.json",
        help="Archivo piloto a generar",
    )
    parser.add_argument(
        "--dimension",
        default="dim:VI",
        help="Clave de la dimensión a incluir (por defecto: dim:VI)",
    )
    parser.add_argument(
        "--validar-solo",
        action="store_true",
        dest="validar_solo",
        help="Solo validar el piloto existente, sin regenerarlo",
    )
    args = parser.parse_args()

    if args.validar_solo:
        datos, registros = cargar(Path(args.salida))
        meta = datos.get("meta") or {}
        version = (registros[0].get("version_marco") if registros else meta.get("version_marco"))
        errores = validar(registros, meta, version)
    else:
        origen = Path(args.entrada)
        datos, registros = cargar(origen)
        version = datos["meta"]["version_marco"]
        incluidos, excluidos, detalle = seleccionar(registros, args.dimension)
        por_nivel = Counter(r["nivel"] for r in incluidos)
        if por_nivel.get("dimension", 0) != 1 or not all(
            por_nivel.get(n, 0) > 0 for n in ("componente", "criterio", "estandar", "indicador")
        ):
            raise SystemExit(
                f"La dimensión {args.dimension} no produce una rama completa "
                f"(contenidos: {dict(por_nivel)})"
            )
        meta_piloto = {
            "tipo": "dataset_piloto_subconjunto",
            "aprobado_institucionalmente": False,
            "version_marco": version,
            "fuente_pdf": datos["meta"].get("fuente_pdf"),
            "norma": datos["meta"].get("norma"),
            "dimension_incluida": args.dimension,
            "dataset_origen": str(origen).replace("\\", "/"),
            "dataset_origen_sha256": sha256_archivo(origen),
            "script_generador": "scripts/preparar_piloto_eq_sidaces.py",
            "reglas_seleccion": [
                "registros de la dimensión indicada",
                "estado == confirmado",
                "cadena completa de ancestros confirmados dentro del subconjunto",
                "evidencias indicativas excluidas (asociación indicador sin resolver: D8)",
            ],
            "conteos_piloto": dict(sorted(por_nivel.items())),
            "conteos_piloto_total": len(incluidos),
            "exclusiones": {
                "por_motivo_dimensión": {
                    k: v for k, v in sorted(excluidos.items()) if k != "fuera_dimension"
                },
                "fuera_dimension_total": excluidos["fuera_dimension"],
                "detalle_excluidos_dimension": [
                    {"clave": c, "motivo": m} for c, m in detalle
                ],
            },
            "notas": [
                "Subconjunto reproducible para pruebas técnicas; no representa el marco completo",
                "Los campos de cada registro se copian sin modificar del dataset de origen",
                "Codigos de indicadores/evidencias del origen son sintéticos, no oficiales",
            ],
        }
        errores = validar(incluidos, meta_piloto, version)
        salida = {
            "meta": meta_piloto,
            "registros": incluidos,
        }
        if not errores:
            Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
            with open(args.salida, "w", encoding="utf-8") as fh:
                json.dump(salida, fh, ensure_ascii=False, indent=2)
                fh.write("\n")

    if errores:
        for e in errores:
            print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(f"Validación fallida: {len(errores)} error(es)")

    por_nivel = Counter(r["nivel"] for r in (datos.get("registros") if args.validar_solo else incluidos))
    print("Piloto OK")
    for nivel in NIVELES_MATRIZ:
        print(f"  {nivel:11} {por_nivel.get(nivel, 0):4}")
    print(f"  {'TOTAL':11} {sum(por_nivel.values()):4}")
    if not args.validar_solo:
        print("Exclusiones (dimensión):", dict(sorted(excluidos.items())))
        print(f"Archivo: {args.salida}")
        print(
            "Validar con el importador (sin tocar BD): backend\\venv\\Scripts\\python.exe "
            f"backend\\manage.py import_eq_sidaces --file {args.salida} "
            f"--marco-version {version} --check"
        )


if __name__ == "__main__":
    main()
