# 3C — Solicitudes documentales y revisión por documento

Estado: implementación verificada automáticamente, después de la validación
manual de 3B. Migraciones generadas y pendientes de puesta en servicio autorizada
en desarrollo. La prueba interactiva de 3C todavía no se ha realizado.

## Objetivo acordado

Una asignación del marco puede solicitar varios documentos. Cada documento tiene
sus propias versiones, observaciones y decisión de revisión. La aprobación de todos
los documentos no aprueba automáticamente la asignación: el revisor debe ejecutar
una aprobación global explícita.

La asignación conserva indicador, unidad, período y encargado definidos en 3B. Los
colaboradores autorizados de la unidad pueden aportar documentación. El revisor
interno conserva el alcance explícito unidad-período de 3A.

## Contrato funcional del incremento

1. Definir varias solicitudes documentales para una asignación, con título y
   descripción de lo que debe entregarse.
2. Mostrar por separado solicitud, documento entregado y versiones de ese documento.
   Subir el documento B no debe crear una versión nueva del documento A.
3. Permitir enviar cada documento a revisión y consultar su historial.
4. Registrar observación y decisión sobre una versión concreta. La corrección crea
   una versión nueva; no sustituye el archivo que fue revisado.
5. Mostrar el progreso documental sin confundir «archivos cargados», «documentos
   aprobados» y «asignación aprobada».
6. Exigir una acción de aprobación global del revisor y validar en el servidor los
   requisitos documentales aplicables. La misma regla debe cubrir el endpoint de
   aprobación y las actualizaciones de estado para evitar rutas alternativas.
7. Mantener auditoría y notificaciones con identificación de solicitud/documento y
   versión, además de asignación.

## Compatibilidad y transición

- Las evidencias y aprobaciones ya existentes conservan su identidad, archivos e
  historial. La confirmación manual de 3B no autoriza reclasificarlos ni reabrirlos.
- La incorporación al nuevo flujo debe ser explícita. La muestra aprobada de dos
  documentos se preparará sobre una asignación adecuada al terminar la implementación;
  se comprobará primero el estado que dejó la prueba manual.
- Se mantienen las rutas de evidencias activas y heredadas. El diseño técnico debe
  adaptar los consumidores que hoy esperan una sola evidencia por asignación.
- La solicitud documental es una instrucción operativa. No convierte las evidencias
  indicativas del PDF en asociaciones oficiales con indicadores; D8 sigue pendiente.
- La aprobación global no redefine el estado institucional `completado`, ni introduce
  reversión de aprobaciones históricas.

## Implementación

- `SolicitudDocumental → VersionDocumento → RevisionDocumento` se incorpora a la
  app `evidence`. El flujo de `Evidencia → VersionEvidencia → Observacion` conserva
  sus relaciones e historial. No se realiza una conversión histórica de tablas.
- `Asignacion.gestion_documental`, de solo lectura en API, identifica la adhesión
  explícita. La primera solicitud la activa exclusivamente sobre una asignación
  directa al marco, pendiente y sin evidencias activas ni heredadas.
- Cada solicitud comienza pendiente; cargar un archivo crea un borrador. El envío
  explícito la pone en revisión. El revisor aprueba la versión enviada o solicita
  cambios con comentario obligatorio. La corrección crea una versión nueva.
- Los archivos y las decisiones documentales no tienen endpoints de sobrescritura.
  Una solicitud solo puede editarse/eliminarse antes de recibir versiones. Eliminar
  todas las solicitudes no desactiva el flujo y no permite un cierre vacío.
- Los nuevos requisitos bloquean el cierre hasta su aprobación. La asignación y
  cada documento mantienen decisiones diferenciadas. Una asignación cerrada no
  permite añadir requisitos, subir versiones ni modificar decisiones.
- Se bloquean período, asignación y solicitud en ese orden. La numeración tiene
  unicidad SQL por solicitud. El cierre se valida bajo el mismo bloqueo que las
  altas y decisiones, comprobando también la aprobación de la última versión.
- Los endpoints de actualización de estado y las acciones antiguas de revisión no
  permiten saltarse la revisión documental. Los endpoints de evidencia única
  revalidan bajo bloqueo que no se haya iniciado el nuevo flujo.
- La API de solicitudes consulta las asignaciones autorizadas por el filtro común
  de roles. La revocación del ámbito retira listas, detalles y descargas. El externo
  solo consulta asignaciones globalmente aprobadas y la última versión, sin las
  decisiones internas del historial.
- Angular integra el panel en el detalle de asignación: definición, carga, envío,
  revisión, descarga individual de versiones y aprobación global explícita. El
  listado de Evidencias abre este panel para asignaciones documentales.
- Seguimiento y dashboard cuentan una asignación con documentos entregados una sola
  vez en cobertura. El resumen distingue solicitados, entregados, aprobados y
  observados. El reporte de evidencias y sus exportaciones incorporan una fila por
  documento entregado. El ZIP de evidencias anterior conserva su selección por IDs
  de evidencia; los documentos nuevos se descargan individualmente desde el panel.

## Decisiones funcionales confirmadas por el usuario

1. Solo Administración y Coordinación crean y modifican solicitudes. El Revisor
   Institucional revisa entregas dentro de sus ámbitos.
2. Todas las solicitudes son obligatorias: cada documento debe estar aprobado antes
   de habilitar la aprobación global explícita.

## Verificación

- Dos documentos de una asignación con numeraciones de versión independientes.
- Observación/corrección de uno sin alterar la aprobación ni historial del otro.
- Prohibición de aprobar globalmente con requisitos pendientes, incluso mediante
  actualización directa de estado.
- Aprobación documental completa sin aprobación global automática.
- Aislamiento por unidad-período y revocación efectiva de ámbitos.
- Concurrencia de cargas y de aprobación frente a nuevas versiones/cambios de requisitos.
- Conservación de archivos, aprobaciones, IDs y rutas previos; regresión del flujo
  operativo y de los reportes.
- Suites PostgreSQL aisladas y Angular, build y comprobación de migraciones antes
  de solicitar la puesta en servicio de este incremento en desarrollo.

Resultados:

| Comprobación | Resultado |
|---|---|
| Suite completa backend, 13 aplicaciones, PostgreSQL aislado | 457 pruebas satisfactorias |
| Regresión posterior a ajustes finales de bloqueos, `evaluation` y `evidence` | 133 pruebas satisfactorias |
| Nuevas regresiones documentales incluidas | 17, incluidas cargas concurrentes y cierre frente a nuevo requisito |
| Suite Angular | 258 pruebas satisfactorias, incluidas ocho nuevas de panel, servicio, paginación y cobertura |
| Build Angular | Satisfactorio |
| `makemigrations --check --dry-run` | Sin cambios detectados |
| Ruff en módulo documental, pruebas y migraciones nuevas | Satisfactorio |

Las bases PostgreSQL temporales se destruyeron al terminar. Los fallos simulados
de auditoría en los logs verifican rollback de datos y limpieza del archivo recién
subido; no son errores de las suites.

## API y esquema pendiente de desarrollo

- `evaluation.0008_gestion_documental`: añade la marca de incorporación al flujo.
- `evidence.0003_gestion_documental`: crea solicitudes, versiones y revisiones.
- `/api/solicitudes-documentales/`: lista/alta y detalle; PATCH/DELETE de solicitud
  sin entregas para Administración/Coordinación.
- `/api/solicitudes-documentales/contexto/?asignacion=<id>`: permisos efectivos y
  progreso; todas las solicitudes se recuperan con la paginación correspondiente.
- Acciones por solicitud: `subir_version/`, `enviar/`, `aprobar/`,
  `solicitar_cambios/` y `descargar/?version=<id>`. Las decisiones deben enviar el
  `version_id` actual; la observación requiere `comentario`.
- `/api/asignaciones/<id>/aprobar/`: decisión global explícita, restringida a
  revisores autorizados para el flujo documental.

Se consultó el historial de migraciones de desarrollo: ambas migraciones 3C siguen
sin aplicar. La asignación 26 quedó aprobada durante la validación manual de 3B y
conserva su evidencia ID 16; 27, 28 y 29 seguían pendientes al inventariarlas.

## Puesta en servicio y prueba manual siguientes

Tras autorizar el despliegue de este incremento:

1. Aplicar ambas migraciones y reiniciar el backend antes de iniciar la prueba.
   El código actualizado requiere esas columnas y tablas; hasta aplicarlas no debe
   iniciarse otra prueba manual contra el servidor de desarrollo autorecargado.
2. Elegir una asignación pendiente sin evidencias dentro del ámbito de Barahona o
   crear una asignación técnica adicional con un indicador disponible. La 26
   conserva su aprobación e historial de evidencia única.
3. Con `MrRey`, abrir el detalle y definir dos solicitudes claramente identificadas
   como muestra técnica, con título y descripción. Ambas serán obligatorias.
4. Con el encargado autorizado, cargar y enviar los dos documentos. Comprobar que
   ambos comienzan con versión 1.
5. Con `jorge`, aprobar A y solicitar cambios en B. Con el encargado, corregir B y
   reenviarlo: A conserva versión 1 y B pasa a versión 2 con su historial anterior.
6. Aprobar B y comprobar que la asignación continúa en progreso. Ejecutar después
   «Aprobar globalmente la asignación» y verificar el cierre y los bloqueos de edición.
7. Verificar lectura histórica, descargas individuales, aislamiento por ámbitos,
   progreso en seguimiento/dashboard y filas documentales en el reporte de evidencias.
