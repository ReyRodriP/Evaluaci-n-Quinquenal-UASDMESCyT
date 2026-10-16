# Importación y validación — catálogo EQ-SIDACES

Guía operativa. La auditoría de la fuente (conteos, anomalías, casos ambiguos) está en
`docs/auditoria_eq_sidaces.md`.

## 1. Flujo

```
PDF oficial
   │  python scripts/extraer_eq_sidaces.py --pdf "docs/Estándares Marco EQ-SIDACES (Versión Final).pdf" --outdir data/catalogo
   ▼
data/catalogo/eq_sidaces_normalized.json (+ .csv, eq_sidaces_pending_review.json)
   │  backend/venv/Scripts/python.exe backend/manage.py import_eq_sidaces --file ... --marco-version ... --check
   ▼
validación de archivo (sin BD)
   │  ... --dry-run   (simula y revierte)
   ▼
... --apply          (solo BD de pruebas / importación controlada futura)
```

Estados: `--check` y `--dry-run` se ejecutaron contra la BD de desarrollo sin persistir nada.
`--apply` se ejecutó **una sola vez, contra la BD dedicada `evaluacion_quinquenal_piloto`**
(piloto aprobado: 75 registros; ver `docs/catalogo_piloto_guia.md` §4). No se ejecutó
`--apply` contra la BD de desarrollo ni contra ninguna base operativa.

## 2. Salidas del extractor

| Archivo | Contenido |
|---|---|
| `data/catalogo/eq_sidaces_normalized.json` | `meta` (conteos, incidencias, notas) + `registros` (2352) |
| `data/catalogo/eq_sidaces_normalized.csv` | registros en plano (sin `meta` ni `origen.definicion`) |
| `data/catalogo/eq_sidaces_pending_review.json` | solo los 1128 `pendiente_revision` |

Esquema de registro: `clave` (`dim:`, `comp:`, `cri:`, `std:`, `ind:`, `evi:` + código o
`#orden`), `nivel`, `codigo` (vacío en indicador/evidencia: la fuente no tiene código de 5
segmentos), `texto_original`, `padre` (clave del padre), `orden`, `nivel_jerarquico`,
`version_marco` (`EQ-SIDACES-2019-Res27-2019`), `origen.{pdf_pagina, pagina_documento, seccion,
definicion?, …}`, `estado` (`confirmado` | `pendiente_revision`), `observaciones[]`.

Estado actual: 1224 confirmados / 1128 pendientes (31 no evidencia: estructurales + quiebres de
justificación; 1097 evidencias pendientes por no poder asociarse a un indicador).

## 3. Comando `import_eq_sidaces`

```
manage.py import_eq_sidaces --file <json|csv> --marco-version <etiqueta> (--check | --dry-run | --apply)
                             [--ack-discrepancias] [--allow-synthetic-codes]
```

- **Exactamente un modo.** `--check` valida el archivo y reporta sin tocar la BD;
  `--dry-run` simula la importación dentro de una transacción y la revierte;
  `--apply` persiste (en esta fase: solo BD de pruebas).
- `--marco-version` debe coincidir con `version_marco` de cada registro. Se llama así porque
  `--version` está reservado por Django.
- **Discrepancias** entre `meta.conteos_referencia` (texto §2.3) y los conteos reales bloquean
  `--dry-run`/`--apply` salvo `--ack-discrepancias`; en `--check` solo se reportan.
- **Solo confirmados** con todos los ancestros confirmados se importan; los pendientes se
  omiten y se contabilizan. Las evidencias se importan solo si su padre es un indicador
  (en el dataset real son todas pendientes → no se importan).
- **Códigos sintéticos**: los indicadores no tienen código oficial → `--apply` exige
  `--allow-synthetic-codes` (genera `{std}-IND-{orden:02d}`, marcado como no oficial).
  En `--dry-run` se generan con advertencia.
- `version.activo` no se modifica (solo puede haber una versión activa; decisión pendiente).
- Validaciones: campos requeridos, claves únicas, jerarquía (padre existente y de nivel
  correcto; nivel estricto solo para confirmados), coherencia de prefijos de código en
  confirmados, unicidad global de código (igual que `unique_together` de la BD), orden ≥ 1,
  texto no vacío en confirmados, evidencia confirmada exige padre indicador, versión coincidente.

## 4. Pruebas

- `backend/catalogo/tests/test_import.py` — 19 tests con dataset sintético completo
  (jerarquía válida, omisión de pendientes/hijos de pendiente, códigos sintéticos,
  discrepancias con/sin `--ack`, idempotencia, fallos de validación, CSV, exactamente un modo).
- `backend/catalogo/tests/test_catalogo.py` — 5 tests de modelos (no modificar).
- `backend/catalogo/tests/test_api.py` — 25 tests (consulta + exportación CSV).
- Resultado verificado el 15/10/2026 en el commit `6a3dd7f`: `test catalogo` → **49 OK**;
  suite regresión completa
  (`accounts auditoria dashboard evaluation evidence evidencias health notificaciones organization
  reportes search catalogo`) → **236 OK**. `makemigrations --check --dry-run` → sin cambios.
- Contra el dataset real (solo `--check`, no toca BD): 2352 registros, **0 errores**;
  reporta las discrepancias 211/923/1097 vs 210/909/915.

## 5. Restricciones respetadas

- La única importación persistida (`--apply`) fue contra la BD dedicada del piloto
  `evaluacion_quinquenal_piloto`; la BD de desarrollo conserva su mini-muestra de 6
  registros y las tablas operativas no se modificaron.
- Modelos operativos intactos; `IndicadorMarco` sin conexión con `evaluation.Indicador`/`Asignacion`.
- App heredada `evidencias` conservada; contratos API Angular sin cambios; datos existentes intactos.
- Códigos ambiguos, textos vacíos y discrepancias de conteo: marcados/documentados, nunca
  corregidos automáticamente.

## 6. Pendientes antes de importar datos reales

1. Revisión institucional de `eq_sidaces_pending_review.json` (1128 registros).
2. Reconciliación manual de conteos y de los 3 estándares con prefijo fuera de contexto.
3. Criterio de asociación evidencia→indicador (hoy todas pendientes, asociadas al estándar).
4. Decisión sobre `version.activo` (D13) y sobre los indicadores sin código oficial (D9).
5. Extraer definiciones de dimensión (páginas de separación, pendientes).
