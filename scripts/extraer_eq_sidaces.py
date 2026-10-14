#!/usr/bin/env python
"""Extrae la matriz oficial EQ-SIDACES desde el PDF y genera el dataset normalizado.

Uso (desde la raiz del repositorio):

    pip install pypdf
    python scripts/extraer_eq_sidaces.py \
        --pdf "docs/Estándares Marco EQ-SIDACES (Versión Final).pdf" \
        --outdir data/catalogo

Salidas:
    eq_sidaces_normalized.json      dataset completo (meta + registros)
    eq_sidaces_normalized.csv       misma informacion en formato plano
    eq_sidaces_pending_review.json  solo registros con estado=pendiente_revision

Notas de extraccion:
  * Se usa pypdf en modo "layout" para conservar las 4 columnas de la matriz
    (Criterios | Estandares | Indicadores | Evidencias).
  * Los limites de columna se derivan de la posicion real del contenido y, si una
    pagina no trae codigos nuevos, se heredan de la pagina anterior (se marca en
    origen.limites_columnas).
  * El texto se normaliza colapsando espacios multiples. La justificacion del PDF
    quiebra palabras en algunas celdas: esos casos se listan en incidencias y no
    se corrigen automaticamente.
  * No se inventan codigos. Indicadores y evidencias no tienen codigo en la fuente
    (codigo queda vacio en el dataset).
  * Toda anomalia de la fuente se marca estado=pendiente_revision con observacion;
    nada se corrige ni se descarta silenciosamente.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

RE_DIM = re.compile(r"^DIMENSI[ÓO]N\s+([IVXLC]+)\s*[:\-]\s*(.+?)\s*$")
RE_COMP = re.compile(r"^Componente\s+(\d+\.\d+)\s*:\s*(.+?)\s*$")
LETTER = r"A-Za-z\u00C0-\u024F"
RE_CRI = re.compile(rf"^(\d{{1,2}}\.\d{{1,2}}\.\d{{1,2}})(?:\.(?!\d)|\s|[{LETTER}])\s*(.*)$")
RE_STD = re.compile(rf"^(\d{{1,2}}\.\d{{1,2}}\.\d{{1,2}}\.\d{{1,2}})(?:\.(?!\d)|\s|[{LETTER}])\s*(.*)$")
RE_STD_ANY = re.compile(rf"(?<![\d.])(\d{{1,2}}\.\d{{1,2}}\.\d{{1,2}}\.\d{{1,2}})(?=\s|\.|[{LETTER}])")
RE_IND_BULLET = re.compile(r"(?:(?<=\s)|^)\u2022")
RE_EVI_BULLET = re.compile(r"(?:(?<=\s)|^)[\u2212\u2013\u2014]")
RE_GAP = re.compile(r" {2,}")
RE_MULTI_SPACE = re.compile(r"\s+")
RE_TERMINADOR = re.compile(r"[.:;!?)]$")
# Quiebres de palabra por la justificacion del PDF: hueco multiple dentro de la linea
# o continuacion de linea que empieza con un fragmento corto.
RE_QUIEBRE = re.compile(r"(?<=[A-Za-zÁÉÍÓÚáéíóúñ])\s{2,}([a-záéíóúñ]{1,4})(?=[\s.,;:)\]]|$)")
RE_COLA = re.compile(r"^([a-záéíóúñ]{1,4})(?=[\s.,;:]|$)")
# Tokens cortos legitimos en espanol: no se marcan como quiebre.
STOP_CORTO = {
    "de", "la", "el", "en", "un", "una", "unos", "unas", "los", "las", "del", "al", "por",
    "con", "que", "se", "su", "sus", "es", "e", "y", "a", "o", "u", "ya", "si", "sí", "no",
    "ni", "te", "me", "he", "tu", "mi", "lo", "le", "da", "di", "nos", "tras", "son", "ser",
    "sea", "han", "ha", "hay", "uso", "web", "in", "tal", "fin", "dos", "uno", "tres", "mil",
    "ley", "vez", "más", "mas", "año", "así", "aún", "red", "rol", "voz", "paz", "mes", "hoy",
    "rey", "pie", "dar", "fue", "den", "va", "van", "ir", "para", "como", "sino", "hace",
    "está", "sido", "dado", "bien", "gran", "alto", "alta", "otra", "otro", "cual", "cuyo",
    "cuya", "mismo", "caso", "mar", "sol", "luz", "quien", "cabe", "junto", "junta",
    # palabras cortas legitimas frecuentes en el texto (falsos positivos verificados)
    "plan", "cada", "debe", "años", "área", "toma", "vida", "cabo", "país", "usos",
    "bajo", "ejes", "voto", "mide", "tipo", "sean", "sin", "base", "zona", "sede",
    "modo", "vía", "via", "todo", "toda", "dan", "era", "dio", "hizo", "solo", "sólo",
    "arte", "meta", "fin", "ley", "vez", "dos", "tres", "mil", "rey", "mes",
    "pie", "paz", "hoy", "voz", "red", "uso", "web", "tal", "año", "así", "aún",
}

TOL = 10
DESPLAZAMIENTO_PAGINA_DOCUMENTO = 12  # PDF 50 = pagina 38 del documento

VERSION_MARCO = "EQ-SIDACES-2019-Res27-2019"
NIVELES = ["dimension", "componente", "criterio", "estandar", "indicador", "evidencia"]
PREFIJOS = {
    "dimension": "dim",
    "componente": "comp",
    "criterio": "cri",
    "estandar": "std",
    "indicador": "ind",
    "evidencia": "evi",
}

CONTEOS_REFERENCIA = {
    "texto_seccion_2_3": {
        "dimension": 8,
        "componente": 36,
        "criterio": 77,
        "estandar": 210,
        "indicador": 909,
        "evidencia": 915,
    },
    "figura_2": {
        "dimension": 8,
        "componente": 36,
        "criterio": 77,
        "estandar": 212,
        "indicador": 915,
        "evidencia": 1082,
    },
}


def limpiar(texto: str) -> str:
    return RE_MULTI_SPACE.sub(" ", texto).strip()


# --------------------------------------------------------------------------
# Extraccion de texto en modo layout
# --------------------------------------------------------------------------


def extraer_paginas(pdf: Path) -> dict[str, str]:
    from pypdf import PdfReader  # importacion diferida: dependencia opcional

    reader = PdfReader(str(pdf))
    paginas = {}
    for i, page in enumerate(reader.pages, 1):
        try:
            paginas[str(i)] = page.extract_text(extraction_mode="layout") or ""
        except Exception:  # noqa: BLE001 - se reporta como pagina sin texto
            paginas[str(i)] = ""
    return paginas


# --------------------------------------------------------------------------
# Parser de la matriz
# --------------------------------------------------------------------------


def indice_cabecera(lineas: list[str]) -> int | None:
    for i, line in enumerate(lineas):
        if "Criterios" in line and "Evidencias" in line:
            return i
    return None


def primera_posicion(linea: str, regex: re.Pattern) -> int | None:
    m = regex.search(linea)
    return m.start() if m else None


def ajustar(linea: str, aproximado: int) -> int:
    """Ajusta un limite de columna al hueco de espacios mas cercano."""
    mejor = None
    for m in RE_GAP.finditer(linea):
        dist = abs(m.start() - aproximado)
        if dist <= TOL and (mejor is None or dist < mejor[0]):
            mejor = (dist, m.start())
    return mejor[1] if mejor else aproximado


def limites_pagina(lineas: list[str], previo: tuple[int, int, int] | None):
    """(limites, origen) con origen: contenido | heredado | cabecera."""
    std_x: list[int] = []
    ind_x: list[int] = []
    evi_x: list[int] = []
    for line in lineas:
        for m in RE_STD_ANY.finditer(line):
            if m.start() == 0 or line[m.start() - 1].isspace():
                std_x.append(m.start())
        for m in RE_IND_BULLET.finditer(line):
            ind_x.append(m.start())
        for m in RE_EVI_BULLET.finditer(line):
            evi_x.append(m.start())
    b1 = min(std_x) if std_x else (previo[0] if previo else None)
    b2 = min(ind_x) if ind_x else (previo[1] if previo else None)
    b3 = min(evi_x) if evi_x else (previo[2] if previo else None)
    origen = "contenido" if (std_x and ind_x and evi_x) else ("heredado" if previo else None)
    if None in (b1, b2, b3) or not (0 < b1 < b2 < b3):  # type: ignore[operator]
        return None, "cabecera"
    return (b1, b2, b3), origen


def limites_cabecera(linea: str) -> tuple[int, int, int] | None:
    pos = [linea.find(w) for w in ("Criterios", "Estándares", "Indicadores", "Evidencias")]
    if all(p >= 0 for p in pos):
        return pos[1], pos[2], pos[3]
    return None


def partir_linea(linea: str, b1: int, b2: int, b3: int) -> tuple[str, str, str, str]:
    std_pos = primera_posicion(linea, RE_STD_ANY)
    if std_pos is None:
        std_pos = ajustar(linea, b1)
    ind_pos = primera_posicion(linea, RE_IND_BULLET)
    evi_pos = primera_posicion(linea, RE_EVI_BULLET)
    fin1 = ind_pos if ind_pos is not None else ajustar(linea, b2)
    fin2 = evi_pos if evi_pos is not None else ajustar(linea, b3)
    fin1 = max(fin1, std_pos)
    fin2 = max(fin2, fin1)
    return linea[:std_pos], linea[std_pos:fin1], linea[fin1:fin2], linea[fin2:]


def parsear(paginas: dict[str, str]) -> dict:
    def marcar(reg, texto, cola=False):
        """Marca en el registro una posible palabra partida por la justificacion del PDF."""
        if reg is None or not texto:
            return
        frag = None
        m = RE_QUIEBRE.search(texto)
        if m and m.group(1) not in STOP_CORTO:
            frag = m.group(1)
        if frag is None and cola:
            m2 = RE_COLA.match(texto)
            if m2 and m2.group(1) not in STOP_CORTO:
                frag = m2.group(1)
        if frag:
            obs = (
                f"posible palabra partida por la justificacion del PDF "
                f"(fragmento '{frag}'); verificar contra el PDF"
            )
            lista = reg.setdefault("observaciones", [])
            if obs not in lista:
                lista.append(obs)

    dimensiones: dict[str, dict] = {}
    componentes: dict[str, dict] = {}
    criterios: list[dict] = []
    estandares: list[dict] = []
    incidencias: list[dict] = []
    avisos_pagina: list[dict] = []
    paginas_no_matriz: list[int] = []
    paginas_limites_heredados: list[int] = []
    paginas_limites_cabecera: list[int] = []
    previo = None

    cur_dim = cur_comp = cur_cri = cur_std = None
    cur_ind = cur_evi = None

    for clave_pagina in sorted(paginas, key=int):
        pagina = int(clave_pagina)
        lineas = paginas[clave_pagina].splitlines()
        hi = indice_cabecera(lineas)
        if hi is None:
            paginas_no_matriz.append(pagina)
            continue

        limites, origen = limites_pagina(lineas, previo)
        if origen == "cabecera":
            limites = limites_cabecera(lineas[hi])
            if limites is None:
                incidencias.append({"tipo": "sin_limites_columnas", "pagina": pagina})
                continue
            paginas_limites_cabecera.append(pagina)
            avisos_pagina.append(
                {"pagina": pagina, "nota": "limites de columna derivados de la cabecera de tabla"}
            )
        elif origen == "heredado":
            paginas_limites_heredados.append(pagina)
        previo = limites
        b1, b2, b3 = limites

        # --- encabezado: dimension, componente, definicion del componente ---
        en_definicion = False
        definicion: list[str] = []
        for line in lineas[:hi]:
            s = line.strip()
            if not s:
                continue
            m_dim = RE_DIM.match(s)
            if m_dim:
                en_definicion = False
                cur_dim = m_dim.group(1)
                entrada = dimensiones.setdefault(
                    m_dim.group(1),
                    {"codigo": m_dim.group(1), "nombre": limpiar(m_dim.group(2)), "paginas": []},
                )
                if pagina not in entrada["paginas"]:
                    entrada["paginas"].append(pagina)
                continue
            m_comp = RE_COMP.match(s)
            if m_comp:
                en_definicion = True
                definicion = []
                cur_comp = {"codigo": m_comp.group(1), "nombre": limpiar(m_comp.group(2)), "dim": cur_dim}
                entrada = componentes.setdefault(
                    m_comp.group(1), {**cur_comp, "paginas": [], "definicion": ""}
                )
                if pagina not in entrada["paginas"]:
                    entrada["paginas"].append(pagina)
                continue
            if not en_definicion:
                continue
            if "ESTÁNDARES MARCO" in s.upper() or "EVALUACIÓN QUINQUENAL" in s.upper():
                break
            definicion.append(s)
        if cur_comp is not None and definicion:
            entrada = componentes.get(cur_comp["codigo"])
            if entrada is not None and not entrada["definicion"]:
                marcar(entrada, definicion[0])
                for linea_def in definicion[1:]:
                    marcar(entrada, linea_def, cola=True)
                entrada["definicion"] = limpiar(" ".join(definicion))

        # --- cuerpo de la matriz ---
        for line in lineas[hi + 1 :]:
            if not line.strip():
                continue
            c0, c1, c2, c3 = (x.strip() for x in partir_linea(line, b1, b2, b3))
            std_anterior = cur_std
            nuevo_std = False

            if c0:
                m = RE_CRI.match(c0)
                if m:
                    cur_cri = {
                        "codigo": m.group(1),
                        "texto": limpiar(m.group(2)),
                        "dim": cur_dim,
                        "comp": cur_comp["codigo"] if cur_comp else None,
                        "paginas": [pagina],
                    }
                    criterios.append(cur_cri)
                    marcar(cur_cri, m.group(2))
                    cur_std = None
                    cur_ind = cur_evi = None
                elif cur_cri is not None:
                    if pagina not in cur_cri["paginas"]:
                        cur_cri["paginas"].append(pagina)
                    cur_cri["texto"] = limpiar(cur_cri["texto"] + " " + c0)
                    marcar(cur_cri, c0, cola=True)
                else:
                    incidencias.append({"tipo": "texto_criterio_sin_codigo", "pagina": pagina, "texto": c0[:120]})

            if c1:
                m = RE_STD.match(c1)
                if m:
                    nuevo_std = True
                    cur_std = {
                        "codigo": m.group(1),
                        "texto": limpiar(m.group(2)),
                        "dim": cur_dim,
                        "comp": cur_comp["codigo"] if cur_comp else None,
                        "criterio": cur_cri["codigo"] if cur_cri else None,
                        "paginas": [pagina],
                        "indicadores": [],
                        "evidencias": [],
                        "avisos": [],
                    }
                    estandares.append(cur_std)
                    marcar(cur_std, m.group(2))
                    cur_ind = cur_evi = None
                elif cur_std is not None:
                    if pagina not in cur_std["paginas"]:
                        cur_std["paginas"].append(pagina)
                    cur_std["texto"] = limpiar(cur_std["texto"] + " " + c1)
                    marcar(cur_std, c1, cola=True)
                else:
                    incidencias.append({"tipo": "texto_estandar_sin_codigo", "pagina": pagina, "texto": c1[:120]})

            if c2:
                if cur_std is None:
                    incidencias.append(
                        {"tipo": "indicador_sin_estandar", "pagina": pagina, "texto": c2[:120], "estandar": None}
                    )
                elif c2.startswith("\u2022"):
                    texto = limpiar(c2[1:])
                    cur_std["indicadores"].append(
                        {
                            "texto": texto,
                            "pagina": pagina,
                            "pagina_ultima": pagina,
                            "vineta": True,
                            "observaciones": [],
                        }
                    )
                    cur_ind = cur_std["indicadores"][-1]
                    marcar(cur_ind, c2[1:])
                    if not texto:
                        incidencias.append(
                            {
                                "tipo": "vineta_indicador_sin_texto",
                                "pagina": pagina,
                                "estandar": cur_std["codigo"],
                            }
                        )
                elif cur_ind is not None:
                    cur_ind["texto"] = limpiar(cur_ind["texto"] + " " + c2)
                    cur_ind["pagina_ultima"] = pagina
                    marcar(cur_ind, c2, cola=True)
                else:
                    # Sin vineta y sin indicador activo. Dos casos distintos de la fuente:
                    #  (a) la ultima linea del indicador del estandar ANTERIOR queda en la
                    #      fila del estandar nuevo (paginas 102 y 170): se reensambla el
                    #      indicador anterior y se marca pendiente_revision;
                    #  (b) celda propia sin vineta en la fuente (pagina 78): se crea como
                    #      indicador pendiente_revision del estandar nuevo.
                    cola = None
                    if (
                        nuevo_std
                        and std_anterior is not None
                        and std_anterior["indicadores"]
                        and not RE_TERMINADOR.search(std_anterior["indicadores"][-1]["texto"])
                        and c2[:1].islower()
                    ):
                        cola = std_anterior["indicadores"][-1]
                    if cola is not None:
                        cola["texto"] = limpiar(cola["texto"] + " " + c2)
                        cola["pagina_ultima"] = pagina
                        marcar(cola, c2, cola=True)
                        cola["observaciones"].append(
                            f"ultima linea del indicador impresa en la fila del estandar "
                            f"{cur_std['codigo']} (pagina {pagina}); verificar contra el PDF"
                        )
                        incidencias.append(
                            {
                                "tipo": "indicador_reensamblado_en_fila_siguiente",
                                "pagina": pagina,
                                "estandar_anterior": std_anterior["codigo"],
                                "estandar_nuevo": cur_std["codigo"],
                                "texto": c2[:120],
                            }
                        )
                    else:
                        cur_std["indicadores"].append(
                            {
                                "texto": limpiar(c2),
                                "pagina": pagina,
                                "pagina_ultima": pagina,
                                "vineta": False,
                                "observaciones": [
                                    "celda de indicador sin vineta en la fuente; verificar si contiene "
                                    "uno o varios indicadores"
                                ],
                            }
                        )
                        cur_ind = cur_std["indicadores"][-1]
                        marcar(cur_ind, c2)
                        incidencias.append(
                            {
                                "tipo": "indicador_sin_vineta",
                                "pagina": pagina,
                                "estandar": cur_std["codigo"],
                                "texto": c2[:120],
                            }
                        )

            if c3:
                if cur_std is None:
                    incidencias.append(
                        {"tipo": "evidencia_sin_estandar", "pagina": pagina, "texto": c3[:120], "estandar": None}
                    )
                elif c3[0] in "\u2212\u2013\u2014":
                    texto = limpiar(c3[1:])
                    cur_std["evidencias"].append({"texto": texto, "pagina": pagina, "vineta": True})
                    cur_evi = cur_std["evidencias"][-1]
                    marcar(cur_evi, c3[1:])
                    if not texto:
                        incidencias.append(
                            {
                                "tipo": "vineta_evidencia_sin_texto",
                                "pagina": pagina,
                                "estandar": cur_std["codigo"],
                            }
                        )
                elif cur_evi is not None:
                    cur_evi["texto"] = limpiar(cur_evi["texto"] + " " + c3)
                    marcar(cur_evi, c3, cola=True)
                else:
                    # Rotulo/cola de evidencia sin vineta: no se inventa una evidencia.
                    incidencias.append(
                        {
                            "tipo": "evidencia_inicio_invalido",
                            "pagina": pagina,
                            "estandar": cur_std["codigo"],
                            "texto": c3[:120],
                        }
                    )
                    cur_std["avisos"].append(
                        f"anomalia en la celda de evidencias (pagina {pagina}): {limpiar(c3)[:60]}"
                    )
                    if cur_ind is not None:
                        cur_ind["observaciones"].append(
                            f"posible contaminacion del texto por la columna de evidencias "
                            f"(pagina {pagina}); verificar contra el PDF"
                        )

    return {
        "dimensiones": dimensiones,
        "componentes": componentes,
        "criterios": criterios,
        "estandares": estandares,
        "incidencias": incidencias,
        "avisos_pagina": avisos_pagina,
        "paginas_no_matriz": paginas_no_matriz,
        "paginas_limites_heredados": paginas_limites_heredados,
        "paginas_limites_cabecera": paginas_limites_cabecera,
    }


# --------------------------------------------------------------------------
# Emision del dataset normalizado
# --------------------------------------------------------------------------


def construir_registros(parsed: dict) -> list[dict]:
    registros: list[dict] = []
    claves_usadas: set[str] = set()

    def clave_unica(nivel: str, codigo: str, padre: str | None) -> str:
        clave = f"{PREFIJOS[nivel]}:{codigo}"
        if clave in claves_usadas:
            clave = f"{clave}@{padre}"
        base_clave = clave
        n = 2
        while clave in claves_usadas:
            clave = f"{base_clave}#{n}"
            n += 1
        claves_usadas.add(clave)
        return clave

    def base(nivel, clave, codigo, texto, padre, orden, pagina, estado, observaciones, extra=None):
        reg = {
            "clave": clave,
            "nivel": nivel,
            "codigo": codigo,
            "texto_original": texto,
            "padre": padre,
            "orden": orden,
            "nivel_jerarquico": NIVELES.index(nivel) + 1,
            "version_marco": VERSION_MARCO,
            "origen": {
                "pdf_pagina": pagina,
                "pagina_documento": pagina - DESPLAZAMIENTO_PAGINA_DOCUMENTO,
                "seccion": "Matriz de estandares",
            },
            "estado": estado,
            "observaciones": observaciones,
        }
        if extra:
            reg["origen"].update(extra)
        return reg

    # Dimensiones en orden de aparicion en el documento
    for i, (codigo, dim) in enumerate(parsed["dimensiones"].items(), start=1):
        observaciones = [] if dim["nombre"] else ["nombre vacio en la extraccion"]
        registros.append(
            base(
                "dimension",
                clave_unica("dimension", codigo, None),
                codigo,
                dim["nombre"],
                None,
                i,
                dim["paginas"][0],
                "pendiente_revision" if observaciones else "confirmado",
                observaciones,
            )
        )

    # Componentes
    orden_dim: dict[str, int] = {}
    for codigo in sorted(parsed["componentes"], key=lambda c: (int(c.split(".")[0]), int(c.split(".")[1]))):
        comp = parsed["componentes"][codigo]
        orden_dim[comp["dim"]] = orden_dim.get(comp["dim"], 0) + 1
        observaciones = list(comp.get("observaciones", []))
        if not comp["nombre"]:
            observaciones.append("nombre vacio en la extraccion")
        registros.append(
            base(
                "componente",
                clave_unica("componente", codigo, f"dim:{comp['dim']}"),
                codigo,
                comp["nombre"],
                f"dim:{comp['dim']}",
                orden_dim[comp["dim"]],
                comp["paginas"][0],
                "pendiente_revision" if observaciones else "confirmado",
                observaciones,
                extra={"definicion": comp["definicion"]},
            )
        )

    # Criterios
    orden_cri: dict[str, int] = {}
    cri_claves: dict[str, str] = {}
    for cri in parsed["criterios"]:
        comp = cri["comp"]
        orden_cri[comp] = orden_cri.get(comp, 0) + 1
        observaciones = list(cri.get("observaciones", []))
        prefijo = ".".join(cri["codigo"].split(".")[:2])
        if comp and prefijo != comp:
            observaciones.append(f"el codigo no corresponde al componente en contexto ({comp})")
        if not cri["texto"]:
            observaciones.append("texto vacio en la extraccion")
        clave_cri = clave_unica("criterio", cri["codigo"], f"comp:{comp}")
        cri_claves.setdefault(cri["codigo"], clave_cri)
        registros.append(
            base(
                "criterio",
                clave_cri,
                cri["codigo"],
                cri["texto"],
                f"comp:{comp}",
                orden_cri[comp],
                cri["paginas"][0],
                "pendiente_revision" if observaciones else "confirmado",
                observaciones,
            )
        )

    # Estandares
    orden_std: dict[str, int] = {}
    for std in parsed["estandares"]:
        cri = std["criterio"]
        orden_std[cri] = orden_std.get(cri, 0) + 1
        observaciones = list(std.get("avisos", [])) + list(std.get("observaciones", []))
        prefijo = ".".join(std["codigo"].split(".")[:2])
        if std["comp"] and prefijo != std["comp"]:
            observaciones.append(f"el codigo no corresponde al componente en contexto ({std['comp']})")
        if cri and not std["codigo"].startswith(cri + "."):
            observaciones.append(f"el codigo no corresponde al criterio en contexto ({cri})")
        if not std["texto"]:
            observaciones.append("texto vacio en la extraccion")
        clave_std = clave_unica("estandar", std["codigo"], f"cri:{cri}")
        clave_cri = cri_claves.get(cri, f"cri:{cri}")
        registros.append(
            base(
                "estandar",
                clave_std,
                std["codigo"],
                std["texto"],
                clave_cri,
                orden_std[cri],
                std["paginas"][0],
                "pendiente_revision" if observaciones else "confirmado",
                observaciones,
                extra={
                    "paginas": std["paginas"],
                    "limites_columnas": (
                        "heredado"
                        if any(p in parsed["paginas_limites_heredados"] for p in std["paginas"])
                        else "contenido"
                    ),
                },
            )
        )

        # Indicadores: la fuente oficial no define codigo
        for i, ind in enumerate(std["indicadores"], start=1):
            observaciones_ind = list(ind.get("observaciones", []))
            if not ind["texto"]:
                observaciones_ind.append("vineta sin texto en la fuente (celda vacia); verificar contra el PDF")
            registros.append(
                base(
                    "indicador",
                    clave_unica("indicador", f"{std['codigo']}#{i}", clave_std),
                    "",
                    ind["texto"],
                    clave_std,
                    i,
                    ind["pagina"],
                    "pendiente_revision" if observaciones_ind else "confirmado",
                    observaciones_ind,
                    extra={"pagina_ultima": ind["pagina_ultima"], "con_vineta": ind["vineta"]},
                )
            )

        # Evidencias: sin codigo y sin asociacion evidencia->indicador determinable
        for i, evi in enumerate(std["evidencias"], start=1):
            observaciones_evi = [
                "sin codigo oficial en la fuente",
                "asociacion evidencia->indicador no determinable desde la matriz; "
                "se conserva asociada a su estandar",
            ]
            observaciones_evi.extend(std.get("avisos", []))
            observaciones_evi.extend(evi.get("observaciones", []))
            if not evi["texto"]:
                observaciones_evi.append("vineta sin texto en la fuente (celda vacia); verificar contra el PDF")
            registros.append(
                base(
                    "evidencia",
                    clave_unica("evidencia", f"{std['codigo']}#{i}", clave_std),
                    "",
                    evi["texto"],
                    clave_std,
                    i,
                    evi["pagina"],
                    "pendiente_revision",
                    observaciones_evi,
                )
            )

    return registros


def conteos(registros: list[dict]) -> dict:
    resumen = {}
    for nivel in NIVELES:
        del_nivel = [r for r in registros if r["nivel"] == nivel]
        resumen[nivel] = {
            "total": len(del_nivel),
            "confirmados": sum(1 for r in del_nivel if r["estado"] == "confirmado"),
            "pendientes": sum(1 for r in del_nivel if r["estado"] == "pendiente_revision"),
        }
    return resumen


def escribir_salidas(outdir: Path, registros: list[dict], meta: dict) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    dataset = {"meta": meta, "registros": registros}
    (outdir / "eq_sidaces_normalized.json").write_text(
        json.dumps(dataset, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    pendientes = [r for r in registros if r["estado"] == "pendiente_revision"]
    (outdir / "eq_sidaces_pending_review.json").write_text(
        json.dumps({"meta": meta, "registros": pendientes}, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    columnas = [
        "clave",
        "nivel",
        "codigo",
        "texto_original",
        "padre",
        "orden",
        "nivel_jerarquico",
        "version_marco",
        "pdf_pagina",
        "pagina_documento",
        "estado",
        "observaciones",
    ]
    with (outdir / "eq_sidaces_normalized.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(columnas)
        for reg in registros:
            writer.writerow(
                [
                    reg["clave"],
                    reg["nivel"],
                    reg["codigo"],
                    reg["texto_original"],
                    reg["padre"] or "",
                    reg["orden"],
                    reg["nivel_jerarquico"],
                    reg["version_marco"],
                    reg["origen"]["pdf_pagina"],
                    reg["origen"]["pagina_documento"],
                    reg["estado"],
                    " | ".join(reg["observaciones"]),
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, help="Ruta al PDF oficial")
    parser.add_argument("--outdir", default="data/catalogo", help="Directorio de salida")
    parser.add_argument(
        "--layout-cache",
        default="",
        help="JSON opcional con el texto en modo layout ya extraido (evita re-leer el PDF)",
    )
    args = parser.parse_args()

    if args.layout_cache and Path(args.layout_cache).exists():
        paginas = json.loads(Path(args.layout_cache).read_text(encoding="utf-8"))
    else:
        paginas = extraer_paginas(Path(args.pdf))

    parsed = parsear(paginas)
    registros = construir_registros(parsed)

    meta = {
        "fuente_pdf": Path(args.pdf).name,
        "version_marco": VERSION_MARCO,
        "norma": "Resolucion 27-2019 del CONESCyT (27/09/2019)",
        "herramienta_extraccion": "pypdf modo layout + scripts/extraer_eq_sidaces.py",
        "niveles": NIVELES,
        "conteos_extraidos": conteos(registros),
        "conteos_referencia": CONTEOS_REFERENCIA["texto_seccion_2_3"],
        "conteos_referencia_figura_2": CONTEOS_REFERENCIA["figura_2"],
        "notas_extraccion": [
            "El texto se normaliza colapsando espacios multiples; la justificacion del PDF "
            "puede haber dejado palabras partidas en algunas celdas (ver incidencias).",
            "Indicadores y evidencias no tienen codigo en la fuente: el dataset los deja vacios.",
            "La asociacion evidencia->indicador no es determinable desde la matriz: todas las "
            "evidencias quedan en estado pendiente_revision asociadas a su estandar.",
            "Las definiciones de dimension no se extraen (viven en paginas separadas sin "
            "cabecera de matriz): el campo definicion de dimension queda vacio por diseño.",
            f"Paginas sin cabecera de matriz (portadas de dimension, blancas, bibliografia): "
            f"{len(parsed['paginas_no_matriz'])}.",
            f"Paginas con limites de columna heredados de la pagina anterior: "
            f"{parsed['paginas_limites_heredados']}.",
            f"Paginas con limites derivados de la cabecera de tabla: "
            f"{parsed['paginas_limites_cabecera']}.",
        ],
        "incidencias": parsed["incidencias"],
        "avisos_pagina": parsed["avisos_pagina"],
        "paginas_no_matriz": parsed["paginas_no_matriz"],
    }

    escribir_salidas(Path(args.outdir), registros, meta)

    resumen = meta["conteos_extraidos"]
    print(f"Registros emitidos: {len(registros)}")
    for nivel in NIVELES:
        dato = resumen[nivel]
        print(
            f"  {nivel:11s} total={dato['total']:4d} "
            f"confirmados={dato['confirmados']:4d} pendientes={dato['pendientes']:4d}"
        )
    print(f"Incidencias: {len(parsed['incidencias'])}")
    for inc in parsed["incidencias"]:
        print("   -", inc)
    print("Salidas en", args.outdir)


if __name__ == "__main__":
    main()
