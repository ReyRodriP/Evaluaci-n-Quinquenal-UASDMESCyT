# 3B — Asignaciones directamente vinculadas al marco

## Estado al 21/10/2026

Implementación verificada automáticamente. Tras la autorización del usuario se
aplicó `evaluation.0007_asignacion_marco` en desarrollo, base
`evaluacion_quinquenal`, y se preparó la muestra técnica descrita abajo. Las suites
utilizaron PostgreSQL aislado y no quedaron bases temporales con prefijo
`test_uasd_marco_3b_`. El usuario confirmó que la prueba interactiva desde Angular
funciona correctamente y autorizó continuar con el siguiente incremento.

## Modelo y reglas

- Cada período puede seleccionar explícitamente `version_marco`; no se infiere del
  catálogo activo. Una versión piloto inactiva puede seleccionarse sin activarla
  globalmente. La versión no puede sustituirse mientras existan asignaciones del
  marco en el período. El guardado comparte un bloqueo transaccional del período
  para evitar carreras entre cambio de versión y creación de asignaciones.
- Cada asignación tiene exactamente uno de los dos orígenes: `indicador` operativo
  o `indicador_marco`. La restricción SQL `asignacion_origen_unico` lo garantiza.
- Para el marco, indicador + unidad responsable + período es una combinación única.
  Se conserva también la unicidad operativa existente.
- Las nuevas asignaciones del marco requieren indicador y unidad activos y un
  encargado activo de la misma unidad, autorizado para consultar asignaciones y
  consultar/aportar evidencias. Un evaluador externo no puede ser encargado.
  Se crean en estado `pendiente`.
- Indicador, estándar, criterio, componente y dimensión deben pertenecer todos a la
  versión seleccionada en el período.
- La API impide cambiar origen, unidad o período de una asignación del marco con
  evidencias, tanto activas como heredadas.
- El encargado identifica la responsabilidad individual; la colaboración mantiene
  los permisos existentes dentro de la unidad. La revisión interna respeta los
  ámbitos explícitos unidad-período de 3A.
- `encargado` permite NULL para conservar registros operativos y utiliza SET_NULL
  si se elimina el usuario. Las referencias al catálogo utilizan PROTECT.

## Contratos y consulta

`/api/periodos/` incorpora `version_marco` y `version_marco_nombre`.
`/api/asignaciones/` incorpora `indicador_marco`, `encargado`, `encargado_nombre`,
`tipo_origen`, `criterio_nombre` y `ruta_marco`. El campo `indicador` sigue
identificando exclusivamente un indicador operativo.

Ejemplo de creación por API, sustituyendo los identificadores por los aprobados:

```json
{
  "indicador_marco": 10,
  "unidad_responsable": 19,
  "periodo": 2,
  "encargado": 20
}
```

Los filtros directos son `version_marco`, `dimension`, `componente`,
`criterio_marco`, `estandar` e `indicador_marco`; se aplican a asignaciones,
evidencias activas y reportes de evidencias. Los IDs son los del catálogo. El
parámetro `indicador` conserva su significado operativo.

`ruta_marco` identifica versión, dimensión, componente, criterio, estándar e
indicador. Los códigos sintéticos del indicador se muestran como identificadores
internos no oficiales.

Angular muestra la ruta y el encargado en los detalles de asignación y evidencia.
Los grupos de asignaciones distinguen ambos orígenes; las asignaciones del marco
abren su detalle. El alta del marco está disponible por API y administración
Django; el formulario operativo anterior conserva su función.

Seguimiento y dashboard distinguen asignaciones directas de correspondencias
operativas. La ruta directa sirve para filtrar aunque no existan correspondencias.
Los conteos de indicadores suman ambos orígenes sin colisionar sus IDs. Auditoría,
notificaciones, descargas ZIP y reportes utilizan los nombres del origen correcto.
El acceso a detalles conserva el período histórico consultado.

## Alcance documental

Se conserva la relación actual de una evidencia activa por asignación y su historial
de versiones. Las solicitudes documentales múltiples, la revisión por documento y
el cierre global explícito corresponden a una fase posterior. La muestra acordada
de dos documentos en la asignación principal dependerá de esa fase.

La migración es de esquema: conserva asignaciones operativas, no crea
correspondencias, no importa catálogo ni carga asignaciones de muestra. Las
asociaciones documentales del piloto siguen siendo técnicas y provisionales según
la decisión D8 en `docs/decisiones_eq_sidaces.md`.

## Verificación automática

| Comprobación | Resultado |
|---|---|
| Suite backend, 13 aplicaciones, PostgreSQL aislado | 440 pruebas satisfactorias |
| Regresiones específicas `evaluation.test_asignaciones_marco` | 21 pruebas incluidas en la suite, con concurrencia, permisos, rollback y ciclo de evidencia |
| Suite Angular, Edge headless mediante ChromeHeadless | 250 pruebas satisfactorias |
| `npm run build` | Satisfactorio |
| `makemigrations --check --dry-run` | Sin cambios detectados |
| Ruff en filtros, migración y pruebas nuevas | Satisfactorio |
| `git diff --check` | Sin errores de espacios |

Los errores simulados de auditoría en los registros de pruebas verifican rollback
transaccional. Las advertencias locales de longitud de clave JWT y paginación ya
existían y no provocaron fallos.

## Puesta en servicio en desarrollo

- Migración aplicada y confirmada en `django_migrations`; `manage.py check` correcto.
- Versión ID 1, `EQ-SIDACES-2019-Res27-2019`, seleccionada explícitamente en período
  ID 2, `Periodo 2025-2030`. La versión conserva `activo=False`.
- Subconjunto importado del normalizado: estándares `6.1.1.2`, `6.2.1.2` y
  `8.4.1.1`, sus diez indicadores confirmados y sus ancestros. No se importaron
  evidencias indicativas. SHA256 del origen:
  `99a3c360be87adf6c048b177b9da16e1cc703522749c2f501f040ecc2f804d42`.
- Se conservaron el estándar `6.1.1.1` y su indicador preexistentes. El catálogo
  resultante tiene dos dimensiones, cuatro estándares y once indicadores; diez
  indicadores pertenecen a la nueva muestra.
- Preparación validada primero mediante transacción revertida y luego confirmada
  en una transacción. La reversión explica los huecos en IDs; los IDs definitivos
  de las asignaciones son 26–29.
- Altas de asignaciones y selección de versión realizadas mediante API interna con
  la cuenta de coordinación `MrRey`. Cada asignación tiene además una entrada de
  auditoría «Preparar muestra 3B» que la identifica como muestra técnica ficticia.
- Las asignaciones operativas conservaron exactamente sus campos durante la carga.

### Asignaciones de muestra

| ID | Indicador interno no oficial | Unidad | Encargado |
|---|---|---|---|
| 26 | `6.1.1.2-IND-01` | Unidad de Postgrado- UASD Barahona (23) | `usuario1` |
| 27 | `8.4.1.1-IND-01` | Unidad de Postgrado- UASD Barahona (23) | `usuario1` |
| 28 | `6.2.1.2-IND-01` | Escuela de Informática (14) | `sosua` |
| 29 | `6.1.1.2-IND-02` | Postgrado General (21) | `mrPopoMaster` |

Las cuatro quedaron `pendiente`, sin evidencias, listas para la prueba interactiva.
Son escenarios técnicos: la distribución no representa una decisión institucional
de responsabilidad sobre esos estándares.

### Comprobaciones HTTP sobre el servidor efectivo

Se verificaron con autenticación las listas y los cuatro detalles en el backend
local. Dentro de la muestra:

| Cuenta | IDs visibles | Detalles ajenos |
|---|---|---|
| `MrRey` | 26, 27, 28, 29 | No aplica: coordinación global |
| `usuario1` | 26, 27 | 28 y 29 devuelven 404 |
| `sosua` | 28 | 26, 27 y 29 devuelven 404 |
| `mrPopoMaster` | 29 | 26, 27 y 28 devuelven 404 |
| `jorge` | 26, 27 | 28 y 29 devuelven 404 |

`jorge` conserva su ámbito activo ID 1, Recinto Barahona (19), período 2. El servidor
efectivo confirma `AMBITOS_REVISION_EXPLICITOS=True`. La consulta de configuración
se comprobó con coordinación; el endpoint de gestión devuelve 403 al revisor sin
permisos de gestión de ámbitos.

También se comprobaron filtros directos por dimensión VI/VIII y los tres
estándares, y respuestas 200 en resumen, avance por criterio y pendientes del
dashboard. Angular compiló en modo desarrollo y `http://localhost:4200/` respondió
200. Backend local: `http://127.0.0.1:8000/`.

## Recorrido de prueba manual — validado por el usuario

1. Abrir `http://localhost:4200/` e iniciar sesión con `usuario1`. Seleccionar el
   período 2025–2030. En Asignaciones/Evidencias deben aparecer las nuevas
   asignaciones 26 y 27, además de las operativas que ya correspondan a su unidad.
2. Abrir `/asignaciones/26/detalle?periodo=2` y comprobar encargado y ruta completa:
   versión, dimensión VI, componente, criterio, estándar `6.1.1.2` e indicador.
   La asignación 27 debe mostrar dimensión VIII y estándar `8.4.1.1`.
3. Desde Evidencias, gestionar la asignación 26, crear su evidencia y subir un
   archivo de prueba claramente identificado como muestra. Enviar a revisión.
4. Entrar con `jorge`, revisar la evidencia y solicitar cambios. Volver a `usuario1`,
   cargar una versión corregida y reenviar; después aprobar con `jorge`.
   Comprobar versiones, observaciones, estados y notificaciones.
5. Con `jorge`, abrir directamente
   `/asignaciones/28/detalle?periodo=2`: debe denegarse el acceso sin conservar
   datos ni acciones del detalle anterior. La API correspondiente devuelve 404.
6. Con `MrRey`, revisar Seguimiento y Dashboard, filtrar por dimensiones VI/VIII y
   por los tres estándares, y comprobar CSV y ZIP después de subir evidencia.
7. Si se prueba revocación manual, desactivar el ámbito de `jorge` desde la cuenta
   de coordinación: debe perder los datos operativos y el acceso directo. Reactivar
   el mismo ámbito al terminar para continuar con el escenario preparado.

El usuario confirmó «todo funciona correctamente» después de este recorrido. Con
esa confirmación se da por validado manualmente 3B. Las comprobaciones HTTP de
preparación fueron de lectura; conservaron los cuatro estados pendientes y el
ámbito activo antes de la prueba del usuario. No se restablecen los estados ni se
eliminan las evidencias que el usuario haya generado durante esa prueba.
