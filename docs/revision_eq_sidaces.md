# Revisión asistida EQ-SIDACES — pendientes, conteos y relación evidencia↔indicador

Estado: **informe listo para revisión. No se corrigió, ni importó, ni modificó ningún dato.**
Archivos generados en esta fase:

| Archivo | Descripción |
|---|---|
| `data/catalogo/eq_sidaces_revision.csv` | archivo de trabajo de revisión (1128 filas, 21 columnas) |
| `scripts/revisar_eq_sidaces.py` | generador reproducible del archivo de trabajo |
| `docs/revision_eq_sidaces.md` | este informe |

Los normalizados originales (`eq_sidaces_normalized.json/.csv`, `eq_sidaces_pending_review.json`)
**no fueron modificados** (mtime sin cambios: 14/10/2026 17:04).

---

## 1. Informe de pendientes agrupados por causa

Método: clasificación de los 1128 registros `pendiente_revision` por su(s) observación(es) del
dataset (`eq_sidaces_pending_review.json`). Cada observación cae en exactamente una categoría;
las categorías **no son excluyentes entre registros** (un registro con dos observaciones de tipos
distintos cuenta en ambas).

| Categoría | Registros | Niveles | Ubicación / ejemplo |
|---|---:|---|---|
| Evidencia sin asociación inequívoca | 1097 | evidencia | todas las evidencias; observación base "asociacion evidencia->indicador no determinable desde la matriz" |
| Posible palabra partida por la justificación | 52 | 1 criterio, 6 estándares, 13 indicadores, 32 evidencias | p. ej. `cri:4.4.1` (fragmento 'r'), `std:4.4.2.1` ('of erta') |
| Texto contaminado por rótulos de evidencia | 12 | 1 estándar, 1 indicador, 10 evidencias | pág. 90: `std:2.5.2.2`, `ind:2.5.2.2#1` ("Archivo físi…"), evidencias del mismo estándar |
| Viñeta sin texto | 9 | 7 evidencias, 2 indicadores | pág. 52 `evi:1.1.2.2#5` vacío; `ind:7.3.1.2#5` (pág. 180) |
| Código fuera de contexto | 3 | 3 estándares | pág. 56 `std:1.2.3.1@cri:1.3.1` y `std:1.2.3.2`; pág. 82 `std:2.6.1.1` |
| Celda de indicador sin viñeta | 2 | 2 indicadores | pág. 78 `ind:2.2.1.3#1`, `ind:2.2.1.4#1` |
| Indicador reensamblado entre filas | 2 | 2 indicadores | pág. 102 `ind:3.1.1.1#7`, pág. 170 `ind:7.1.6.1#5` |
| Otras anomalías | 0 | — | ninguna observación quedó sin clasificar |
| **Suma de categorías** | **1177** | | ≠ registros únicos |

**Solapamientos (verificado, no supuesto):**

- Registros únicos pendientes: **1128** (1097 evidencias + 20 indicadores + 10 estándares + 1 criterio).
- Registros en **exactamente una** categoría: 1079.
- Registros en **exactamente dos** categorías: 49 (todas evidencias):
  32 evidencia+palabra partida, 10 evidencia+texto contaminado, 7 evidencia+viñeta sin texto.
- Registros en tres o más categorías: 0.
- Por eso 1177 (suma) − 1128 (únicos) = 49 = los registros contados dos veces.

**Las incidencias del parser (16 eventos) tampoco son registros:**

- 9 `vineta_evidencia_sin_texto` → solo 7 registros quedaron vacíos; 2 recibieron un residual de
  continuación: `evi:1.2.1.3#6` = "el" (pág. 53) y `evi:7.2.1.2#4` = "a" (pág. 175).
- 2 `vineta_indicador_sin_texto` → 2 registros vacíos.
- 2 `indicador_sin_vineta` + 2 `indicador_reensamblado_en_fila_siguiente` + 1
  `evidencia_inicio_invalido` (`co:`, pág. 90; sin registro: no se inventó una evidencia).
- Los 3 estándares con código fuera de contexto llevan **dos** observaciones cada uno (componente
  y criterio), no una incidencia de parser sino una regla de validación.

(`docs/auditoria_eq_sidaces.md` §3.5 fue corregido para reflejar los 7 vs 9 registros vacíos.)

## 2. Archivo de trabajo para revisión manual

**`data/catalogo/eq_sidaces_revision.csv`** — generado por
`python scripts/revisar_eq_sidaces.py` (lee el PDF si no se pasa `--layout`; ~50 s; verificado
que reproduce los mismos 921/1097 viñetas que el parser).

- **1128 filas**, ordenadas por `pagina_pdf`, luego nivel jerárquico y orden.
- Codificación UTF-8 con BOM (se abre directo en Excel).
- Columnas:
  - Identificación: `orden_revision`, `pagina_pdf`, `pagina_documento`, `clave`, `nivel`, `codigo`.
  - Contexto: `padre_clave`, `padre_codigo`, `padre_texto`, `hermanos` (clave y texto truncado de
    los registros del mismo padre), `indicadores_del_estandar` (solo filas de evidencia: claves
    de los indicadores del estándar padre).
  - Motivo: `motivos` (categorías de §1), `observaciones_fuente` (observaciones literales),
    `estado_actual`.
  - Inferencia (solo evidencias): `indicador_sugerido_linea` (clave `ind:…` existente, **sintética
    y no oficial**, derivada de la misma línea) y `criterio_asociacion`
    (`misma_linea` | `linea_adyacente` | `sin_correspondencia`).
  - Revisión (vacías hasta ser llenadas): `decision`, `texto_corregido`, `padre_confirmado`,
    `observaciones_revision`.
- **Valores de `decision`**: `confirmar` | `corregir` | `pendiente`.
  - `confirmar`: el texto/padre del dataset es correcto tal cual.
  - `corregir`: completar `texto_corregido` (y/o `padre_confirmado`) con la corrección propuesta.
  - `pendiente`: requiere una segunda opinión o falta información.
- **Trazabilidad**: toda corrección propuesta vive **solo en este CSV** (o en una copia del
  mismo). Los normalizados originales no se editan; la aplicación de lo revisado será un paso
  posterior y separado.

**Apertura del PDF para contrastar cada caso** (verificado en este entorno):

- El archivo existe en `docs/` (`Estándares Marco EQ-SIDACES (Versión Final).pdf`, 2.272.431 bytes).
- Abrirlo: `Start-Process (Get-ChildItem docs\*.pdf).FullName` (visor predeterminado de Windows).
- Navegación manual con la columna `pagina_pdf` (el número que muestra el visor);
  `pagina_documento = pagina_pdf − 12`. No se afirma apertura automática por página: no está
  verificada, así que no se ofrece.

## 3. Análisis de los conteos discrepantes

### Hechos verificados (con método)

**Estándares = 211 filas / 209 códigos únicos.**

- Método A: parser del extractor (celdas con código de 4 segmentos).
- Método B: recuento independiente de segmentos de fila en el layout del PDF → **211** (idéntico).
- Códigos únicos: 209. Duplicados (los4 registros):

| Código | Página PDF | Contexto (criterio) | Estado |
|---|---|---|---|
| `1.2.3.1` | 55 | 1.2.3 | confirmado |
| `1.2.3.1` | 56 | 1.3.1 | pendiente |
| `2.6.1.1` | 82 | 2.3.3 | pendiente |
| `2.6.1.1` | 93 | 2.6.1 | confirmado |

**Indicadores = 923 registros = 921 viñetas + 2 celdas sin viñeta (pág. 78).**

- Recuento independiente de viñetas `•` en la columna 3: **921** (idéntico al parser).
- Los 923 incluyen 2 viñetas con texto vacío (págs. 180 y 189): con texto = 921.
- Las 2 colas reensambladas (págs. 102/170) no alteran el total: se concatenaron a su indicador.

**Evidencias = 1097 viñetas.**

- Recuento independiente de viñetas `−` en la columna 4: **1097** (idéntico al parser).
- 7 registros con texto vacío + 2 residuales ('el', 'a'); la celda `co:` (pág. 90) no generó
  registro (se contó como incidencia, no como evidencia).
- Todas las 211 filas tienen ≥1 evidencia; por estándar: mín. 1, máx. 21.

### Referencias oficiales verificadas en el PDF

| Referencia | Página PDF | Cifras |
|---|---|---|
| Texto narrativo (§2.3) | 33 | 8 / 36 / 77 / **210** estándares / **909** indicadores / **915** evidencias |
| Glosario con conteos entre paréntesis (la "Figura 2" del proyecto) | 25 | Dimensione (8), Componente (36), Criterio (77), Estándar (**212**), Indicador (**915**), Evidencia (**1082**) |

### Diferencias aritméticas (hechos)

| Nivel | Extraídos | Texto (pág. 33) | Δ | Glosario (pág. 25) | Δ |
|---|---:|---:|---:|---:|---:|
| Estándar | 211 | 210 | +1 | 212 | −1 |
| Indicador | 923 (921 viñetas) | 909 | +14 (+12) | 915 | +8 (+6) |
| Evidencia | 1097 | 915 | +182 | 1082 | +15 |

### Hipótesis (NO verificadas, NO aplicadas)

- **H1 (210):** el conteo oficial excluye una de las dos repeticiones de código
  (211 − 1 = 210). La aritmética coincide, pero no se conoce el criterio oficial de conteo.
- **H2 (212):** no se identificó una fila adicional en la matriz (recuento independiente = 211);
  podría deberse a una convención de conteo o a contenido fuera de la matriz. No resoluble sin
  conteo manual contra el PDF.
- **H3 (indicadores):** ni excluir las 2 celdas sin viñeta (921) ni excluir las 2 viñetas vacías
  (919) alcanza 915 o 909. Podrían existir indicadores visualmente fusionados (casos como los de
  págs. 102/170 muestran que la maquetación mezcla filas) o un criterio de conteo distinto.
- **H4 (evidencias):** 1097 − 1082 = 15 viñetas "de más" sin identificación unívoca; y el 915
  textual coincide exactamente con el Indicador del glosario → posible transcripción errónea en
  el texto narrativo.

Ninguna hipótesis se aplicó: los conteos y registros permanecen intactos. La reconciliación
definitiva requiere conteo manual (decisión institucional D1/D10).

## 4. Relación evidencia↔indicador — análisis y recomendación

### Lo que la fuente dice explícitamente (hechos documentales)

1. **Pág. 28 (metodología):** "Este tercer y último nivel de la matriz está integrado por el
   tercer par categorial matricial: **INDICADORES – EVIDENCIAS**." → la relación evidencia–
   indicador es explícita **a nivel conceptual** (par categorial del tercer nivel).
2. **Pág. 25 (glosario):** Evidencia = "Recurso, información o dato verificable … que **aluden al
   indicador y estándar** bajo examen…" → la fuente declara que la evidencia alude a **ambos**.
3. **En la matriz no existe asociación por ítem:** las evidencias usan viñeta `−` sin número ni
   referencia cruzada a un indicador concreto (verificado: 0 evidencias con viñeta de indicador
   embebida en su texto; ningún texto de evidencia cita un indicador).

### Lo que la estructura visual aporta (inferido por posición, NO explícito)

Recuento de correspondencia de líneas entre viñetas de indicador (`•`) y de evidencia (`−`)
en las 211 filas (misma lógica de columnas que el parser):

| Correspondencia de la viñeta de evidencia | Registros | % |
|---|---:|---:|
| Misma línea que una viñeta de indicador | 479 | 43.7% |
| Línea adyacente con una única viñeta de indicador | 10 | 0.9% |
| Sin correspondencia de línea | 608 | 55.4% |

Por estándar: 12 tienen **todas** sus evidencias en línea con un indicador, 197 solo **en parte**,
2 ninguna (pág. 78, donde los indicadores carecen de viñeta).

Incluso la "misma línea" es **inferencia por proximidad**: la adyacencia es ambigua porque los
textos se justifican en varias líneas (una evidencia en línea adyacente puede corresponder al
indicador anterior o al siguiente).

### Conclusión

- **Asociación al estándar: explícita** por posición de fila en la matriz (y es la que conserva
  el dataset: `padre = std:…`).
- **Asociación a un indicador específico: no determinable de forma automática** — no hay
  marcador explícito y la posición solo sugiere candidatos en 44% de los casos.
- **Asociación a "ambos": es la intención declarada** de la metodología (par INDICADORES–
  EVIDENCIAS, pág. 28), pero la matriz no materializa el vínculo por ítem.

### Recomendación sustentada

1. **Mantener, durante y después de la revisión, la asociación canónica al estándar**
   (`EvidenciaIndicativa.indicador_marco` sin poblar). Es la única relación respaldada por
   posición explícita y evita perder el anclaje de la evidencia.
2. **Conservar la señal inferida sin aplicarla:** las columnas `indicador_sugerido_linea` y
   `criterio_asociacion` del CSV de trabajo documentan la posición observada; no se copian al
   dataset.
3. **Decisión por fila, no automática:** quien revise puede registrar en `padre_confirmado` la
   asociación indicador↔evidencia cuando el PDF lo respalde; las claves usadas son las
   existentes `ind:…` (sintéticas, **no oficiales**; no se crea ningún código nuevo).
4. **Si la revisión confirma el criterio**, la asociación a indicador debe guardarse como dato
   derivado con procedencia (`inferido` vs `confirmado_por_revision`) que **no sustituya** el
   vínculo al estándar, preservando la trazabilidad.
5. **No asociar por defecto:** 608/1097 evidencias no tienen ninguna línea de indicador
   correspondiente; asociarlas por proximidad forzaría relaciones que la fuente no respalda.

## 5. Decisiones que requieren confirmación institucional

> Matriz operativa D1–D13 (pregunta, evidencia, opciones, recomendación técnica, responsable):
> `docs/decisiones_eq_sidaces.md`, junto con los lotes de revisión y el lote piloto.

| # | Decisión | Contexto |
|---|---|---|
| D1 | Criterio oficial de conteo de estándares: ¿211 filas, 210 o 212? | §3; hipótesis H1/H2 |
| D2 | Estándares duplicados (`1.2.3.1` pág. 55/56; `2.6.1.1` pág. 82/93): ¿dos entradas legítimas por contexto o error tipográfico? | 4 registros (2 pendientes, 2 confirmados) |
| D3 | `std:1.2.3.2` (solo aparece bajo el criterio 1.3.1, pág. 56): ¿código correcto? | no corregir sin decisión |
| D4 | Contenido de las 2 celdas de indicador sin viñeta (pág. 78): ¿cuántos indicadores contiene cada una? | 2 registros; texto con fórmula incluida |
| D5 | Pág. 90: recuperar el texto real de `ind:2.5.2.2#1` (contaminado con "Archivo físico") y decidir el destino del remanente `co:` (¿evidencia perdida?) | 12 registros afectados |
| D6 | Confirmar o rechazar el reensamblado de colas (págs. 102 y 170) | 2 indicadores |
| D7 | Texto de los 9 registros vacíos (7 evidencias + 2 indicadores) y de los 2 residuales ('el' pág. 53, 'a' pág. 175) | §1 |
| D8 | Criterio de asociación evidencia↔indicador (estándar / indicador / ambos) y su procedencia | §4; la más transversal |
| D9 | Confirmar el uso de códigos sintéticos **no oficiales** para indicadores/evidencias (`{std}-IND-NN`) y su etiquetado permanente | §4.3; importador `--allow-synthetic-codes` |
| D10 | Aprobar el uso de `--ack-discrepancias` pese a los conteos no reconciliados (D1) | bloquea `--dry-run/--apply` |
| D11 | Las 52 posibles palabras partidas: confirmar cada corrección textual vía CSV (`decision=corregir`) | 52 registros |
| D12 | Definiciones de dimensión: extraerlas de las páginas de separación o dejarlas vacías | limitación documentada |
| D13 | Tras importar: ¿quién y cuándo se activa la versión (`VersionMarcoEvaluacion.activo`, solo puede haber una activa)? | no se tocó el flag |

## 6. Protecciones verificadas en esta fase

- No se ejecutó `--apply`; no se modificó ninguna base de datos (las pruebas usan la BD de test).
- Modelos y relaciones operativas sin cambios; app `evidencias` heredada intacta.
- Normalizados originales sin tocar (verificado por mtime); las propuestas de corrección están
  solo en `eq_sidaces_revision.csv`.
- No se crearon códigos oficiales nuevos; las claves `ind:…`/`evi:…` siguen siendo sintéticas y
  marcadas como no oficiales en el importador.
- Pruebas en verde: `test catalogo` → 24 OK; suite de regresión completa → 211 OK.

## 7. Reproducibilidad

```powershell
# regenerar el dataset desde el PDF (no modifica nada hasta escribir salidas):
pip install pypdf
python scripts/extraer_eq_sidaces.py --pdf "docs/Estándares Marco EQ-SIDACES (Versión Final).pdf" --outdir data/catalogo

# regenerar el archivo de trabajo de revision:
python scripts/revisar_eq_sidaces.py            # lee el PDF (~50 s)
python scripts/revisar_eq_sidaces.py --layout ruta/al/layout.json   # sin releer el PDF

# validacion sin tocar la BD:
backend\venv\Scripts\python.exe backend\manage.py import_eq_sidaces `
    --file data/catalogo/eq_sidaces_normalized.json `
    --marco-version EQ-SIDACES-2019-Res27-2019 --check

# pruebas:
backend\venv\Scripts\python.exe backend\manage.py test catalogo --noinput
```

**Detente aquí.** No se corrige definitivamente ni se importa hasta que este informe y el CSV de
trabajo sean revisados.
