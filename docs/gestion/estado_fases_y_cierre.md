# Estado de los incrementos y propuesta de cierre funcional

## Incrementos validados por el usuario

| Incremento | Resultado |
|---|---|
| 3A | Ámbitos explícitos de revisión interna |
| 3B | Asignaciones directamente vinculadas al marco |
| 3C | Solicitudes múltiples, versiones independientes y revisión por documento |
| 3D | Seguimiento y resultados por dimensión/estándar |
| 3E | Alta de asignaciones del marco desde la interfaz |
| 3F | Alta del marco como entrada principal; gestión de registros existentes |
| 3G | ZIP unificado de documentos y evidencias anteriores |
| 3H | Observaciones y acceso a versiones comentadas |
| 3I | Notificaciones documentales con destinatarios y destinos autorizados |

Son nueve incrementos validados. Los documentos de diagnóstico anteriores contienen
otra numeración y propuestas históricas: no fijan un número cerrado de incrementos
restantes con las letras 3A–3I.

## Estimación de cierre del alcance funcional actual

Para responder a la consulta del usuario y evitar ampliar indefinidamente los
incrementos, se propone completar tres bloques, contando el que se aborda ahora:

1. **3J — Historial global de asignación y cierre.** Consulta de transiciones,
   responsable de cada registro, fecha y comentario, con permisos y paginación.
2. **3K — Validación integral por roles.** Comprobación del recorrido completo:
   asignar, solicitar, cargar, observar, corregir, aprobar documentos, cerrar,
   consultar historial, recibir avisos, exportar reportes y descargar ZIP.
   Las incidencias de ese recorrido se resuelven dentro de este bloque.
3. **3L — Documentación y demostración final.** Actualizar los manuales funcionales
   y técnicos del flujo implementado y preparar un recorrido reproducible de entrega.

3J está implementado y verificado técnicamente, incluida la consulta HTTP y la
presentación en navegador de escritorio y móvil. Su validación manual está pendiente;
el recorrido se detalla en `historial_asignacion_3j.md`.

 **Este conteo es una estimación propuesta para el cierre funcional, no una lista
oficial de fases previamente aprobada.** Al validar 3J quedarían dos bloques de
esta propuesta. Las nuevas solicitudes de funcionalidad modificarían el alcance.

## Pendientes que no se consideran resueltos con ese cierre

- Validación institucional del catálogo completo, sus discrepancias y la asociación
  de evidencias indicativas con indicadores: `docs/decisiones_eq_sidaces.md`.
- Reglas oficiales de aplicabilidad y evaluación que todavía requieran confirmación.
- Puesta en producción: infraestructura, dominio/HTTPS, servicios externos y
  verificaciones del entorno desplegado descritos en `PENDIENTES_PRODUCCION.md`.

Los incrementos funcionales actuales utilizan el catálogo piloto explícitamente
seleccionado para el período. Su validación técnica no equivale a aprobar el catálogo
ni una calificación oficial institucional.
