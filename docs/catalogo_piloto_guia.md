# Catálogo EQ-SIDACES — Guía técnica del piloto

> **Estado:** piloto técnico. Los datos expuestos son **provisionales**: provienen de una
> extracción automatizada del PDF del marco EQ-SIDACES y **no constituyen un catálogo
> aprobado institucionalmente**. La versión importada permanece con `activo = false`.

## 1. Arquitectura del piloto

**Modelos** (`backend/catalogo/models.py`): `VersionMarcoEvaluacion → Dimension →
Componente → CriterioMarco → Estandar → IndicadorMarco` (+ `EvidenciaIndicativa`, sin datos
en el piloto). Todo cuelga de `version_marco`; unicidad por versión; una única versión
activa (constraint parcial). Migración `0002` convirtió `CriterioMarco.nombre` a `TextField`
(textos oficiales de hasta 529 caracteres).

**Importación** (`backend/catalogo/management/commands/import_eq_sidaces.py`): modos
`--check` (solo archivo), `--dry-run` (transaccional, revierte) y `--apply` (persiste);
importa solo registros **confirmados** con ancestros confirmados; idempotente
(`get_or_create`); no modifica `activo`; exige `--allow-synthetic-codes` en `--apply` para
generar códigos sintéticos de indicadores (`{estandar}-IND-{NN}`, no oficiales).

**Endpoints** (`/api/catalogo/`, solo lectura, `IsAuthenticated`, paginación 50):

| Endpoint | Filtro |
|---|---|
| `/api/catalogo/versiones/` | — (detalle incluye conteos por nivel) |
| `/api/catalogo/dimensiones/` | `?version={slug\|id}` |
| `/api/catalogo/componentes/` | `?dimension={id}` |
| `/api/catalogo/criterios/` | `?componente={id}` |
| `/api/catalogo/estandares/` | `?criterio={id}` |
| `/api/catalogo/indicadores/` | `?estandar={id}` |
| `/api/catalogo/exportar/` | `?version={slug\|id}` (obligatorio), `?dimension={id}` (rama opcional); devuelve CSV con BOM UTF-8, una fila por nodo con las columnas de ruta (`nivel, version, dimension, componente, criterio, estandar, codigo, nombre, codigo_sintetico, estado_revision`) |

Filtros inválidos → 400; detalle inexistente → 404; escrituras → 405. Los detalles incluyen
hijos directos y breadcrumb (`select_related`, sin N+1). `codigo_sintetico` marca los códigos
generados; `estado_revision: "confirmado"` refleja el invariante del importador.

**Componentes Angular** (Angular 20, standalone):
- `src/app/core/services/catalogo.service.ts` — cliente HTTP de los 7 endpoints (el de
  exportación descarga un `Blob`).
- `src/app/features/catalogo/catalogo.{ts,html,css}` — explorador jerárquico con migas de
  pan, aviso de provisionalidad, insignias «Confirmado»/«Código sintético (no oficial)»,
  estados de carga, error (con Reintentar) y lista vacía; con una versión seleccionada
  muestra el botón **«Exportar CSV»** que descarga `arbol_eq_sidaces_{slug}.csv`.
- Ruta `/catalogo` (tras `AuthGuard`) y entrada de menú «Catálogo EQ» visible para todo
  usuario autenticado (`grupos: null`).

## 2. Preparar y ejecutar el entorno de desarrollo

```powershell
# Backend (PostgreSQL local vía docker-compose o servicio del sistema)
Set-Location backend
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# Frontend (en otra terminal)
Set-Location frontend\evaluacion-quinquenal-front
npm start          # http://localhost:4200  → login → menú «Catálogo EQ»
```

El frontend usa `environment.apiUrl = http://localhost:8000/api`. Por defecto el backend
lee la BD de desarrollo `evaluacion_quinquenal` (que contiene una mini-muestra de 6
registros de prueba, **no** el piloto). Para navegar el piloto real:

```powershell
$env:DB_NAME = 'evaluacion_quinquenal_piloto'
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

## 3. Generar y validar el dataset piloto

```powershell
# Generar (reproducible; dimensión VI por defecto, solo confirmados, sin evidencias)
venv\Scripts\python.exe scripts\preparar_piloto_eq_sidaces.py

# Validar integridad/unicidad/trazabilidad
venv\Scripts\python.exe scripts\preparar_piloto_eq_sidaces.py --validar-solo

# Validar con el importador (no toca BD)
venv\Scripts\python.exe backend\manage.py import_eq_sidaces --file data/catalogo\eq_sidaces_piloto.json --marco-version EQ-SIDACES-2019-Res27-2019 --check
```

Salida: `data/catalogo/eq_sidaces_piloto.json` (75 registros: 1 dimensión, 2 componentes,
6 criterios, 16 estándares, 50 indicadores; 0 evidencias por decisión D8). Las exclusiones
quedan listadas en `meta.exclusiones` con clave y motivo.

## 4. Importar el piloto a la BD dedicada

```powershell
# Crear BD dedicada (idempotente; credenciales de backend/.env; opcional:
# argumento con otro nombre de base)
venv\Scripts\python.exe scripts\crear_bd_piloto.py
$env:DB_NAME = 'evaluacion_quinquenal_piloto'
venv\Scripts\python.exe backend\manage.py migrate

venv\Scripts\python.exe backend\manage.py import_eq_sidaces --file data/catalogo\eq_sidaces_piloto.json --marco-version EQ-SIDACES-2019-Res27-2019 --dry-run
venv\Scripts\python.exe backend\manage.py import_eq_sidaces --file data/catalogo\eq_sidaces_piloto.json --marco-version EQ-SIDACES-2019-Res27-2019 --apply --allow-synthetic-codes
```

Verificado: 75 filas creadas; segunda ejecución = 0 nuevos / 75 existentes (idempotente);
jerarquía íntegra; `activo = false`; tablas operativas vacías en esa BD. Recuperación:
`DROP DATABASE evaluacion_quinquenal_piloto`.

## 5. Resultados reales de pruebas (15/10/2026)

| Suite | Resultado | Comando |
|---|---|---|
| Backend (12 apps, incluye catalogo: 49 tests) | **236 OK** | `venv\Scripts\python.exe backend\manage.py test accounts auditoria dashboard evaluation evidence evidencias health notificaciones organization reportes search catalogo --noinput` |
| Frontend Karma (51 specs, incluye 14 del catálogo) | **51 SUCCESS** | `npm run test -- --watch=false --browsers=ChromeHeadless` (con `CHROME_BIN` apuntando a Edge si no hay Chrome) |
| Integración API real (BD piloto + JWT) | **OK** | 401 sin token; JWT; versiones (conteos 1/2/6/16/50); dimensión VI → 2 componentes; criterio 6.1.1 → 3 estándares; estándar 6.1.1.1 → 4 indicadores con `codigo_sintetico=true`, `codigo_oficial=null`, `estado_revision=confirmado`; filtro inválido → 400 |
| Exportación CSV real (BD piloto + JWT) | **OK** | 401 sin token → JWT → 200 `text/csv` con BOM y `filename="arbol_eq_sidaces_eq-sidaces-2019-res27-2019.csv"`; 75 filas de datos con distribución 1/2/6/16/50; columnas de ruta validadas contra pila DFS (0 errores); `estado_revision=confirmado` en todas las filas |
| Operativas intactas | **OK** | `Asignacion=21, IndicadorOp=37, Periodo=2, Evidencia=15` sin cambios antes/después |

## 6. Limitaciones conocidas

- Solo la dimensión VI (piloto). El resto del marco (2179 registros) está pendiente de
  revisión institucional (D1–D13 en `docs/decisiones_eq_sidaces.md`).
- Cero evidencias indicativas: su asociación a indicadores es hipótesis sin resolver (D8).
- Los códigos de indicadores son sintéticos (la fuente oficial no asigna código).
- El importador no hace upsert de correcciones (re-importar la misma versión reutiliza
  existentes por `codigo_completo`, pero no actualiza textos).
- `estado_revision` es un invariante del importador, no un campo por fila.
- La exportación es **solo CSV** (UTF-8 con BOM); un PDF/imprimible del árbol requiere
  un incremento adicional.
- Pantalla Angular sin E2E real contra navegador (la integración se cubrió con specs
  Karma + smoke HTTP contra la BD piloto).

## 7. Decisiones institucionales pendientes

Mantenimiento de la matriz D1–D13 (`docs/decisiones_eq_sidaces.md`): duplicados de
estándar (D1–D3), indicadores sin viñeta (D4), textos contaminados (D5), correcciones
puntuales (D6/D7), asociación evidencia↔indicador (D8), permisos de visualización (D9),
vinculación futura con `evaluation.Indicador` (D10), palabras partidas (D11), definiciones
de dimensión (D12), alcance de la importación completa (D13). Ninguna resuelta aún; ninguna
es necesaria para continuar con el siguiente incremento funcional.

## 8. Revisión de Git (sin commitear a 15/10/2026)

- **Modificados:** `backend/accounts/urls.py` (ancla `^me$` — corrige captura de
  `/api/catalogo/dimensiones/`), `backend/catalogo/models.py` (nombre → TextField),
  `backend/catalogo/views.py` y `urls.py` (endpoint `exportar/`),
  `backend/catalogo/tests/test_api.py` (base compartida + 9 tests de exportación),
  `app.routes.ts` (+ruta), `permisos.service.ts` (+menú),
  `catalogo.service.ts`/`.spec.ts` (+`exportarCsv`), `features/catalogo/*`
  (+botón «Exportar CSV» y specs).
- **Nuevos:** migración `0002_alter_criteriomarco_nombre.py`, `scripts/crear_bd_piloto.py`
  (creación idempotente de la BD piloto), `scripts/preparar_piloto_eq_sidaces.py`,
  `data/catalogo/eq_sidaces_piloto.json`, `docs/catalogo_piloto_guia.md`.
  **Borrado:** `tests/test_diag.py` (diagnóstico temporal).
- **Sensibles:** `.env` ignorado por gitignore ✓; los JSON/CSV de `data/catalogo/`
  contienen texto extraído del PDF oficial (marco público institucional) — revisar antes
  de publicar el repositorio.

## 9. Siguiente incremento recomendado

**Vinculación visual del catálogo con el flujo operativo** (no nueva investigación):
permitir que `Asignaciones`/`Evidencias` muestren, en modo solo lectura, el estándar e
indicador del marco asociados al criterio operativo seleccionado — ya con catálogo
consultable, API probada, pantalla base y exportación CSV del árbol. Requiere decisión
previa mínima: cómo mapear `evaluation.Criterio/Indicador` (operacionales) con
`catalogo.CriterioMarco/IndicadorMarco` (sin tocar modelos: tabla de correspondencia
explícita).
