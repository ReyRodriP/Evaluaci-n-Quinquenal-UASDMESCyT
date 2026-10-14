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

Estados: en esta fase **solo `--check` contra la BD real**. `--apply` está reservado para pruebas
y para la importación controlada posterior a la revisión institucional.

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
- Resultado: `test catalogo` → **24 OK**; suite regresión completa
  (`accounts auditoria dashboard evaluation evidence evidencias health notificaciones organization
  reportes search catalogo`) → **211 OK**. `makemigrations catalogo --check --dry-run` → sin cambios.
- Contra el dataset real (solo `--check`, no toca BD): 2352 registros, **0 errores**;
  reporta las discrepancias 211/923/1097 vs 210/909/915.

## 5. Restricciones respetadas

- No se importó nada a PostgreSQL; no se ejecutó `--apply` contra la BD real.
- Modelos operativos intactos; `IndicadorMarco` sin conexión con `evaluation.Indicador`/`Asignacion`.
- App heredada `evidencias` conservada; contratos API Angular sin cambios; datos existentes intactos.
- Códigos ambiguos, textos vacíos y discrepancias de conteo: marcados/documentados, nunca
  corregidos automáticamente.

## 6. Pendientes antes de importar datos reales

1. Revisión institucional de `eq_sidaces_pending_review.json` (1128 registros).
2. Reconciliación manual de conteos y de los 3 estándares con prefijo fuera de contexto.
3. Criterio de asociación evidencia→indicador (hoy todas pendientes, asociadas al estándar).
4. Decisión sobre `version.activo` y sobre qué hacer con indicadores sin código oficial.
5. Extraer definiciones de dimensión (páginas de separación, pendientes).
