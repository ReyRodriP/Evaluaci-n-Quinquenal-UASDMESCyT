# Decisiones EQ-SIDACES — matriz D1–D13 y plan de revisión

Estado: **todas las decisiones en `pendiente`. Este documento no aplica cambios.**
Complementa `docs/revision_eq_sidaces.md` (§5) y `docs/auditoria_eq_sidaces.md`.
Fuente de evidencia: PDF oficial (`docs/Estándares Marco EQ-SIDACES (Versión Final).pdf`),
`data/catalogo/eq_sidaces_normalized.json` y `data/catalogo/eq_sidaces_revision.csv`.

Convenciones:

- **Verificable técnicamente** = puede resolverse con el equipo del proyecto leyendo el PDF o el
  dataset, sin decidir contenido normativo.
- **Requiere validación institucional** = fija contenido oficial, metodología o autorización;
  el equipo técnico solo prepara la evidencia.
- **Recomendación técnica** = propuesta del equipo, **no** es una decisión oficial.

---

## 1. Matriz de decisiones

### D1 — Criterio de conteo de estándares

- **Pregunta:** ¿cuál es el número oficial de estándares —211 filas impresas, 210 (texto pág. 33)
  o 212 (glosario pág. 25)— y qué criterio de conteo rige (filas, códigos únicos, exclusiones)?
- **Evidencia disponible:** recuento independiente doble = **211 filas** (parser + recuento de
  layout); **209 códigos únicos**; 2 códigos impresos dos veces (págs. 55/56 y 82/93); citas
  literales en pág. 33 (210) y pág. 25 (212).
- **Verificable técnicamente:** conteo fila por fila contra el PDF (lista de 211 claves disponible
  en el dataset); demostrar qué cifras **no** se alcanzan por deduplicación simple.
- **Requiere validación institucional:** fijar el número oficial y el criterio de conteo.
- **Opciones y consecuencias:**
  - A) Adoptar 211 (todo el contenido impreso): el dataset queda como está; hay que documentar la
    diferencia con las cifras oficiales.
  - B) Adoptar 210 excluyendo una repetición: exige definir cuál; se pierde un contenido impreso.
  - C) Adoptar 212: no existe una fila candidata adicional en la matriz → implicaría introducir
    contenido no presente (riesgo de invención, descartado técnicamente).
- **Recomendación técnica:** opción A para el dataset (nunca eliminar filas para igualar cifras),
  con la discrepancia documentada hasta que la institución fije la cifra oficial.
- **Estado:** pendiente.
- **Responsable sugerido:** comisión de estandarización (UASD/MESCyT) con apoyo del equipo
  técnico. **Evidencia para cerrar:** acta/nota que fije número oficial + criterio, y conteo
  manual cruzado por dos revisores.

### D2 — Estándares duplicados (dos códigos impresos dos veces)

- **Pregunta:** ¿`1.2.3.1` (págs. 55 y 56) y `2.6.1.1` (págs. 82 y 93) son cuatro estándares
  legítimos con códigos repetidos por error de numeración, o los dos registros pendientes son
  erratas y su código correcto es otro?
- **Evidencia disponible:** los textos son **distintos**:
  - `1.2.3.1` pág. 55 (bajo cri. 1.2.3): "Los procesos para la elección, delegación y sucesión
    de sus autoridades…" — 5 indicadores / 3 evidencias.
  - `1.2.3.1` pág. 56 (bajo cri. 1.3.1): "La institución cuenta con un marco normativo interno
    que sustenta la regulación de la gestión de los procesos institucionales." — 7 / 8.
  - `2.6.1.1` pág. 82 (bajo cri. 2.3.3): "La IES asegura la pertinencia de los perfiles de
    egreso…" — 5 / 3.  `2.6.1.1` pág. 93 (bajo cri. 2.6.1): "La institución cuenta con
    procedimientos que sirven de guía a los responsables del proceso de enseñanza - aprendizaje."
    — 4 / 4.
- **Verificable técnicamente:** comparación de textos, hijos y contextos (hecha); verificar si
  los prefijos coherentes esperados (p. ej. `1.3.1.x`, `2.3.3.x`) están libres en el PDF.
- **Requiere validación institucional:** determinar si el código impreso es correcto o es errata,
  y cuál sería el correcto (no se inventa).
- **Opciones y consecuencias:**
  - A) Mantener ambos con su código impreso: en BD los duplicados chocarían con
    `unique_together (version, codigo_completo)` si ambos se confirman → exigiría desambiguación
    (código sintético de contexto o excepción documentada).
  - B) Confirmar el legítimo y corregir el pendiente al código oficial determinado por la
    comisión: requiere decisión de D3/D2 en conjunto.
  - C) Confirmar solo uno y documentar el otro como no oficial: se conserva el contenido pero sin
    código del marco.
- **Recomendación técnica:** verificar la secuencia de códigos vecina en las páginas 55/56 y
  82/93; presentar ambas lecturas a la comisión; **no** corregir automáticamente.
- **Estado:** pendiente.
- **Responsable sugerido:** comisión, con revisor académico de la dimensión correspondiente
  (I y II). **Evidencia para cerrar:** transcripción de la numeración vecina de cada página +
  decisión escrita sobre cada código.

### D3 — `std:1.2.3.2` bajo el criterio 1.3.1 (pág. 56)

- **Pregunta:** ¿es correcto el código `1.2.3.2` para el estándar "La institución aplica los
  requisitos contenidos en la Ley de Educación Superior…" impreso bajo el criterio 1.3.1?
- **Evidencia disponible:** el criterio 1.3.1 ("Establecimiento del marco normativo interno y
  legal externo", pág. 56) contiene **dos** estándares: `1.2.3.1` (D2) y `1.2.3.2` — **ninguno**
  con prefijo `1.3.1`; el texto del estándar es temáticamente coherente con el criterio.
- **Verificable técnicamente:** confirmar en el PDF si el criterio 1.3.1 carece por completo de
  estándares `1.3.1.x` (sí, según el dataset) y si `1.2.3.2` ya existe en el criterio 1.2.3 (no
  aparece allí).
- **Requiere validación institucional:** el código oficial correcto.
- **Opciones y consecuencias:**
  - A) Mantener `1.2.3.2`: la validación del importador rechaza confirmarlo con prefijo
    incoherente → se quedaría `pendiente_revision` de forma permanente o requeriría una excepción
    documentada.
  - B) Corregir el código al que determine la comisión (p. ej. `1.3.1.x`, sin inventarlo):
    registro pasa a ser confirmable y la jerarquía queda coherente.
  - C) Dejar pendiente indefinidamente: conserva el contenido pero no entra al catálogo.
- **Recomendación técnica:** hipótesis de errata (el código no corresponde al contexto); preparar
  la numeración libre real de `1.3.1.x` en el PDF y someterla a decisión. No aplicar corrección.
- **Estado:** pendiente.
- **Responsable sugerido:** comisión + revisor de la dimensión I. **Evidencia para cerrar:**
  lectura literal de la página 56 y decisión sobre el código.

### D4 — Celdas de indicador sin viñeta (pág. 78)

- **Pregunta:** ¿las celdas de `std:2.2.1.3` y `std:2.2.1.4` contienen uno o varios indicadores?
- **Evidencia disponible:** textos completos con enunciado + fórmula + leyenda
  (`PI/DI/TD`; `PV/DV/TD`); el resto de la página sí usa viñetas `•`; cada celda trae **una**
  fórmula y una leyenda; el estándar `2.2.1.3` muestra la fórmula intercalada en su propio texto
  ("participa en grupos de 𝑃𝐼 investigación. 𝑇𝐷"), señal de la maquetación de esa página.
- **Verificable técnicamente:** análisis textual (una oración + una fórmula → candidato a un
  indicador por celda) y comparación con páginas análogas donde las fórmulas van dentro de una
  viñeta única.
- **Requiere validación institucional:** ratificación (impacta el conteo de indicadores de D1/D10).
- **Opciones y consecuencias:**
  - A) Un indicador por celda (los 2 registros actuales, `confirmar`): respeta el conteo 923.
  - B) Separar enunciado, fórmula y leyenda (`corregir`): Pierde la forma literal de la celda.
  - C) Varios indicadores por celda: no respaldado por el texto.
- **Recomendación técnica:** opción A (una viñeta implícita = un indicador), con B solo si la
  revisión decide separar la leyenda; documentar en `observaciones_revision`.
- **Estado:** pendiente.
- **Responsable sugerido:** revisor técnico; ratifica la comisión. **Evidencia para cerrar:**
  lectura visual de la página 78 y decisión por celda.

### D5 — Texto contaminado por rótulos de evidencia (pág. 90) y fragmento `co:`

- **Pregunta:** ¿cuál es el texto real de `ind:2.5.2.2#1` sin el rótulo "Archivo físico", y a qué
  corresponde el fragmento `co:` de la columna de evidencias?
- **Evidencia disponible:** texto actual: "Las condiciones ambientales son apropiadas para
  Archivo físi preservar la información de los estudiantes."; incidencia
  `evidencia_inicio_invalido` (`co:`, pág. 90); 10 evidencias del estándar (una con
  "Archivo digital:" pegado); el estándar `2.5.2.2` es "…mecanismos para el archivo y la
  actualización de los datos personales de los estudiantes."
- **Verificable técnicamente:** lectura visual de la página 90 (columnas 3 y 4) para reconstruir
  el indicador y ubicar `co:`.
- **Requiere validación institucional:** si `co:` era una evidencia de la fuente, decidir si se
  reconstruye o se documenta como pérdida; **no inventar** su contenido.
- **Opciones y consecuencias:**
  - A) Corregir solo el indicador y documentar `co:` como pérdida de la fuente (más seguro).
  - B) Reconstruir también la evidencia **solo si** el PDF muestra su texto completo.
  - C) Dejar todo pendiente: conserva el texto contaminado.
- **Recomendación técnica:** A, elevando a B únicamente si la página respalda la reconstrucción
  con lectura literal; doble verificación por ser contenido oficial.
- **Estado:** pendiente.
- **Responsable sugerido:** revisor técnico (doble verificación); la comisión ratifica si se
  recupera contenido. **Evidencia para cerrar:** transcripción visual de la página 90.

### D6 — Colas de indicador reensambladas (págs. 102 y 170)

- **Pregunta:** ¿las colas "de investigación." (pág. 102) y "apropiadas para su uso." (pág. 170)
  pertenecen al último indicador del estándar anterior?
- **Evidencia disponible:** el parser reensambló por tres señales simultáneas: nuevo estándar en
  la misma línea de la cola, indicador anterior sin punto final y arranque en minúscula; los
  textos resultantes leen completos ("…normativas **de investigación.**",
  "…dimensiones **apropiadas para su uso.**"); observación registrada en ambos registros.
  Dato adicional a verificar: el texto de `std:3.1.1.1` termina "…objetivos de la IES. IES."
  (posible artefacto de la misma maquetación).
- **Verificable técnicamente:** lectura visual de las páginas 102 y 170 (posición de la cola en
  la fila del estándar siguiente).
- **Requiere validación institucional:** ratificación (contenido oficial; no cambia conteos).
- **Opciones y consecuencias:**
  - A) Aceptar el reensamblado (`confirmar`): el indicador queda con su texto completo.
  - B) Rechazarlo: el indicador quedaría truncado y la cola sin destino (no respaldado por la
    lectura).
- **Recomendación técnica:** opción A previa verificación visual; aprovechar para revisar el
  "IES. IES." de `std:3.1.1.1`.
- **Estado:** pendiente.
- **Responsable sugerido:** revisor técnico (cierre con evidencia visual documentada); comisión
  solo si hay duda. **Evidencia para cerrar:** captura de referencia (número de página) y
  lectura literal de ambas filas.

### D7 — Registros vacíos y residuales

- **Pregunta:** ¿qué contenido tienen las viñetas sin texto —7 evidencias (págs. 52, 82, 116,
  164, 180×2, 188) y 2 indicadores (`ind:7.3.1.2#5` pág. 180; `ind:8.3.1.3#4` pág. 189)— y los
  dos residuales `evi:1.2.1.3#6` = "el" (pág. 53) y `evi:7.2.1.2#4` = "a" (pág. 175)?
- **Evidencia disponible:** incidencias del parser (9 + 2); los residuales muestran restos de
  continuación; todos están en el CSV de revisión (los residuales se localizan por `clave`).
- **Verificable técnicamente:** lectura visual de las 9 páginas afectadas.
- **Requiere validación institucional:** si el PDF muestra contenido no extraíble (imágenes,
  símbolos), la transcripción oficial.
- **Opciones y consecuencias:**
  - A) Vacío real en la fuente: `confirmar` con observación "celda vacía en la fuente" (no
    inventar texto).
  - B) Contenido visible no extraído: transcribir con doble verificación (`corregir`).
  - C) Residuales: unir al registro que la lectura indique o eliminar el resto (`corregir`);
    no dejar restos sin explicación.
- **Recomendación técnica:** revisar las 9 páginas; A donde el vacío sea real; C para los
  residuales únicamente con lectura literal.
- **Estado:** pendiente.
- **Responsable sugerido:** revisor técnico; comisión si se transcribe contenido no extraíble.
  **Evidencia para cerrar:** ficha por página con la lectura visual.

### D8 — Criterio de asociación evidencia ↔ indicador

- **Pregunta:** ¿cuál es la asociación canónica de las evidencias (estándar, indicador o ambos)
  y con qué procedencia debe guardarse?
- **Evidencia disponible:** metodología pág. 28 ("tercer par categorial matricial:
  INDICADORES – EVIDENCIAS"); glosario pág. 25 (las evidencias "aluden al indicador y estándar
  bajo examen"); en la matriz **no** hay asociación por ítem (viñetas sin número ni referencia);
  estadística de alineación: 479/1097 en línea con un indicador, 10 en línea adyacente única,
  608 sin correspondencia; por estándar: 12 totalmente alineados, 197 parciales, 2 ninguno;
  el CSV conserva la señal inferida en `indicador_sugerido_linea` + `criterio_asociacion`.
- **Verificable técnicamente:** las estadísticas y ejemplos (hechos); **no** la asociación por
  ítem.
- **Requiere validación institucional:** decisión metodológica (impacta el modelo de datos y el
  instrumento de evaluación).
- **Opciones y consecuencias:**
  - A) Asociación al estándar (estado actual): trazabilidad completa; no materializa el par
    declarado.
  - B) Asociación al indicador: para 608 evidencias exigiría un criterio de asignación no
    respaldado → riesgo de asociaciones inventadas.
  - C) Ambos: vínculo canónico al estándar + atributo derivado a indicador **con procedencia**
    (`inferido` vs `confirmado_por_revision`), sin sustituir el anclaje al estándar.
- **Recomendación técnica:** opción C, empezando por revisar los 12 estándares totalmente
  alineados (método piloto del lote 5) y sin asociar por defecto los 608 sin correspondencia.
- **Estado:** pendiente.
- **Responsable sugerido:** comisión metodológica; evidencia para cerrar: acta que defina el
  criterio y su representación en el sistema.

### D9 — Códigos sintéticos no oficiales para indicadores y evidencias

- **Pregunta:** ¿se aprueba el uso de códigos sintéticos (`{std}-IND-NN`, `{ind}-EV-NN`)
  claramente marcados como **no oficiales** para satisfacer las claves únicas del modelo?
- **Evidencia disponible:** verificado que la fuente no tiene código de 5+ segmentos (todo el
  PDF); el modelo exige `codigo_completo` único; el importador exige `--allow-synthetic-codes` y
  emite advertencia.
- **Verificable técnicamente:** hecho de la fuente y comportamiento del importador (pruebas en
  verde).
- **Requiere validación institucional:** aprobar la convención y su etiquetado permanente.
- **Opciones y consecuencias:**
  - A) Aprobar los sintéticos no oficiales (habilita importar indicadores/evidencias).
  - B) Esperar códigos oficiales: la importación de esos niveles queda bloqueada.
- **Recomendación técnica:** opción A, manteniendo la marca de no oficial en documentación y
  advertencias del comando.
- **Estado:** pendiente.
- **Responsable sugerido:** comisión. **Evidencia para cerrar:** aprobación escrita de la
  convención de nombres.

### D10 — Importación con discrepancias de conteo (`--ack-discrepancias`)

- **Pregunta:** ¿se autoriza ejecutar la importación con las discrepancias sin reconciliar
  (211/923/1097 vs 210/909/915 y vs 212/915/1082)?
- **Evidencia disponible:** el comando valida sin errores (`--check` real en verde) y bloquea
  `--dry-run`/`--apply` salvo `--ack-discrepancias`; informe §3 con hechos e hipótesis.
- **Verificable técnicamente:** `--check` y `--dry-run` con `--ack` en BD de prueba.
- **Requiere validación institucional:** autorización explícita (las cifras oficiales quedarían
  sin cuadrar en auditorías futuras).
- **Opciones y consecuencias:**
  - A) Autorizar con nota documentada (condicionada a D1, D8 y al cierre del piloto).
  - B) Exigir reconciliación previa: la importación queda bloqueada hasta cerrar D1.
- **Recomendación técnica:** opción A solo después de resolver D1/D8 y cerrar el lote piloto.
- **Estado:** pendiente.
- **Responsable sugerido:** coordinación del proyecto + comisión. **Evidencia para cerrar:**
  autorización registrada (correo/acta) que referencie este documento.

### D11 — Posibles palabras partidas por la justificación (52 registros)

- **Pregunta:** ¿se confirma la unión de cada fragmento detectado (p. ej. "gestió" + "n") en los
  52 registros marcados?
- **Evidencia disponible:** filas del CSV con `motivos = palabra_partida`; fragmento en
  `observaciones_fuente`; heurística y su límite documentados (solo fragmentos ≤ 4 letras; puede
  haber quiebres no detectados).
- **Verificable técnicamente:** cada caso contra el PDF (línea justificada visible).
- **Requiere validación institucional:** solo el criterio general de corrección; el detalle se
  cierra técnico-mente fila por fila (muestra de ≥20% en doble revisión).
- **Opciones y consecuencias:**
  - A) `corregir` uniendo el fragmento cuando la lectura lo respalde.
  - B) `confirmar` tal cual cuando el fragmento resulte ser palabra completa legítima.
  - C) `pendiente` si la página no se lee con claridad.
- **Recomendación técnica:** A/B por fila con trazabilidad en `texto_corregido`; ninguna
  corrección automática.
- **Estado:** pendiente.
- **Responsable sugerido:** dos revisores técnicos; la comisión ratifica el criterio.
  **Evidencia para cerrar:** CSV de revisión completado para el lote 4 (o su resumen).

### D12 — Definiciones de las dimensiones

- **Pregunta:** ¿se incorporan al campo `definicion` las definiciones de las 8 dimensiones que
  viven en páginas separadas?
- **Evidencia disponible:** páginas identificadas y verificadas con párrafo definicional:
  **49** (Gestión Institucional, doc. 37), **73** (Gestión Académica, doc. 61), **101**
  (Investigación, doc. 89), **113** (Vinculación con el Medio/Extensión, doc. 101), **131**
  (Estudiantes, doc. 119), **151** (Personal Académico, doc. 139), **163** (Servicios y
  Estructuras de Apoyo Institucional, doc. 151), **183** (Aseguramiento de la Calidad, doc. 171).
  El dataset los deja vacíos por diseño (limitación documentada en la auditoría).
- **Verificable técnicamente:** extracción factible (el texto existe); riesgo de quiebres por
  justificación (mismo caso D11).
- **Requiere validación institucional:** ratificación de la transcripción (contenido oficial).
- **Opciones y consecuencias:**
  - A) Extraer, verificar y ratificar (completa el catálogo).
  - B) Dejar vacío: el campo queda incompleto para la instrumentación.
- **Recomendación técnica:** opción A, transcribiendo a un archivo de propuestas separado (no a
  los normalizados) y con contraste visual de las 8 páginas.
- **Estado:** pendiente.
- **Responsable sugerido:** técnico + comisión ratifica. **Evidencia para cerrar:** 8 fichas de
  transcripción (página, texto, revisor).

### D13 — Activación de la versión del marco

- **Pregunta:** cuándo y quién activa `VersionMarcoEvaluacion.activo` (solo puede haber una
  versión activa).
- **Evidencia disponible:** restricción del modelo (tests de unicidad en verde); el importador no
  modifica el flag (lo reporta).
- **Verificable técnicamente:** comportamiento de la restricción (ya probado).
- **Requiere validación institucional:** decisión operativa (convivencia con versiones previas).
- **Opciones y consecuencias:**
  - A) Activar tras importar y validar (recomendada si no hay otra versión en uso).
  - B) Mantener inactiva hasta el siguiente ciclo.
  - C) Activar reemplazando a otra: exige decidir el destino de la anterior.
- **Recomendación técnica:** opción A recién después de cerrar D1/D8/D10 y verificar la
  importación en BD de prueba.
- **Estado:** pendiente.
- **Responsable sugerido:** coordinación del proyecto. **Evidencia para cerrar:** registro de la
  activación (fecha, responsable, versión).

---

## 2. Lotes de revisión manual (orden recomendado)

El orden prioriza primero lo que desbloquea decisiones y afecta la integridad jerárquica.

| Orden | Lote | Filas | Filtro en el CSV | Decisiones que desbloquea |
|---|---|---:|---|---|
| 1 | Códigos fuera de contexto y duplicados | 3 (+2 confirmados como contexto) | `motivos` contiene `codigo_fuera_de_contexto` | D1, D2, D3 |
| 2 | Indicadores sin viñeta y reensamblados | 4 | `motivos` contiene `indicador_sin_vineta` o `indicador_reensamblado` | D4, D6 |
| 3 | Texto contaminado y vacíos/residuales | 12 + 9 + 2 | `motivos` contiene `texto_contaminado` o `vineta_sin_texto`; los 2 residuales por `clave` (`evi:1.2.1.3#6`, `evi:7.2.1.2#4`) | D5, D7 |
| 4 | Posibles palabras partidas | 52 | `motivos` contiene `palabra_partida` | D11 |
| 5 | Asociación evidencias ↔ indicadores | 1097 | `nivel = evidencia` | D8 |
| 6 | Definiciones de dimensiones | 8 páginas | fuera del CSV (págs. 49, 73, 101, 113, 131, 151, 163, 183) | D12 |

Columnas a revisar por lote y criterio de `decision`:

- **Lote 1:** `clave`, `codigo`, `pagina_pdf`, `padre_clave`, `padre_codigo`, `padre_texto`,
  `texto_original`, `hermanos`.
  - `confirmar`: el código impreso es correcto tal cual (y se acepta su coexistencia).
  - `corregir`: hay errata → registrar el código/texto correcto en `texto_corregido` /
    `padre_confirmado` (el código corregido se anota al inicio de `observaciones_revision` como
    `codigo_oficial_propuesto: …`).
  - `pendiente`: no se puede determinar con la evidencia actual.
- **Lote 2:** `texto_original`, `hermanos`, `observaciones_fuente`, `pagina_pdf`.
  - `confirmar`: el texto actual (ya reensamblado o con fórmula incluida) es correcto tal cual.
  - `corregir`: transcribir el texto correcto en `texto_corregido`; si la celda contiene varios
    indicadores, describir la segmentación en `observaciones_revision` (no se parte el registro
    en esta fase).
  - `pendiente`: la página no se lee con claridad.
- **Lote 3:** `texto_original`, `observaciones_fuente`, `indicadores_del_estandar` (evidencias),
  `pagina_pdf`.
  - `confirmar`: vacío real en la fuente o texto correcto.
  - `corregir`: texto reconstruido con lectura literal en `texto_corregido`.
  - `pendiente`: requiere transcripción institucional (contenido no extraíble).
- **Lote 4:** `texto_original`, `observaciones_fuente` (contiene el fragmento), `pagina_pdf`.
  - `confirmar`: el fragmento era palabra completa (no un quiebre).
  - `corregir`: `texto_corregido` con la palabra unida.
  - `pendiente`: no se lee con claridad.
- **Lote 5:** `indicadores_del_estandar`, `indicador_sugerido_linea`, `criterio_asociacion`,
  `padre_clave`, `padre_confirmado`.
  - `confirmar`: la evidencia se queda asociada al estándar (decisión D8 = opción A) o la
    sugerencia de línea es correcta y se registra en `padre_confirmado` con la clave `ind:…`
    (sintética, no oficial).
  - `corregir`: se decide otra asociación → `padre_confirmado` con la clave elegida.
  - `pendiente`: no se puede decidir (p. ej. `sin_correspondencia` cuando D8 exige indicador).
  - **Nota:** el lote 5 se procesa **después** de decidir D8; mientras tanto, solo se calibra el
    método con los 12 estándares totalmente alineados.
- **Lote 6:** no usa el CSV: se transcribe a un archivo de propuestas por dimensión
  (`decision`, `texto_propuesto`, `pagina`, `revisor`) y se ratifica.

## 3. Lote piloto (guía de primera revisión)

Alcance: los casos estructurales más críticos = lote 1 completo + lote 2 completo + los dos
registros no evidencia del lote 3 (pág. 90). **11 filas del CSV** + 2 estándares `confirmado`
que sirven de contexto (no están en el CSV) + el caso `co:` (sin registro). Todas las decisiones
siguen en `pendiente`: esta guía es para **tomar** decisiones, no para aplicarlas.

Cómo registrar la decisión de cada fila (una vez aprobada la revisión): completar
`decision`, y si `corregir` también `texto_corregido` (y `padre_confirmado` si aplica) más una
línea en `observaciones_revision` con la lectura literal usada como evidencia.

| # | Clave (en CSV si…) | Pág. PDF / doc. | Contexto | Texto actual (extracto) | Pregunta de revisión | Cierra |
|---|---|---|---|---|---|---|
| 1 | `std:1.2.3.1@cri:1.3.1` (sí) | 56 / 44 | cri. 1.3.1 "Establecimiento del marco normativo interno y legal externo" | "La institución cuenta con un marco normativo interno que sustenta la regulación de la gestión de los procesos institucionales." | ¿El código impreso es correcto pese a no corresponder al criterio 1.3.1, o es errata? ¿Cuál sería el código libre real en 1.3.1.x? | D2, D3 |
| 2 | `std:1.2.3.2` (sí) | 56 / 44 | cri. 1.3.1 (con el estándar anterior) | "La institución aplica los requisitos contenidos en la Ley de Educación Superior… y otras normativas… del sistema de educación superior dominicano." | Igual que #1: ¿código correcto o errata? Verificar además que `1.2.3.2` no exista bajo 1.2.3. | D2, D3 |
| 3 | `std:2.6.1.1` (sí) | 82 / 70 | cri. 2.3.3 "Perfiles de egreso" (junto a `2.3.3.1`, `2.3.3.2`) | "La IES asegura la pertinencia de los perfiles de egreso con las necesidades de la sociedad mediante su revisión periódica." | ¿Es una fila legítima con código repetido o una errata de numeración? Comparar con el homónimo de la pág. 93. | D1, D2 |
| 4 | `ind:2.2.1.3#1` (sí) | 78 / 66 | `std:2.2.1.3` (el estándar muestra la fórmula intercalada en su texto) | "Porcentaje de docentes que participan en investigación. = 𝐷𝐼 𝑥100 PI: … TD: Total de Docentes." | ¿La celda contiene un solo indicador (enunciado + fórmula + leyenda)? | D4 |
| 5 | `ind:2.2.1.4#1` (sí) | 78 / 66 | `std:2.2.1.4` | "Porcentaje de docentes que participan en vinculación con el medio / extensiones. = 𝐷𝑉 𝑥100 PV: … TD: Total de Docentes." | Igual que #4. | D4 |
| 6 | `ind:3.1.1.1#7` (sí) | 102 / 90 | `std:3.1.1.1` (último de 7 indicadores) | "Los criterios para la asignación de recursos están claramente definidos en las políticas y normativas de investigación." | ¿La cola "de investigación." impresa en la fila de `3.1.1.2` pertenece a este indicador? Revisar también "…IES. IES." en el texto del estándar. | D6 |
| 7 | `ind:7.1.6.1#5` (sí) | 170 / 158 | `std:7.1.6.1` | "Los espacios colectivos tienen dimensiones apropiadas para su uso." | ¿La cola "apropiadas para su uso." impresa en la fila de `7.1.6.2` pertenece a este indicador? | D6 |
| 8 | `std:2.5.2.2` (sí) | 90 / 78 | cri. 2.5.2 "Actualización de la información académica" | "La institución cuenta con mecanismos para el archivo y la actualización de los datos personales de los estudiantes." | Leer la página completa: ¿el remanente `co:` de la columna de evidencias corresponde a una evidencia de la fuente? | D5 |
| 9 | `ind:2.5.2.2#1` (sí) | 90 / 78 | mismo estándar (6 indicadores, 10 evidencias) | "Las condiciones ambientales son apropiadas para Archivo físi preservar la información de los estudiantes." | Transcribir el texto sin el rótulo "Archivo físico": ¿es "…son apropiadas para preservar la información de los estudiantes."? | D5 |
| 10 | `std:1.2.3.1` (**contexto**, `confirmado`, no está en el CSV) | 55 / 43 | cri. 1.2.3 "Mecanismos de elección, delegación y sucesión" | "Los procesos para la elección, delegación y sucesión de sus autoridades se encuentran claramente establecidos… (5 indicadores / 3 evidencias)" | ¿Este registro es el legítimo del par duplicado? | D2 |
| 11 | `std:2.6.1.1@cri:2.6.1` (**contexto**, `confirmado`, no está en el CSV) | 93 / 81 | cri. 2.6.1 "Procedimientos, metodología y técnicas de enseñanza" | "La institución cuenta con procedimientos que sirven de guía a los responsables del proceso de enseñanza - aprendizaje. (4 indicadores / 4 evidencias)" | ¿Este registro es el legítimo del par duplicado? | D2 |

Evidencia a recabar por fila (anexar en la revisión): número de página del PDF, lectura literal
de la celda o fila, y —para códigos— la secuencia de códigos vecina de la página. Abrir el PDF
con `Start-Process (Get-ChildItem docs\*.pdf).FullName` y navegar con `pagina_pdf`.

## 4. Resumen: qué decide cada quien

| Decisiones | Equipo técnico (puede cerrar) | Institucional (debe aprobar) |
|---|---|---|
| Solo técnico | D6 (con verificación visual), D11 (detalle por fila, tras aprobar el criterio) | — |
| Técnico prepara, institucional ratifica | D4, D5, D7, D12 (preparan transcripciones y opciones) | ratificación del contenido |
| Solo institucional | aporta estadística y opciones (D1, D8, D9, D10, D13) | decisión final |
| Conjunta condicionada | D10 depende de D1+D8+piloto; D2/D3 dependen de la lectura de códigos vecina | fija el código oficial |

## 5. Protecciones y próxima acción

- Sin `--apply`, sin modificar la BD, sin tocar modelos, relaciones ni contratos de API.
- JSON/CSV normalizados intactos; las correcciones propuestas se registran únicamente en el CSV
  de revisión (o en fichas separadas del lote 6).
- Ninguna hipótesis (H1–H4) se ha convertido en dato; no se han creado códigos oficiales.
- Pruebas existentes en verde al cierre de esta fase (24 catálogo / 211 regresión).

**Próxima acción:** ejecutar el lote piloto (§3) con los revisores designados y traer sus
decisiones a esta matriz antes de cualquier corrección o importación. **Detente aquí.**
