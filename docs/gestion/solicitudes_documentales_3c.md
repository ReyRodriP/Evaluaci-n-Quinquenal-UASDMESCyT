# 3C — Solicitudes documentales y revisión por documento

Estado: implementación verificada automáticamente y puesta en servicio autorizada
en desarrollo, después de la validación manual de 3B. Ambas migraciones están
aplicadas y la muestra de dos documentos está preparada en la asignación 27.
El usuario confirmó que el flujo funciona totalmente bien y que la interfaz se ve
bien tras la corrección de presentación y acceso. Se da por validada manualmente 3C.

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
  documento entregado. En el despliegue inicial de 3C, los documentos nuevos se
  descargaban individualmente desde el panel. El incremento 3G amplía la descarga
  masiva para incluirlos junto con las evidencias anteriores.

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

## API y esquema aplicado en desarrollo

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

Tras la autorización del usuario se aplicó `migrate evidence
0003_gestion_documental`, que incluye la dependencia
`evaluation.0008_gestion_documental`. Ambas quedaron confirmadas en
`django_migrations` de PostgreSQL `evaluacion_quinquenal`; `manage.py check` no
reportó incidencias. Se iniciaron backend y Angular con el esquema actualizado.

## Muestra técnica preparada

- Asignación **27**, indicador interno `8.4.1.1-IND-01`, estándar de gestión de
  riesgos, período **2025–2030** (2).
- Unidad: **Unidad de Postgrado- UASD Barahona** (23). Encargado: **`usuario1`**.
- Revisor de la muestra: **`jorge`**, con ámbito activo en Recinto Barahona (19),
  período 2. Se mantiene el modo explícito de ámbitos.
- `gestion_documental=True`; asignación y solicitudes pendientes, sin versiones.

| Documento | Solicitud | Título |
|---|---|---|
| A | 3 | [Muestra 3C] Metodología documentada de gestión de riesgos |
| B | 4 | [Muestra 3C] Acta de revisión de la metodología de riesgos |

Ambas solicitudes son obligatorias y sus descripciones aclaran el carácter ficticio
y la asociación documental técnica, no oficial. Se crearon por API interna con la
cuenta `MrRey`, con auditoría de alta y «Preparar muestra 3C». Primero se verificó
la preparación mediante una transacción revertida; por eso los IDs 1 y 2 no son
los definitivos. La transacción confirmada produjo los IDs **3 y 4**.

Se compararon las otras asignaciones, las evidencias activas y los historiales
antes y después de la preparación y conservaron sus campos. En particular, la
asignación **26** sigue aprobada, con su evidencia **16** y flujo anterior.

### Comprobaciones HTTP del servidor efectivo

| Cuenta | Consulta de solicitudes 3/4 | Definir | Aportar | Revisar |
|---|---|---|---|---|
| `MrRey` | 200 | Sí | Sí | Sí |
| `usuario1` | 200 | No | Sí | No |
| `jorge` | 200 | No | No | Sí |
| `sosua` | 404; listado vacío | Fuera de alcance | Fuera de alcance | Fuera de alcance |
| `mrPopoMaster` | 404; listado vacío | Fuera de alcance | Fuera de alcance | Fuera de alcance |
| `revisor` (externo) | 404; listado vacío | No | No | No |

El contexto informa dos documentos y cero aprobados. Ninguna de las tres cuentas
autorizadas tiene habilitada la aprobación global mientras faltan las entregas.
Se comprobaron respuestas 200 en resumen y avance por criterio del dashboard y en
el reporte de evidencias. Angular compiló en modo desarrollo y respondió 200 en
`http://localhost:4200/`. Backend: `http://127.0.0.1:8000/`.

Las comprobaciones HTTP de puesta en servicio fueron de lectura: los documentos
quedaron sin archivos ni decisiones para la prueba del usuario.

## Prueba manual pendiente

1. Abrir `http://localhost:4200/asignaciones/27/detalle?periodo=2` con **`usuario1`**.
   Comprobar los documentos A y B y que no aparecen controles para crear solicitudes.
2. Cargar un archivo de prueba en A y otro en B. Pulsar **Enviar documento a revisión**
   en cada uno. Ambos deben comenzar con versión 1.
3. Con **`jorge`**, abrir el mismo detalle, aprobar A y solicitar cambios en B con
   un comentario. La asignación todavía no debe poder aprobarse globalmente.
4. Con **`usuario1`**, cargar una corrección de B y reenviarla. A conserva versión 1;
   B tiene versión 2, con la observación y el archivo anterior en su historial.
5. Con **`jorge`**, aprobar B. Comprobar que la asignación continúa en progreso y
   ahora aparece **Aprobar globalmente la asignación**.
6. Ejecutar la aprobación global y comprobar el cierre, las notificaciones y los
   bloqueos de edición. Revisar descargas de las versiones de ambos documentos.
7. Con **`MrRey`**, consultar Seguimiento, Dashboard y el reporte de evidencias:
   la cobertura cuenta una asignación y el reporte incorpora sus dos documentos.

El usuario confirmó el funcionamiento después de este recorrido y de la corrección
de interfaz descrita abajo. La fase 3C queda validada manualmente; sus archivos,
decisiones e historiales se conservan al avanzar al siguiente incremento.

## Corrección de presentación y acceso desde Evidencias (22/10/2026)

El usuario reportó que el panel documental no conservaba el diseño de evidencia
individual y que, después de subir los archivos, el listado parecía vacío y el
revisor no encontraba cómo abrirlos.

El inventario confirmó que la asignación 27 estaba en progreso y las solicitudes
3 y 4 estaban en revisión, con sus archivos guardados. El problema era de
integración: el listado consultaba solo evidencias del flujo anterior y sus botones
dependían de `evidenciaId`, que no identifica una solicitud documental.

Correcciones:

- El listado consulta las solicitudes por período y muestra una fila por documento,
  con título, archivo, estado documental y observación de revisión. El acceso al
  detalle está disponible para el revisor aunque no tenga permiso de carga.
- «Ver detalle» abre el documento seleccionado mediante `documento=<id>`. Descargar
  utiliza el identificador de solicitud y versión correspondientes; el historial
  abre el detalle documental. La búsqueda incluye el título del documento.
- El panel y la cabecera reutilizan el CSS de la evidencia individual: tarjetas,
  indicadores de estado, historial a la izquierda y acciones a la derecha. Las
  pestañas permiten seleccionar cada evidencia y mantener independientes sus archivos,
  versiones y decisiones. La selección se conserva tras guardar o revisar.
- Se incorpora vista previa de imágenes, PDF y texto, con descarga para los otros
  formatos. La disposición pasa a una columna en pantallas pequeñas.
- Se conserva el filtro de permisos por asignación en el nuevo filtro de período.

Verificación de la corrección:

| Comprobación | Resultado |
|---|---|
| Suite frontend completa | 265 pruebas satisfactorias |
| Suite documental PostgreSQL aislada | 18 pruebas satisfactorias |
| Build Angular | Satisfactorio |
| Ruff en módulo documental y pruebas | Satisfactorio |
| `git diff --check` | Sin errores |
| Navegador Edge con la cuenta `jorge` | Dos filas con archivos y acceso al detalle; ambos documentos muestran controles de revisión |
| Estilos efectivos en navegador | Tarjetas y botones del detalle individual, distribución de historial/acciones |
| Vista previa real | Imagen del documento B cargada correctamente |
| Pantalla de 390 px | Una columna, sin desbordamiento horizontal |

La comprobación en navegador fue de consulta: no ejecutó aprobaciones ni alteró los
archivos enviados. El usuario puede continuar la revisión desde Evidencias con
los documentos que ya cargó; no necesita volver a subirlos.
