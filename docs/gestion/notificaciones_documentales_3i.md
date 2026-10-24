# 3I — Avisos del ciclo documental y acceso al detalle

## Estado y decisión confirmada

Implementado, verificado y desplegado en desarrollo después de la validación
manual de 3H. El usuario decidió que los documentos enviados a revisión avisen
**solo a Revisores Institucionales autorizados**, sin avisos automáticos a
Coordinación.

El usuario confirmó que funciona correctamente y autorizó continuar. Se da por
validado manualmente el recorrido de notificaciones de 3I.

## Eventos y destinatarios

| Evento | Aviso | Destinatarios |
|---|---|---|
| Crear solicitud | Nueva solicitud documental | Encargado con acceso vigente |
| Cambiar título/descripción antes de entregas | Solicitud documental actualizada | Encargado con acceso vigente; no se duplica por guardar los mismos valores |
| Retirar solicitud sin entregas | Solicitud documental retirada | Encargado con acceso vigente; enlace a la asignación si la solicitud ya no existe |
| Enviar un documento o corrección | Documento enviado a revisión | Revisores Institucionales activos con permiso de revisión y alcance unidad-período |
| Aprobar una versión o solicitar cambios | Documento revisado | Encargado y autor de la versión, si conservan acceso |
| Aprobar globalmente la asignación | Asignación aprobada globalmente | Encargado con acceso vigente |

Se excluye al actor de su propio aviso y se deduplican destinatarios cuando
encargado y autor son la misma cuenta. La carga de un borrador no notifica a los
revisores: el aviso se genera al enviarlo explícitamente a revisión. Cada nueva
versión reenviada tiene su propio aviso y destino.

Si no hay revisores activos autorizados, el envío documental se conserva y no se
convierte en un aviso automático a Coordinación. Los roles globales mantienen su
acceso existente al seguimiento y la revisión; eso no los añade a la distribución
acordada salvo que tengan también el rol de Revisor Institucional.

## Destinos y acceso vigente

- `DestinoNotificacionDocumental` enlaza un aviso nuevo con su asignación y,
  cuando corresponde, solicitud y versión. La consistencia de esas referencias
  se valida al crearlo.
- La API incorpora el campo de solo lectura `destino` con `asignacion_id`,
  `periodo_id`, `solicitud_id` y `version_id`. Los textos no se interpretan como URLs.
- En Notificaciones aparece **Abrir detalle** para avisos con destino estructurado.
  La campana también abre ese detalle. Se utilizan rutas internas conocidas y
  parámetros numéricos válidos.
- Antes de navegar se consulta el endpoint de lectura del aviso, incluso si ya
  estaba leído. La respuesta del servidor proporciona el destino autorizado actual.
  Los avisos de versiones abren el documento con su **Versión referenciada** resaltada.
- El listado sigue siendo personal. Los avisos documentales además se limitan a
  asignaciones actualmente visibles para el destinatario; una revocación o cambio
  de unidad retira el aviso del listado y bloquea su apertura con 404.
- **Marcar todas como leídas** actúa sobre los avisos visibles, sin modificar los
  documentales que dejaron de estar autorizados.
- Los avisos anteriores conservan sus mensajes y lectura personal. No se les
  inventan destinos a partir del contenido histórico.

## Transacciones y correo

El aviso y su destino se guardan dentro de la transacción de la acción documental.
Si falla esa acción, se revierten ambos y se descarta el correo pendiente.

El correo documental, cuando está habilitado y configurado, se programa después
del commit y vuelve a comprobar actividad, permisos y alcance del destinatario.
Una incidencia posterior de entrega se registra sin deshacer la acción confirmada.
La notificación en la aplicación permanece como registro del aviso.

El cierre global conserva el comentario en su aviso documental y evita el segundo
aviso genérico por unidad del flujo anterior. La aprobación documental y el cierre
global mantienen mensajes y acciones separados.

## Esquema y puesta en servicio

- Generada y aplicada `notificaciones.0002_destinos_documentales` en PostgreSQL
  `evaluacion_quinquenal`.
- La migración crea únicamente la tabla de destinos; depende de los esquemas
  existentes de asignación y documentos. No añade destinos a notificaciones previas.
- Una firma de datos antes y después confirmó la conservación de asignaciones,
  períodos, evidencias, versiones, observaciones, solicitudes, revisiones, avisos
  existentes, perfiles, ámbitos y permisos de grupos.
- Se inició el backend con el esquema actualizado. La lectura HTTP de avisos con
  `usuario1`, `jorge` y `MrRey` devolvió 200 y únicamente avisos de su propia cuenta.
- La evaluación de destinatarios actuales de la asignación 27 identificó solo a
  `jorge`, coherente con el ámbito de Barahona y la decisión del usuario.

La comprobación de puesta en servicio fue de lectura. No se generaron eventos
documentales ficticios ni avisos retroactivos en desarrollo. Los destinos nuevos
aparecerán al realizar acciones documentales a partir del despliegue.

## Verificación

| Comprobación | Resultado |
|---|---|
| Suite completa backend, 13 aplicaciones, PostgreSQL aislado | 502 pruebas satisfactorias |
| Regresión final de notificaciones, asignaciones del marco y documentos | 59 pruebas satisfactorias |
| Comprobación final de notificaciones y entrega tras commit | 20 pruebas satisfactorias |
| Nuevas regresiones backend | 12 incluidas: destinatarios, ámbito, duplicados, propiedad, revocación, cierre, rollback y correo |
| Suite completa frontend | 310 pruebas satisfactorias |
| Nuevas regresiones frontend | 6 incluidas: destinos estructurados, revalidación, pérdida de alcance, apertura única y compatibilidad de campana |
| Build Angular | Satisfactorio |
| Ruff en notificaciones y migración | Satisfactorio |
| `makemigrations --check --dry-run` | Sin cambios detectados |
| Verificación HTTP de lectura en desarrollo | Correcta; avisos existentes e historiales conservados |

Las pruebas comprueban que Coordinación no recibe los envíos por defecto, que no
se avisa a revisores inactivos o ajenos al ámbito, que repetir un envío ya realizado
no duplica mensajes y que el correo no se entrega antes del commit ni después de
perder el acceso. La navegación usa el destino devuelto por el servidor, no una
copia anterior del navegador ni una URL del mensaje.

## Recorrido manual siguiente

1. Con **`usuario1`**, abrir una asignación documental de prueba. Si continúa la
   muestra de la asignación 27, cargar la corrección del documento observado y
   pulsar **Enviar documento a revisión**.
2. Entrar con **`jorge`**. Revisar la campana o abrir
   `http://localhost:4200/notificaciones`; debe aparecer **Documento enviado a revisión**.
   La campana consulta periódicamente los avisos; recargar la página los actualiza.
3. Abrir el aviso y comprobar asignación, documento y versión resaltada. El aviso
   debe quedar leído.
4. Con `jorge`, aprobar la versión o solicitar cambios. Con `usuario1`, comprobar
   **Documento revisado** y su acceso a la versión correspondiente.
5. Al completar todos los documentos, ejecutar la aprobación global explícita y
   comprobar su aviso separado para el encargado.
6. Al definir una solicitud de otra asignación de prueba con `MrRey`, comprobar
   que su encargado recibe **Nueva solicitud documental**. Los avisos anteriores
   al despliegue mantienen su presentación histórica sin botón de detalle.

El usuario confirmó «Bien, funciona correctamente, podemos seguir».
