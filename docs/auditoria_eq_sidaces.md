# Auditoría EQ-SIDACES — fuente PDF y dataset normalizado

Estado: **auditoría completada, dataset generado, pendiente de revisión institucional antes de importar.**
Este documento registra qué se extrajo, con qué método, qué discrepancias existen y por qué
ninguna se corrigió automáticamente.

---

## 1. Fuente y método

| Ítem | Detalle |
|---|---|
| Fuente | `docs/Estándares Marco EQ-SIDACES (Versión Final).pdf` (201 páginas, entrega oficial; ignorada por `.gitignore`) |
| Norma | Resolución 27-2019 del CONESCyT (27/09/2019) |
| Matriz oficial | PDF páginas 50–194 (136 páginas con cabecera `Criterios/Estándares/Indicadores/Evidencias`) |
| Offset | página_documento = pdf_pagina − 12 (PDF 50 = documento 38) |
| Extracción | `pypdf` 6.20.0 en modo `layout` (conserva las 4 columnas de la matriz) |
| Script reproducible | `scripts/extraer_eq_sidaces.py` |

Reproducción:

```powershell
pip install pypdf
python scripts/extraer_eq_sidaces.py --pdf "docs/Estándares Marco EQ-SIDACES (Versión Final).pdf" --outdir data/catalogo
```

Método del parser:

- Los límites de columna (Criterios | Estándares | Indicadores | Evidencias) se derivan de la
  posición real del contenido de cada página; si una página no trae códigos nuevos se heredan de
  la anterior (páginas 119, 136, 139, 144, 146, 147, 155, 182) y se marca
  `origen.limites_columnas = "heredado"`.
- Páginas sin cabecera de matriz (portadas de dimensión, en blanco, bibliografía): 1–49, 73, 101,
  113, 131, 150–151, 162–163, 183, 195–201 (no aportan registros).
- El texto se normaliza colapsando espacios múltiples. **No se corrigen** quiebres de
  justificación, códigos ambiguos ni textos vacíos: se marcan `estado = pendiente_revision` con
  observación.

## 2. Conteos: extraídos vs referencias

| Nivel | Extraídos | Texto §2.3 (pág. 33) | Δ | Figura 2 (pág. 25) | Δ |
|---|---:|---:|---:|---:|---:|
| Dimensión | **8** | 8 | 0 | 8 | 0 |
| Componente | **36** | 36 | 0 | 36 | 0 |
| Criterio | **77** | 77 | 0 | 77 | 0 |
| Estándar | **211** (209 códigos únicos) | 210 | +1 | 212 | −1 |
| Indicador | **923** (921 con viñeta + 2 celdas sin viñeta) | 909 | +14 | 915 | +8 |
| Evidencia | **1097** (viñetas crudas; 9 sin texto) | 915 | +182 | 1082 | +15 |

- Dimensión, componente y criterio coinciden **exactamente** con ambas referencias.
- Estándares: la fuente imprime 211 filas de estándar; dos códigos aparecen impresos dos veces en
  contextos distintos (ver §3.1). Ni 210 ni 212 explica por sí solo las 211 filas: la
  reconciliación requiere revisión manual; **no se ajustó ningún conteo**.
- Indicadores: el conteo crudo de viñetas de la columna 3 es 921; se detectaron además 2 celdas
  sin viñeta (§3.2) → 923. No coincide con 909 ni con 915 → revisión manual.
- Evidencias: el conteo crudo de la columna 4 es 1097 (incluye 9 viñetas sin texto, §3.4). No
  coincide con 915 ni con 1082 → revisión manual. Además la asociación evidencia→indicador no es
  determinable desde la matriz (§4).

## 3. Anomalías estructurales de la fuente

Todas quedaron marcadas `pendiente_revision`; ninguna se corrigió.

### 3.1 Estándares con código fuera de contexto (3)

| Código impreso | Aparece bajo | Página PDF | Observación |
|---|---|---|---|
| `1.2.3.1` | criterio 1.3.1 (comp. 1.3) | 56 | duplicado: también existe bajo 1.2.3 (pág. 55), que sí es coherente |
| `1.2.3.2` | criterio 1.3.1 (comp. 1.3) | 56 | solo existe en ese contexto; no se alteró el código |
| `2.6.1.1` | criterio 2.3.3 (comp. 2.3) | 82 | duplicado: también existe bajo 2.6.1 (pág. 93), que sí es coherente |

Reglas aplicadas: si el prefijo del código no corresponde al componente/criterio en contexto →
`pendiente_revision` con la razón. El registro legítimo permanece `confirmado`.

### 3.2 Celdas de indicador sin viñeta (pág. 78, estándares 2.2.1.3 y 2.2.1.4)

La fuente omite el `•` en esas dos celdas (el resto de la página sí lo trae). Se conservaron como
indicadores `pendiente_revision` con la observación "celda de indicador sin vineta en la fuente;
verificar si contiene uno o varios indicadores". Ambas celdas incluyen fórmula y leyenda
(`PI/DI/TD`, `PV/DV/TD`) dentro del texto.

### 3.3 Colas de indicador impresas en la fila del estándar siguiente (2)

| Indicador reensamblado | Página | Fracción que apareció en la fila de |
|---|---|---|
| `3.1.1.1` IND7 → "…normativas **de investigación.**" | 102 | estándar 3.1.1.2 |
| `7.1.6.1` IND5 → "…dimensiones **apropiadas para su uso.**" | 170 | estándar 7.1.6.2 |

El parser detecta el caso (nuevo estándar en la misma línea + texto del indicador anterior sin
punto final + arranque en minúscula), reensambla el indicador anterior y lo marca
`pendiente_revision` para verificación contra el PDF.

### 3.4 Rótulos de evidencia sin viñeta (pág. 90, estándar 2.5.2.2)

Los rótulos `Archivo físico:` / `Archivo digital:` de la columna 4 aparecen sin `−` y contaminan:

- `2.5.2.2` IND1 → "Las condiciones ambientales son apropiadas para **Archivo físi** preservar la
  información de los estudiantes." (`pendiente_revision`),
- el estándar `2.5.2.2` (observación en el registro) y sus evidencias (EV4 conserva
  "Archivo digital:" pegado),
- el remanente `co:` se registró como incidencia `evidencia_inicio_invalido`; **no** se inventó
  una evidencia para él.

### 3.5 Viñetas sin texto (11)

9 viñetas de evidencia (págs. 52, 53, 82, 116, 164, 175, 180×2, 188) y 2 de indicador
(págs. 180, 189) traen el guion/viñeta pero ninguna celda de texto. Se conservaron como registros
con texto vacío y observación "viñeta sin texto en la fuente (celda vacia)"; las de indicador
quedan `pendiente_revision` (las evidencias ya lo son por §4).

### 3.6 Incidencias del parser (16 en total)

`vineta_evidencia_sin_texto` ×9, `indicador_sin_vineta` ×2, `indicador_reensamblado_en_fila_siguiente` ×2,
`vineta_indicador_sin_texto` ×2, `evidencia_inicio_invalido` ×1. Completan las de §3.5–3.4.

## 4. Indicadores y evidencias no tienen código oficial

- En todo el PDF **no existe ningún código de 5 segmentos**: los indicadores y evidencias solo
  llevan viñetas (`•` / `−`) en las columnas 3 y 4. Por eso el campo `codigo` queda vacío en el
  dataset para esos niveles (y `IndicadorMarco`/`EvidenciaIndicativa` exigen
  `codigo_completo` único: el importador usará códigos sintéticos solo con
  `--allow-synthetic-codes`, documentados como no oficiales).
- La obligatoriedad de las evidencias no está declarada en la fuente → `obligatoria = None`.
- La asociación evidencia→indicador **no es determinable** desde la matriz (la viñeta está a nivel
  de fila del estándar, no por indicador): las 1097 evidencias quedan `pendiente_revision`
  asociadas a su estándar y **no se importan** en esta fase.

## 5. Quiebres de justificación del PDF

La justificación del documento parte palabras en algunas celdas (p. ej. `gestió n`,
`socieda d`, `implementa r`, `of erta`, `procedimient os`). El parser aplica dos heurísticas:

1. hueco de 2+ espacios seguido de un fragmento de ≤4 letras no legítimo dentro de la misma línea;
2. continuación de línea que arranca con un fragmento de ≤4 letras no legítimo.

Con un stoplist de palabras cortas legítimas (verificado manualmente contra los casos detectados),
quedaron marcados **52 registros** con la observación "posible palabra partida por la
justificación del PDF (fragmento '…')": 1 criterio, 6 estándares, 13 indicadores y 32 evidencias.
Ejemplos: `cri:4.4.1` ("implementa r"), `std:4.4.2.1` ("of erta"), `ind:2.3.2.1#3` ("socieda d").

**Límites conocidos de la heurística** (declarados, no corregidos):

- solo detecta fragmentos de ≤4 letras: quiebres con fragmentos más largos
  (p. ej. `identi fica`) pueden quedar sin marcar;
- el texto ya normalizado pierde la señal de espacios múltiples, así que la detección es
  conservadora por diseño: **un registro `confirmado` puede conservar aún un quiebre no detectado**;
- por ello se recomienda muestreo manual antes del import definitivo.

## 6. Estado final del dataset

`data/catalogo/eq_sidaces_normalized.json` — 2352 registros:

| Nivel | Total | confirmados | pendientes |
|---|---:|---:|---:|
| Dimensión | 8 | 8 | 0 |
| Componente | 36 | 36 | 0 |
| Criterio | 77 | 76 | 1 |
| Estándar | 211 | 201 | 10 |
| Indicador | 923 | 903 | 20 |
| Evidencia | 1097 | 0 | 1097 |
| **Total** | **2352** | **1224** | **1128** |

Pendientes estructurales (fuera de los 52 por quiebre): 4 estándares (§3.1 + §3.4) y 7
indicadores (2 × §3.2, 2 × §3.3, 1 × §3.4, 2 × §3.5). Las 1097 evidencias son pendientes por §4.

Verificaciones automáticas del dataset (todas OK): claves únicas, jerarquía resuelta
(padre existe y es del nivel correcto), coherencia de prefijos para `confirmados`, órdenes
contiguos por (nivel, padre), `pagina_documento = pdf_pagina − 12`.

## 7. Salidas generadas

| Archivo | Contenido |
|---|---|
| `data/catalogo/eq_sidaces_normalized.json` | dataset completo (`meta` + `registros`) |
| `data/catalogo/eq_sidaces_normalized.csv` | misma información en formato plano |
| `data/catalogo/eq_sidaces_pending_review.json` | solo los 1128 registros `pendiente_revision` |

Esquema de registro: `clave`, `nivel`, `codigo` (vacío en indicador/evidencia), `texto_original`,
`padre` (clave del padre), `orden`, `nivel_jerarquico`, `version_marco`
(`EQ-SIDACES-2019-Res27-2019`), `origen.{pdf_pagina, pagina_documento, seccion, …}`, `estado`,
`observaciones[]`. `meta` incluye `conteos_extraidos`, ambas referencias, `incidencias`,
`avisos_pagina`, `paginas_no_matriz` y `notas_extraccion`.

## 8. Restricciones respetadas en esta fase

- No se importó nada a PostgreSQL; la BD real no se tocó.
- No se modificaron modelos operativos ni sus relaciones; no se conectó `IndicadorMarco` con
  `evaluation.Indicador`/`Asignacion`; no se eliminó la app heredada `evidencias`.
- No se corrigieron códigos ambiguos, ni se eliminaron/ajustaron registros para igualar
  conteos: las discrepancias se reportan y exigen revisión.
- No se inventó información (sin códigos de indicador/evidencia, sin obligatoriedad, sin
  definiciones de dimensión — viven en páginas separadas sin cabecera de matriz y quedan pendientes).
- Los datos existentes no se eliminaron.

## 9. Pendientes para la siguiente fase

1. Revisión institucional de `eq_sidaces_pending_review.json` (1128 registros) contra el PDF.
2. Reconciliación manual de conteos (211/923/1097 vs 210/909/915 y vs 212/915/1082).
3. Decidir el criterio de asociación evidencia→indicador (hoy todas quedan asociadas al estándar).
4. Extraer las definiciones de dimensión desde las páginas de separación.
5. Importación real con `import_eq_sidaces` (solo tras revisión y con la aprobación que corresponda).
