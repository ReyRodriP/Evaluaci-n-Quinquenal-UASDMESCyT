# Diagnóstico técnico — Sistema de Gestión de Evidencias para la Evaluación Quinquenal UASD–MESCyT

Fecha del diagnóstico: 2026-10-12 (auditoría de solo lectura; no se modificó código).
Referencia del catálogo oficial: [`estructura_estandares_sidaces.md`](./estructura_estandares_sidaces.md).

---

## 1. Alcance y método

Se revisaron (sin modificar):

- Backend Django: modelos, serializers, ViewSets, URLs, permisos, migraciones y servicios de las apps `evaluation`, `evidence`, `evidencias`, `organization`, `accounts`, `dashboard`, `reportes`, `auditoria`, `notificaciones`, `search`, `health`.
- Frontend Angular: servicios (`evaluacion.service`, `evidencias.service`, `organizacion.service`, `permisos.service`) y componentes `criterios`, `indicadores`, `asignaciones`, `evidencias`, `evidencia-detalle`, `periodos`, etc.
- Existencia de datos: no hay `db.sqlite3` ni fixtures JSON en el repositorio. El catálogo oficial EQ-SIDACES (PDF) fue extraído por separado.

---

## 2. Arquitectura actual (mapping real)

Modelo de datos actual:

```
Periodo (fecha_inicio/fin, único activo)
 └─ Criterio (nombre, descripción, periodo nullable, activo)
     └─ Indicador (nombre, descripción, obligatorio, activo)
         └─ Asignacion (indicador + unidad_responsable + periodo) [unique_together]
             └─ Evidencia 1:1 (titulo, descripcion, estado activa/cancelada)      ← app evidence
                 └─ VersionEvidencia (archivo, version incremental, comentario)
                     └─ Observacion (comentario, soft-delete activo)
             └─ Evidencia 1:N (archivo, version, subido_por, tipo, tamano)        ← app evidencias (LEGACY)
```

Rutas REST actuales:

| endpoint | app | Detalle |
|---|---|---|
| `/api/periodos/` (+`/activo/`) | evaluation | CRUD con único activo |
| `/api/criterios/` | evaluation | CRUD |
| `/api/indicadores/` | evaluation | CRUD |
| `/api/asignaciones/` (+`/resumen/`, `/aprobar/`, `/rechazar/`, `/en_revision/`, `/observada/`) | evaluation | flujo de revisión |
| `/api/evidencias/` (+`/detalle/`, `/historial/`, `/subir_version/`, `/editar_version/`, `/descargas-masivas/`)| **evidence** | **gana el prefijo** |
| `/api/versiones/` | evidence | descargar/preview/observaciones |
| `/api/observaciones/` | evidence | CRUD (soft delete) |

---

## 3. Hallazgos principales

### 3.1 Dos apps de evidencias coexistiendo (conflicto estructural)

Existen **dos modelos `Evidencia`** distintos, ambos en `INSTALLED_APPS` y ambos apuntando a `Asignacion`:

| | `evidence.Evidencia` (activa) | `evidencias.Evidencia` (legacy) |
|---|---|---|
| Relación con Asignacion | OneToOne (`related_name="evidencia"`) | ForeignKey (`related_name="evidencias"`) |
| Archivo | en `VersionEvidencia` (archivo + versión incremental + comentario) | en el propio modelo (versión inline, 1 fila por subida) |
| Autor del archivo | **no registra quién subió** | `subido_por` (FK User) |
| Tipo/tamaño de archivo | sin validación en el create actual | validado en serializer (tipos + máx 50 MB) |
| Rol | flujo completo (detalle, historial, versiones, observaciones, ZIP) | solo CRUD simple + descargar |

Impactos concretos verificados:

1. **Enrutado solapado.** `evaluacionQuinquenal/urls.py` incluye primero `evidence.urls` y luego `evidencias.urls`, ambas registran `r"evidencias"`. Django resuelve la primera → `/api/evidencias/` lo sirve `evidence`; la app legacy queda **ensombrecida** (su CRUD es inalcanzable).
2. **La app legacy NO está muerta:** el dashboard la importa (`from evidencias.models import Evidencia as EvidenciaLegada`) y calcula `con_evidencia` con `Exists(evidence... ) | Exists(evidencias...)` (`dashboard/views.py:98-101`). Es decir, la misma métrica mezcla dos tablas con cardinalidades distintas (1:1 vs 1:N) → el gemelo legacy puede inflar el resultado si ambos modelos tienen filas, y duplica el criterio de "tiene evidencia".
3. **Permisos duplicados:** `PuedeDescargarEvidencias` acepta `evidence.view_evidencia` OR `evidencias.view_evidencia` (`accounts/permissions.py:303`) y el mapa de filtrado de `_filtrar_evaluador_externo` define ambas app (`permissions.py:81-82`). El frontend también evalúa las dos app (`permisos.tieneAlgunPermiso(['evidence.add_evidencia','evidencias.add_evidencia', ...])`). Hay que otorgar permisos por partida doble.
4. **Falta trazabilidad del autor del archivo:** el modelo `evidence.Evidencia` no tiene `subido_por`; varios lugares usan `hasattr(evidencia, "subido_por")` que siempre es falso (e.g. `evaluation/views.py:220`, `evidence/views.py:602`). Las notificaciones "tu evidencia fue aprobada/rechazada/observada" al autor dependen de ese campo → **hoy no funcionan**. El único que sabe quién subió es el legacy.
5. **Falta validación de tipo/tamaño de archivo** en el flujo actual (`evidence`): se acepta cualquier archivo en `subir_version`/`editar_version`/create; dicha validación solo existe en el serializer legacy (inutilizado). Según las reglas del sistema actual (tipos admitidos PDF/DOC/DOCX/XLS/XLSX/JPG/PNG/GIF/TXT/ZIP/RAR, 50 MB), esto es un hueco de seguridad/calidad.

### 3.2 Brecha entre el modelo actual y el catálogo EQ-SIDACES

El catálogo oficial tiene 6 niveles:

```
Dimensión (8) → Componente (36) → Criterio (77) → Estándar (~210) → Indicador (~909) → Evidencia indicativa (~915)
```

El modelo actual tiene solo 3:

- **`Periodo`** no existe en el catálogo (es el ciclo de la institución).
- **`Criterio`** actual NO corresponde al criterio oficial: agrupa indicadores "por período", admite nombre libre (sin código), permite `null` en período a pesar de que la UI exige período, y no tiene posición/orden oficial.
- **`Indicador`** actual no tiene código oficial, ni referencia a estándar, ni campo de redacción/base de verificación, ni orden, ni clave única por texto. El campo `obligatorio` es la única noción de "aplicabilidad".
- **No existen** entidades para *Dimensión, Componente, Estándar* ni la **evidencia indicativa** (descripción de qué documento debe aportar la unidad).
- No hay campo de **versión/fuente del catálogo** (no permite registrar la revisión del marco de evaluación que se está aplicando).
- No hay mecánica de **aplicabilidad por tipo de unidad** ("solo 4 dimensiones aplican a Recintos/Centros" — pendiente de confirmar con el cliente) ni de **obligatoriedad por dimensión/estándar**.

### 3.2.1 Corrección del diseño de la sección 5 (jerarquía del catálogo verificada en la fuente)

> **Errata corregida (2026-10-12):** la versión inicial de la sección 5 proponía `Criterio → FK Estándar` e `Indicador → FK Criterio`, **invirtiendo** la relación real. Verificado contra la fuente (texto extraído del PDF `eq_sidaces.txt` y códigos de `parsed.txt`):
>
> ```
> I GESTIÓN INSTITUCIONAL | 1.1 | CRI | 1.1.1  Establecimiento de ...   ← Criterio (código X.Y.Z)
> I GESTIÓN INSTITUCIONAL | 1.1 | STD | 1.1.1.1 La institución de ...   ← Estándar (código X.Y.Z.W)
> I GESTIÓN INSTITUCIONAL | 1.1 | STD | 1.1.1.2 La institución cuenta...
> I GESTIÓN INSTITUCIONAL | 1.1 | CRI | 1.1.2  Ejecución del Plan ...
> I GESTIÓN INSTITUCIONAL | 1.1 | STD | 1.1.2.1 La institución cuenta...
> ```
>
> El texto oficial declara la secuencia "dimensiones, componentes, criterios, estándares, indicadores y evidencias". Los códigos encadenados confirman que **el criterio es PADRE del estándar**.
>
> **Jerarquía correcta para el modelo de datos:**
>
> ```
> Dimension (I..VIII)
>   └─ Componente (FK Dimensión, `X.Y`)
>       └─ Criterio (FK Componente, `X.Y.Z`)
>           └─ Estándar (FK Criterio, `X.Y.Z.W`)
>               └─ Indicador (FK Estándar, `X.Y.Z.W.N`)
>                   └─ EvidenciaIndicativa (FK Indicador, `X.Y.Z.W.N.n`)
> ```
>
> Nota de extracción: algunas filas del PDF presentan criterios con 4 segmentos (p. ej. `1.2.1.1`) por ruido en la maquetación; el patrón oficial mayoritario es `X.Y.Z` (criterio) y `X.Y.Z.W` (estándar). El importador deberá normalizar estos casos.

### 3.3 Evaluación oficial vs. revisión interna

El flujo actual aprueba/rechaza/observa a nivel de **Asignación** (indicador + unidad + período) y usa el vocabulario "aprobar evidencia". El informe no distingue:

- aprobación **administrativa del documento** (revisión interna),
- **evaluación oficial** (resultado/calificación MESCyT, aprobación oficial del estándar).

Además:

- El estado `completado` existe en `EstadoAsignacion` y en las métricas del dashboard, pero **no figura en el mapa de transiciones** `_validar_transicion` (`evaluation/views.py:265-277`) → es inalcanzable por el flujo.
- El frontend de asignaciones permite `PATCH` directo de estado (`patchAsignacion`) y un *toggle* aprobado/pendiente que **ignora `_validar_transicion`** → se pueden saltar reglas de transición desde la UI.
- `CriterioViewSet`/`IndicadorViewSet` llaman a `filtrar_por_rol(queryset, ..., dept_field="unidad_responsable")` sobre modelos que **no tienen** ese campo directo (Criterio/Indicador filtran vía `indicadores__asignaciones__...`). El `kwargs` `{unidad_responsable_id__in: ...}` aplicado a `Criterio`/`Indicador` no hace match con joins. En el caso del Evaluador Externo ese camino se evita porque `_filtrar_evaluador_externo` usa su propio mapa; pero para otros roles el filtro por `unidad_responsable_id__in` sobre Criterion/Indicador **devuelve vacío o error** según el rol — comportamiento frágil.

### 3.4 Organización y permisos

- Jerarquía organizativa nueva correctamente en marcha: `Facultad → Departamento` (legacy) y `UnidadOrganizacional` (tipo + padre + `departamento_legacy` 1:1). Migraciones `organization 0002→0004` y `evaluation 0005` **ya migraron** asignaciones y perfiles de departamento a unidad sin borrar datos → buen precedente de migración no destructiva.
- Roles (grupos Django): `Administrador General`, `Coordinador Quinquenal` (sin restricción), `Revisor Institucional`/`Consulta` (facultad), `Evaluador Externo` (solo registros **aprobados** de su ámbito). `CustomModelPermissions` mapea GET→`view_%s`, etc.
- `Evaluador Externo` ve solo lo aprobado (condición `estado=aprobado` en `_filtrar_evaluador_externo`) pero el **concepto de "estándar aprobado" no está modelado**; hoy "aprobado" aplica a la asignación del indicador.

### 3.5 Migraciones y datos

- No existe BD ni datos sembrados (no `db.sqlite3`, no fixtures). El catálogo EQ-SIDACES **no está cargado en ninguna tabla**: el sistema depende de alta manual.
- Migraciones existentes son aditivas y con precedentes de `RunPython` de datos no destructivos (`evaluation.0005`, `organization.0004`, `accounts.0004`).
- No hay `CheckConstraint`/`UniqueConstraint` que eviten duplicados de `Criterio.nombre`/`Indicador.nombre`.

### 3.6 Frontend Angular

- CRUD genérico y consistente (`CrudTable`, `SearchBar`, `Pagination`, `Modal`) usado por periodos/criterios/indicadores; evidencias tiene UI propia (selección + ZIP masivo + detalle).
- El frontend depende de campos serializados del backend (`periodo_nombre`, `criterio_nombre`, `indicador_nombre`, `unidad_responsable_nombre`, `estado_display`, `id_evidencia`, etc.): cualquier renombrado/cambio de shape de la API rompe estos componentes.
- `permisos.service`/`permiso.guard` + permisos hardcodeados en plantillas (e.g. `'evaluation.add_criterio'`). Aunque la UI los oculta, la autorización real está en el backend (positivo).
- Terminología mixta en UI: "Departamento" vs "Unidad responsable" (en evidencia-detalle se muestran ambos nombres) — reflejo de la transición departamento→unidad incompleta en labels.

### 3.7 Entornos y datos reales (inventario verificado el 2026-10-12)

- **No existe `db.sqlite3`** en el proyecto (gitignored en `.gitignore:22` y `backend/.gitignore:18`; verificado con búsqueda en todo el árbol, incluidos ocultos). No hay otros archivos `*.db`/`*.sql`.
- **La BD real es PostgreSQL**: `settings.py` lee `DB_ENGINE` (default `django.db.backends.sqlite3`) y `DB_NAME/USER/PASSWORD/HOST/PORT`. `docker-compose.yml` (dev) y `k8s/` (prod) montan Postgres con `DB_ENGINE=django.db.backends.postgresql`. `.env` y `backend/.env` contienen `DB_*` (valores no expuestos aquí). `backup.sh` usa `pg_dump`.
- **Docker/k8s no están corriendo ahora** en esta máquina (daemon inaccesible), por lo que en este momento no hay BD viva local; si el usuario levanta `docker compose` / k8s, la BD es Postgres.
- **Sí existen datos locales reales en disco:** `backend/media/` contiene 108 archivos — `media/evidencias/` = 45 archivos planos (patrón con sufijo aleatorio `_XXXXXXXX` de Django al resolver colisiones → producidos por `evidence.Evidencia.archivo` con `upload_to="evidencias/"`) y `media/profile_pictures/`. No hay subcarpetas anidadas (patrón legacy `periodo/unidad/indicador/`), lo que confirma que **el app que se usó para subir fue `evidence`, no `evidencias`**.
- **Pruebas:** suite Django `python manage.py test` (119/119 verdes según `docs/gestion/PENDIENTES_PRODUCCION.md`) y lint `ruff`. Frontend: `ng build` OK; `ng test` roto preexistente (22/29 specs).
- **Documentación existente:** `docs/gestion/PENDIENTES_PRODUCCION.md` ya lista como pendiente #6 "Consolidar las apps duplicadas de evidencia"; `TODO.md` marca la migración a PostgreSQL como hecha.

### 3.8 Referencias completas de la app `evidencias` (para su retirada/integración)

Inventario exahustivo (2026-10-12):

| # | Ubicación | Uso | Acción al retirar |
|---|---|---|---|
| 1 | `evaluacionQuinquenal/settings.py:79` | `INSTALLED_APPS` | quitar de la lista |
| 2 | `evaluacionQuinquenal/urls.py:42` | `include("evidencias.urls")` (ensombrecida) | eliminar include |
| 3 | `dashboard/views.py:29,99-100` | `EvidenciaLegada` en métrica `con_evidencia` | reemplazar por existencial única sobre `evidence` |
| 4 | `accounts/permissions.py:82,303` | mapa de `_filtrar_evaluador_externo` + fallback de `PuedeDescargarEvidencias` | eliminar entradas `evidencias.*` |
| 5 | `accounts/role_permissions.py:27,61,91,117,141` | permisos `evidencias.*` por rol y `OUR_APP_LABELS` | quitar de los 4 roles y de `OUR_APP_LABELS` |
| 6 | `pyproject.toml:82` | `known-first-party` de isort | limpiar (cosmético, do ruff check) |
| 7 | `evidencias/*` (models, serializers, views, urls, apps, migrations/0001, tests) | app completa | conservar como referencia tras consolidación; NO eliminar tablas hasta verificar vacías |
| 8 | Frontend `features/evidencias/evidencias.ts:43,49,54` | permisos `evidencias.*` en `puedeSubir`/`puedeCancelarReactivar`/`puedeDescargarMasivo` | dejar solo `evidence.*` |
| 9 | Frontend `features/roles/permission-labels.ts:54-57` | etiquetas "(antigua)" | eliminar |
| 10 | `dashboard/tests.py` (`data["evidencias"]`), `reportes/views.py:432` | etiqueta de métrica "evidencias" | solo keys JSON, no dependen del app |

El resto de la app (serializer legacy con validación de tipos/50 MB y `subido_por`) se **integra** en `evidence` (ver Fase 0, ítems 2–3) antes de proceder a la retirada.

---

## 4. Puntos de diseño que el marco oficial obliga a resolver (preguntas abiertas)

1. ¿La evaluación se determina por **indicador**, por **estándar**, o ambos? (afecta dónde se asigna/aprueba).
2. ¿La **evidencia indicativa** (catálogo) se usa como "plantilla" de lo que debe subir cada unidad? (recomendado: sí, es la regla del marco).
3. ¿"Aprobar" actual debe separarse en (a) revisión interna de documento y (b) **aprobación/evaluación oficial MESCyT**? El marco exige distinguirlo.
4. Aplicabilidad recintos/centros: confirmar la regla de "solo algunas dimensiones" y dónde se codifica (recomendado: tabla de aplicabilidad por tipo de unidad, no hard-coded en Angular).
5. ¿Existe una fecha de corte por período para la versión oficial del catálogo aplicada? (necesario para versionar el marco).

---

## 5. Propuesta de cambios (por fases, sin romper compatibilidad)

Principios: sin migraciones destructivas, sin renombrar/eliminar modelos a la ligera, sin borrar datos, manteniendo la API que ya consume el frontend, trabajo por etapas con tests.

### Fase 0 — Higiene inmediata (bajo riesgo)
1. **Retirar `evidencias.urls`** del `urls.py` raíz y desregistrar la app legacy de `INSTALLED_APPS` **solo después** de:
   - mover su utilidad restante al dashboard (cambiar `EvidenciaLegada` por una existencial de `evidence` con `Existencias` correctas) y
   - eliminar de `permissions.py` y del frontend las referencias `evidencias.*`.
2. **Validar tipos/máx tamaño de archivo** en el flujo actual `evidence` (mover la validación del serializer legacy al nuevo).
3. **Añadir `subido_por`** a `evidence.Evidencia` (o a `VersionEvidencia`) para restaurar notificaciones/trazabilidad; backfill opcional.
4. Corregir el filtro por rol de `CriterioViewSet`/`IndicadorViewSet` (usar el mapa de `_filtrar_evaluador_externo`/joins correctos) y eliminar el estado `completado` inalcanzable (o incorporarlo al mapa de transiciones).

### Fase 1 — Catálogo EQ-SIDACES alineado al marco (aditivo)
5. **Nuevas entidades (nuevas tablas, sin tocar las existentes) — jerarquía CORREGIDA (ver §3.2.1):**
   - `Dimension` (código `I..VIII`, nombre, definición, orden).
   - `Componente` (**FK → Dimensión**, código `X.Y`, nombre, definición, orden).
   - `Criterio` del marco (**FK → Componente**, código `X.Y.Z`, enunciado, definición, orden). El criterio cuelga del componente — eventualmente reutilizar `Criterio` añadiendo columnas.
   - `Estándar` (**FK → Criterio**, código `X.Y.Z.W`, redacción, rango/orientación cuantitativa, orden).
   - `Indicador` del marco (**FK → Estándar**, código `X.Y.Z.W.N`, redacción oficial, orden).
   - `EvidenciaIndicativa` (**FK → Indicador**, código `X.Y.Z.W.N.n`, descripción del documento esperado, orden).
6. **Versionado del catálogo:** tabla `VersionMarcoEvaluacion` (vigencia por período) y FK en los nodos; permite cargar el 2026 y revisiones futuras sin dañar datos actuales.
7. **Carga inicial:** script de importación reutilizable que lea el extraído del PDF y registre versión; con `--check` que compare conteos/códigos contra el documento (8/36/77/210/909/915) y no duplique.
8. **Aplicabilidad:** tabla `AplicabilidadIndicador → TipoUnidadOrganizacional` (o campo en `IndicadorMarco`) con la regla de recintos/centros confirmada.

### Fase 2 — Puente con el flujo existente (migración no destructiva)
9. Relacionar `Indicador` actual con `IndicadorMarco` (FK nullable) y `Asignacion` con el nivel oficial evaluado (estándar/indicador) según la respuesta a la pregunta 1.
10. Diferenciar en `EstadoAsignacion`/nuevo modelo la **revisión interna** de la **evaluación oficial** (sin asumir que aprobado = oficial).
11. Migrar `Criterio`/`Indicador` mediante `RunPython` a los nodos del marco (patrón probado en `evaluation.0005`), dejando `nombre_corto`/legacy y único constraint por `(codigo, version_marco)`.

### Fase 3 — Reportes, dashboard y frontend
12. Reportes/dashboard: unificar "con evidencia" sobre un único modelo; métricas por dimensión/componente/estándar y por nivel de la organización.
13. Angular: mapear labels y navegación a la jerarquía oficial; eliminar permisos `evidencias.*` del frontend; nueva vista "Evidencia indicativa / qué subir" por asignación.

### Fase 4 — Pruebas
14. Cubrir con tests: import del catálogo (conteos exactos), transiciones del flujo, aplicabilidad por tipo de unidad, permisos por rol, y compatibilidad de la API (regresiones de los `evaluation/tests.py`, `evidence/tests.py`, `dashboard/tests.py`, `reportes/tests.py` existentes).

---

## 6. Riesgos y decisiones pendientes

- **Renombrar/eliminar** `Criterio`, `Indicador`, `Evidencia`, `Asignacion` sin comparar dependencias romperá serializers/views/dashboard/reportes/frontend/tests. **No hacerlo**; se recomienda añadir columnas y nuevos modelos, y los cambios de significado se gestionan por migración de datos con copia de respaldo.
- La app legacy `evidencias` es 100% retirable pero **requiere** ajustar dashboard y permisos en el mismo cambio.
- El scheduler de "finalizar períodos vencidos" (`services.finalizar_periodos_vencidos`) desactiva períodos; validar que siga aplicable al catálogo versionado.
- Confirmar con el cliente: jerarquía de evaluación (indicador vs estándar), aplicabilidad recintos/centros y si la calificación oficial se registra dentro del sistema.