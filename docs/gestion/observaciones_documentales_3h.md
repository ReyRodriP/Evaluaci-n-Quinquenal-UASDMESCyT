# 3H — Observaciones y trazabilidad de revisiones documentales

## Estado

Implementado y verificado automáticamente y en navegador de desarrollo, después
de que el usuario validó la descarga ZIP de 3G. Disponible para la siguiente
comprobación manual. El usuario confirmó después que todo estaba bien y autorizó
continuar; se da por validada manualmente la fase 3H.

## Alcance funcional

- **Reportes → Observaciones** reúne las observaciones activas del flujo anterior
  y las revisiones documentales que contienen comentario.
- La tabla identifica el origen y la decisión: **Comentario** para el registro
  anterior, **Cambios solicitados** o **Aprobada con comentario** para una revisión
  documental. No se infiere una decisión antigua a partir del estado actual de la
  asignación.
- Una aprobación documental sin comentario no crea una observación ficticia en
  el reporte. Los comentarios anteriores continúan disponibles después de corregir
  o aprobar una versión posterior.
- Se mantienen los filtros de período, unidad y observador y se añaden **Origen**
  y **Decisión de revisión**. Los observadores disponibles se derivan de comentarios
  dentro del alcance autorizado; el revisor no necesita consultar el listado de usuarios.
- **Ver versión comentada** abre el recurso correspondiente y resalta la versión
  exacta del historial, tanto para documentos nuevos como para evidencias anteriores.
- Excel y PDF utilizan los mismos filtros y exportan el conjunto autorizado completo,
  independientemente de la página visible. PDF permite continuar comentarios largos
  en varias páginas y trata el texto de observación literalmente.

## Contadores y trazabilidad

El resumen conserva `total_observaciones` y `evidencias_observadas`; este último
cuenta recursos con comentarios mediante la pareja tipo + ID, no por título.
Dos documentos o evidencias de igual título o de IDs coincidentes siguen siendo
recursos distintos. En la pantalla se etiqueta como **Evidencias y documentos con
comentarios** para distinguir historia de revisión de estado actual.

Cada fila conserva los campos anteriores de evidencia, indicador, unidad/período,
versión, observador, comentario, fecha y total de observaciones del recurso dentro
de los filtros. Añade:

- `tipo_recurso`: `evidencia` o `documento`.
- `origen` y `decision_display`: etiquetas visibles.
- `recurso_id`, `asignacion_id`, `periodo_id` y `version_id`.
- `observacion_id`, `observador_id` y `decision`.
- `unidad_responsable` y su ID, manteniendo `departamento` por compatibilidad.

Los resultados se ordenan de más reciente a más antiguo por la fecha real del
registro. La respuesta incorpora `observadores` para preparar el filtro de autores.

Excel conserva las nueve columnas anteriores y añade origen, decisión e IDs de
asignación, recurso y versión. Los nombres y comentarios se guardan como texto,
incluidos valores que podrían interpretarse como fórmulas. PDF prioriza los campos
legibles del comentario, su versión, origen y decisión; la identificación numérica
completa está disponible en Excel y en los enlaces de la pantalla.

## Contratos y permisos

- Se mantienen `/api/reportes/observaciones/` y
  `/api/reportes/observaciones/exportar/` con su permiso de consulta interna de reportes.
- Filtros: `periodo`, `unidad_organizacional`, `departamento`, `usuario`,
  `origen=evidencia|documento` y `decision=comentario|observada|aprobada`. Los filtros
  directos del marco también se aplican a las asignaciones autorizadas.
- Consulta: `page` y `page_size`. Exportación: `formato=xlsx|pdf`.
- Se reutiliza el filtro común de asignaciones por rol y ámbito unidad-período.
  La revocación retira consulta y exportación del período afectado. No se cruzan
  unidades de un ámbito con períodos de otro.
- Las observaciones internas no se conceden al evaluador externo por combinar su
  rol con uno de revisión. Los roles globales conservan su precedencia existente.
- Un cambio de filtro cancela la consulta anterior. Una pérdida de acceso retira
  filas, autores, contadores y exportación habilitada; una respuesta anterior no
  vuelve a mostrar datos de otro filtro.
- Los enlaces documentales utilizan `documento` y `version_documento` en el detalle
  de asignación. El detalle anterior utiliza `version` junto con su período.

El incremento es de consulta y presentación. No cambia decisiones, estados,
archivos ni el flujo de aprobación global, y no requiere migraciones de esquema.

## Verificación

| Comprobación | Resultado |
|---|---|
| Backend completo, 13 aplicaciones, PostgreSQL aislado | 490 pruebas satisfactorias |
| Nuevas regresiones backend | 9 incluidas: conteos, historial, filtros, ámbitos, exportaciones, consulta interna y PDF con comentarios largos |
| Frontend completo | 304 pruebas satisfactorias |
| Nuevas regresiones frontend | 8 incluidas: tabla, filtros, enlaces, exportación, pérdida de alcance, respuestas obsoletas y resaltado de versiones |
| Build Angular | Satisfactorio |
| Ruff en módulo y pruebas nuevos | Satisfactorio |
| `makemigrations --check --dry-run` | Sin cambios detectados |
| HTTP con coordinación y revisor | Consulta documental y Excel/PDF correctos con filtros |
| HTTP con responsable y externo | Consulta y exportación denegadas con 403 |
| Navegador con `jorge` | Filtros, autores autorizados y apertura de versiones exactas de ambos flujos correctos |
| Pantalla de 390 px | Sin desbordamiento horizontal de página |

Las pruebas comprueban que corregir la versión 1 no cambia su comentario histórico,
que las aprobaciones sin comentario no inflan los contadores y que dos recursos de
igual título e ID se distinguen por origen. Las exportaciones verifican los filtros,
el texto literal, la conservación de IDs y la inclusión de todos los resultados.

La comprobación de navegador utilizó las observaciones existentes de desarrollo.
Una firma de datos antes y después confirmó que asignaciones, períodos, evidencias,
solicitudes, versiones, observaciones y decisiones permanecieron iguales.

## Recorrido manual siguiente

1. Con `jorge` o `MrRey`, abrir
   `http://localhost:4200/reportes?reporte=observaciones&periodo=2`.
2. Elegir **Origen → Documento solicitado** y **Decisión de revisión → Cambios
   solicitados**. Comprobar el comentario, autor y número de versión.
3. Pulsar **Ver versión comentada**. Debe abrir el documento y destacar la versión
   vinculada a la observación, aunque exista una corrección posterior.
4. Volver al reporte y seleccionar **Evidencia anterior** para consultar los
   comentarios del flujo previo y abrir su versión correspondiente.
5. Exportar Excel y PDF y comprobar que reflejan los filtros. En Excel, revisar
   también los identificadores de recurso y versión.

El usuario confirmó «Todo bien, podemos continuar».
