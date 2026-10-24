# 3J — Consulta del historial global de asignación

## Estado

Implementado, verificado técnicamente y validado manualmente por el usuario.

## Funcionalidad

El detalle de una asignación incorpora un panel de historial global que presenta:

- Estado anterior y nuevo estado.
- Fecha del cambio.
- Nombre del autor, con identificador de cuenta como alternativa. Si la cuenta ya
  no está asociada, se muestra «Sin cuenta asociada».
- Comentario del registro, cuando existe.
- Navegación paginada, con los registros más recientes primero.

Se consultan las transiciones ya registradas. Una asignación sin registros muestra
el estado vacío correspondiente. La revisión individual de documentos conserva su
historial propio; aprobar un documento no implica el cierre global de la asignación.

## API y permisos

`GET /api/asignaciones/<id>/historial/?periodo=<id>&page=1&page_size=10`

- Reutiliza la visibilidad de la asignación por rol, unidad y período.
- El historial interno se restringe para el rol Evaluador Externo, respetando la
  precedencia existente de superusuarios y roles globales.
- Tamaño predeterminado: 10 registros; máximo: 100.
- Orden estable por fecha descendente e identificador descendente.
- Respuesta paginada con `count`, `next`, `previous`, `results`, `page` y `page_size`.
- Se conservan los campos anteriores del serializador y se añaden
  `usuario_identificador`, `estado_anterior_display` y `estado_nuevo_display`.

El panel limpia los datos al cambiar de contexto o perder acceso y se oculta cuando
el acceso al historial interno devuelve 403. Este incremento no requiere migraciones.

## Verificación técnica

- Siete pruebas backend específicas de historial satisfactorias.
- Suite completa backend: 509 pruebas satisfactorias.
- Suite frontend: 315 pruebas satisfactorias, incluidas cinco del nuevo panel.
- Compilación Angular y comprobación de migraciones pendientes satisfactorias.
- Comprobación HTTP en desarrollo con el revisor `jorge` y el encargado `usuario1`
  sobre la asignación 27 del período 2: acceso y paginación correctos.
- Acceso desde `sosua`, de otra unidad: 404.
- Navegador Edge: panel con autor, estado y comentario reales; presentación de
  escritorio y móvil de 390 píxeles sin desbordamiento horizontal.
- Comparación antes/después: sin cambios en asignaciones, historial, períodos,
  solicitudes, versiones ni revisiones documentales durante esta comprobación.

## Recorrido de validación manual

1. Entrar con una cuenta autorizada y seleccionar el período 2025–2030.
2. Abrir una asignación con transiciones registradas, por ejemplo:
   `http://localhost:4200/asignaciones/27/detalle?periodo=2`.
3. Localizar el panel de historial y comprobar estados, autor, fecha y comentario.
4. Consultar una asignación sin transiciones y verificar el mensaje de historial vacío.
5. Si existen más de diez registros, recorrer las páginas y comprobar el orden.
6. En el flujo documental habitual, comprobar que aprobar documentos conserva su
   revisión individual y que el cierre global explícito aparece en este historial.
7. Repetir con un usuario de otra unidad y comprobar la restricción de acceso.

Las pruebas de cambios de estado deben realizarse sobre asignaciones destinadas a
validación. La comprobación técnica en desarrollo descrita arriba fue de lectura.

## Continuidad

Al validar 3J quedarían dos bloques de la propuesta de cierre funcional:
**3K — Validación integral por roles** y **3L — Documentación y demostración final**.
El alcance y los pendientes institucionales y de producción están en
`estado_fases_y_cierre.md`.
