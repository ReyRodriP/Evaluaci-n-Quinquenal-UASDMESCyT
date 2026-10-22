# 3D — Seguimiento y resultados operativos por dimensión y estándar

## Estado

Implementado y verificado automáticamente y en navegador sobre desarrollo. El
usuario confirmó previamente el funcionamiento y la presentación de 3C, y después
confirmó que 3D funciona perfectamente. Se da por validado manualmente este incremento.

No incorpora cambios de esquema. `makemigrations --check --dry-run` no detecta
cambios. Las consultas y exportaciones conservaron asignaciones, solicitudes,
versiones y decisiones existentes.

## Alcance funcional

- Reportes → **Marco EQ-SIDACES** permite agrupar las asignaciones directas del
  período por dimensión o estándar y filtrar por unidad, dimensión y estándar.
- La versión se toma de la selección explícita del período; el catálogo piloto
  continúa globalmente inactivo. Las correspondencias operativas no se convierten
  en asignaciones directas ni se suman a este reporte.
- Las opciones de dimensión y estándar se derivan de las asignaciones autorizadas
  del período y unidad, antes de aplicar los filtros del marco. No se inventan
  responsabilidades para los indicadores no asignados del catálogo.
- El reporte distingue asignaciones con archivos, aprobadas globalmente y pendientes
  de cierre, además de documentos solicitados, entregados, aprobados, en revisión
  y observados.
- CSV, Excel y PDF exportan todos los grupos autorizados con los mismos filtros,
  independientemente de la página visible.
- Seguimiento muestra la existencia de evidencia también para documentos nuevos,
  el progreso entregados/solicitados y aprobados/solicitados, el enlace a Documentos
  y el estado **Documentos aprobados · pendiente de cierre global** cuando corresponda.
  Su CSV añade el progreso documental cuando la selección contiene este flujo.

## Definiciones

1. **Asignaciones**: responsabilidades visibles vinculadas directamente a un
   indicador del marco en el período y filtros seleccionados. Cada una cuenta una vez.
2. **Con archivos**: asignaciones con al menos un archivo registrado en una versión
   documental, una versión de evidencia anterior o una evidencia heredada. No implica
   aprobación ni envío de todos los documentos.
3. **Documentos entregados**: solicitudes que tienen versiones. Las correcciones
   incrementan versiones, no el número de documentos ni el de asignaciones.
4. **Documentos aprobados / en revisión / observados**: solicitudes en ese estado
   documental actual. El progreso documental se refiere al flujo de solicitudes
   múltiples, sin reclasificar las evidencias anteriores.
5. **Pendientes de cierre**: asignaciones documentales abiertas, con al menos una
   solicitud y todas las solicitudes aprobadas, pendientes de decisión global.
6. **Aprobación global (%)**: asignaciones con estado `aprobado` divididas entre
   asignaciones visibles tras los filtros, multiplicadas por 100 y redondeadas a
   un decimal. Es un resultado operativo del subconjunto autorizado, no una
   calificación o ponderación oficial del marco completo.

Se conserva el significado existente de `completado` y de las aprobaciones previas.
Los contadores no reabren ni modifican registros del flujo de revisión.

## Permisos y contratos

- `/api/reportes/marco/` y `/api/reportes/marco/exportar/` utilizan
  `PuedeVerReportes`: Administración, Coordinación y Revisor Institucional según
  los permisos existentes.
- Ambos endpoints aplican el filtro común de asignaciones por rol y el ámbito
  unidad-período. El externo y el responsable departamental no reciben acceso al
  reporte por este incremento.
- Un período no autorizado al revisor devuelve 404. Una unidad fuera de su alcance
  no produce resultados. La exportación no amplía ese alcance.
- Filtros: `periodo`, `unidad`, `agrupar=dimension|estandar` y los filtros directos
  `version_marco`, `dimension`, `componente`, `criterio_marco`, `estandar`,
  `indicador_marco`. La pantalla expone período, unidad, dimensión, estándar y agrupación.
- Paginación de consulta: `page`, `page_size`. La respuesta incluye `rows`,
  `resumen`, `opciones`, contexto de período/versión y metadatos de paginación.
- Exportación: `formato=csv|xlsx|pdf`. CSV incluye BOM UTF-8; Excel conserva métricas
  numéricas y trata los nombres como texto. PDF usa códigos de dimensión/estándar
  para mantener la legibilidad.
- Los cambios de filtro/período cancelan la consulta anterior. Una pérdida de acceso
  retira resultados y controles de exportación, sin conservar cifras anteriores.

## Verificación

| Comprobación | Resultado |
|---|---|
| Backend completo, 13 aplicaciones, PostgreSQL aislado | 466 pruebas satisfactorias |
| Nuevas regresiones de reporte del marco | 8 incluidas: conteos, cierre, observación, ámbitos, períodos, filtros y exportaciones |
| Frontend completo, Edge headless | 273 pruebas satisfactorias |
| Nuevas regresiones frontend | 8 incluidas: reporte, filtros, exportación, respuestas obsoletas y seguimiento documental |
| Build Angular | Satisfactorio |
| Ruff en módulo y pruebas nuevos | Satisfactorio |
| `makemigrations --check --dry-run` | Sin cambios detectados |
| Comprobación HTTP autenticada | Consulta y CSV/XLSX/PDF correctos con coordinación y revisor; 403 para responsable y externo |
| Navegador con `jorge` | Reporte, agrupación por estándar, filtro `8.4.1.1`, botón CSV y seguimiento correctos |
| Pantalla de 390 px | Sin desbordamiento horizontal de página; tabla con desplazamiento propio |

Los tests verifican que varias versiones no duplican documentos, que documentos
aprobados no equivalen a cierre global, que la revocación retira consulta/exportación,
que no se cruzan ámbitos de distintos períodos y que la exportación incluye todos
los grupos filtrados aunque la consulta esté paginada.

### Estado observado en desarrollo durante la comprobación

| Cuenta | Asignaciones directas | Con archivos | Aprobadas globalmente | Grupos por dimensión / estándar |
|---|---|---|---|---|
| `MrRey` | 4 | 2 | 1 | 2 / 3 |
| `jorge` | 2 | 2 | 1 | 2 / 2 |

Las dos solicitudes de la asignación 27 tenían archivos: una aprobada y otra
observada. El reporte reflejó dos documentos entregados, uno aprobado y uno
observado, y cero asignaciones pendientes de cierre. La aprobación global fue
25 % para coordinación y 50 % para el revisor, debido a sus distintos denominadores
autorizados. Estas cifras son una instantánea y cambiarán con el trabajo del usuario.

El servidor local conservaba configuración de un proceso anterior; se reinició
el proceso iniciado para desarrollo y se repitió la comprobación HTTP correctamente.
Las sesiones anteriores pueden requerir iniciar sesión nuevamente. No se cambiaron
usuarios ni configuraciones institucionales durante la verificación.

## Recorrido manual siguiente

1. Iniciar sesión con `MrRey` y abrir
   `http://localhost:4200/reportes?reporte=marco&periodo=2`.
2. Comparar agrupación por dimensión y por estándar; filtrar el estándar `8.4.1.1`
   y una unidad responsable. Revisar los contadores de asignación y de documentos.
3. Exportar CSV, Excel y PDF y comprobar que conservan los filtros seleccionados.
4. Entrar con `jorge` y consultar el mismo reporte: debe mostrar únicamente el
   ámbito de Barahona, sin las asignaciones de Informática y Postgrado General.
5. En Seguimiento, comprobar la existencia de evidencia y el progreso documental
   de la asignación 27. El estado documental observado se muestra sin alterar el
   estado global de la asignación.
6. Al continuar una corrección documental, revisar que aprobar todos los documentos
   habilita el estado pendiente de cierre; solo la aprobación global debe aumentar
   el contador de asignaciones aprobadas.

El usuario confirmó «Funciona perfectamente, podemos proseguir». La fase 3D queda
validada manualmente; se conservan los datos y resultados existentes al continuar.
