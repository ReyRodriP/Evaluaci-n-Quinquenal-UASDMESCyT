# 3K — Validación integral por roles

## Estado

Verificación técnica satisfactoria el 24 de octubre de 2026. Pendiente de validación
manual del recorrido desde la interfaz por el usuario.

3J ya fue validado por el usuario. Este bloque comprueba que los incrementos
anteriores funcionan juntos sobre un mismo expediente documental.

## Verificación automatizada

Archivo: `backend/evaluation/test_recorrido_integral.py`.

Se incorporan dos recorridos completos: uno con alta de asignación por Coordinación
y otro con alta por Administración General. Se utilizan peticiones API con JWT;
las operaciones del expediente se realizan mediante sus endpoints. El catálogo,
las cuentas y los ámbitos del escenario son sintéticos.

| Paso | Actor | Comprobación |
|---|---|---|
| Alta | Coordinación / Administración | Asignación directa al indicador del marco, unidad, período y encargado |
| Solicitudes | Coordinación | Informe y acta obligatorios e independientes |
| Acceso inicial | Encargado, colaborador y revisor | Acceso dentro de la unidad y ámbito autorizados |
| Restricciones iniciales | Anónimo, encargado, otra unidad y externo | Autenticación requerida, alta restringida y expediente no divulgado |
| Primera revisión | Encargado y revisor | Informe aprobado; acta observada con comentario |
| Cierre prematuro | Revisor | Rechazado mientras falta aprobar el acta |
| Corrección | Colaborador, encargado y revisor | Segunda versión del acta aprobada sin reemplazar su versión anterior |
| Resultados previos al cierre | Revisor | Dos documentos aprobados y una asignación pendiente de cierre |
| Avisos | Revisor | Tres envíos a revisión dirigidos al revisor autorizado, con versión precisa y marcado de lectura |
| Cierre | Revisor | Aprobación global explícita; el encargado no puede ejecutarla |
| Historial | Encargado | Dos transiciones globales reales, con autor y comentario del cierre |
| Bloqueo posterior | Encargado | No se admite una nueva carga tras el cierre |
| Consulta externa | Evaluador Externo | Expediente aprobado visible; solo versión actual, sin revisión ni historial internos |
| Observaciones | Revisor | Comentario original conservado sobre la versión observada |
| Reportes | Revisor | Una aprobación global, sin pendiente de cierre; CSV/XLSX/PDF del marco y XLSX/PDF de observaciones |
| ZIP | Encargado, revisor y externo | Informe v1 y acta v2, con contenido y manifiesto consistentes |
| Correo de prueba | Revisor, encargado y colaborador | Destinatarios autorizados; otra unidad y externo excluidos |
| Revocación | Revisor | Se pierde acceso al expediente, historial, reportes, avisos documentales y ZIP |
| Período distinto | Encargado | No se entrega el historial de otro período |

Los correos se capturan en memoria y se ejecutan explícitamente los callbacks
poscommit de las pruebas. Esto verifica la integración de destinatarios y generación
de mensajes; la entrega mediante un proveedor SMTP corresponde al entorno desplegado.

### Resultados

- Dos recorridos nuevos satisfactorios, tanto de forma independiente como dentro
  de la suite completa.
- **511 pruebas backend satisfactorias** en PostgreSQL aislado.
- Ruff satisfactorio para el archivo nuevo.
- Sin incidencias funcionales detectadas en los recorridos ejecutados.
- Bases temporales eliminadas al terminar; archivos y correo de prueba aislados.
- La primera ejecución de la suite completa alcanzó el límite de tiempo del comando;
  se eliminó su base temporal sin conexiones activas y se repitió con tiempo suficiente.

La configuración efímera utilizada establece un `DATABASES.default.TEST.NAME`
único con prefijo `test_uasd_notis_3i_`, caché en memoria, almacenamiento temporal y
correo en memoria. No se modificó el expediente de desarrollo para ejecutar estos
recorridos. La comprobación de interfaz se completa con el recorrido siguiente.

## Recorrido manual de aceptación

### Preparación

- Seleccionar un período activo con su versión del marco explícitamente configurada.
- Usar una asignación nueva destinada a validación con un indicador disponible,
  una unidad, un encargado y un revisor con ámbito sobre esa unidad y período.
- Disponer de dos archivos de prueba y una corrección para el segundo.
- Tener un colaborador de la misma unidad si se desea comprobar esa participación.
- Para la consulta externa, disponer de una cuenta con ámbito de evaluación sobre
  la misma unidad y período. No se deduce su autorización de la del revisor interno.

### Secuencia

1. **Coordinación:** crear la asignación y solicitar «Informe» y «Acta».
2. **Encargado:** abrirla desde Asignaciones, cargar ambos documentos y enviarlos a
   revisión. Comprobar que una carga sin envío no se confunde con un envío a revisión.
3. **Revisor:** abrir el aviso del documento, aprobar el informe y solicitar cambios
   en el acta con un comentario reconocible, por ejemplo «Completar fecha del acta».
4. **Revisor:** comprobar que la asignación todavía no admite cierre global.
5. **Encargado o colaborador:** cargar la corrección del acta y enviarla a revisión.
   El informe debe conservar su versión y aprobación.
6. **Revisor:** aprobar la nueva versión del acta. Comprobar en resultados que ambos
   documentos están aprobados y que la asignación sigue pendiente de cierre.
7. **Revisor:** aprobar globalmente la asignación con un comentario identificable.
8. **Encargado:** comprobar el aviso de cierre y el historial global en el detalle
   de la asignación. El comentario de la observación anterior debe seguir en el acta.
9. **Coordinación o revisor:** consultar los resultados y las observaciones,
   exportarlos y descargar el ZIP. Debe incluir las últimas versiones de ambos
   documentos, mientras el reporte conserva la observación de la versión anterior.
10. **Usuario de otra unidad:** comprobar que no puede acceder a ese expediente.
11. **Evaluador Externo autorizado:** comprobar que consulta el expediente aprobado
    y los archivos actuales, sin comentarios de revisión ni historial global interno.

La revocación ya tiene comprobación automatizada integral. Si se repite manualmente,
utilizar un ámbito de prueba: desactivarlo y comprobar que los enlaces previamente
abiertos dejan de dar acceso al revisor.

## Criterio de cierre

Registrar el resultado manual o cualquier incidencia indicando actor, asignación,
paso, resultado esperado y resultado obtenido. Una vez validado 3K, quedará
**3L — Documentación y demostración final** dentro de la propuesta de cierre
funcional de `estado_fases_y_cierre.md`.
