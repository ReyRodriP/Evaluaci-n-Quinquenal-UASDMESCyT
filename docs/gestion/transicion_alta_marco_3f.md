# 3F — El marco como entrada principal de nuevas asignaciones

## Decisión y estado

Después de validar 3E, el usuario autorizó sustituir el alta operativa anterior
en la interfaz por la asignación directa al marco y conservar el acceso a los
registros existentes.

Transición implementada y verificada. El usuario confirmó que ya se visualiza y
autorizó continuar con el siguiente incremento.

## Cambios de interfaz

- El encabezado de **Asignaciones** muestra una sola entrada de creación:
  **Asignar indicador del marco**. Está disponible para Administración y
  Coordinación con permiso de alta, sobre el período activo.
- La acción principal abre el formulario del marco de 3E. El anterior formulario
  de nueva asignación operativa ya no se ofrece desde la pantalla.
- Los registros operativos existentes siguen apareciendo en el listado, identificados
  como **Asignación operativa existente**, con acceso a sus detalles y evidencias.
- El modal anterior queda reservado a **Editar asignación operativa existente**.
  Conserva unidad, período y estado. Los indicadores se mantienen asociados a sus
  registros originales.
- La edición de un grupo actualiza cada asignación existente con su propio ID e
  indicador. Ya no crea asignaciones al añadir indicadores ni elimina registros al
  modificar aquella selección.
- Un evento de guardado sin una asignación existente seleccionada no genera altas.
  Los permisos de modificación y eliminación se comprueban separadamente al mostrar
  las acciones. Los períodos finalizados conservan el modo de solo consulta.
- El componente compartido de encabezado admite personalizar el texto del alta;
  las otras pantallas mantienen su etiqueta habitual **+ Nuevo Registro**.

## Alcance de compatibilidad

Esta transición retira el alta anterior de la interfaz. Los contratos API existentes
se conservan para compatibilidad. No se reclasifican asignaciones, no se convierten
indicadores operativos en indicadores del catálogo ni se migran evidencias o
aprobaciones históricas.

La revisión y corrección de las entregas anteriores continúan en su flujo existente,
según los permisos y el período correspondientes. El nuevo flujo de solicitudes
documentales conserva sus reglas de 3C.

## Verificación

| Comprobación | Resultado |
|---|---|
| Suite completa frontend | 289 pruebas satisfactorias |
| Nuevas regresiones | 5: alta única, guardado sin selección, edición de grupo sin altas/bajas, consulta histórica y etiqueta compartida |
| Build Angular | Satisfactorio |
| Búsqueda de llamadas de creación en la funcionalidad de asignaciones | Solo permanece la creación directa del formulario del marco |
| `git diff --check` | Sin errores |
| Navegador con `MrRey` | Un solo botón de alta, formulario del marco y edición de registros operativos existentes correctos |
| Navegador, período histórico | Solo consulta, sin altas ni edición |
| Navegador, Períodos | El botón de creación habitual conserva su etiqueta |

Las pruebas de edición verifican que cada ID conserva su indicador aunque el
evento de formulario contenga una selección diferente, y que no se invocan los
endpoints de creación ni eliminación desde ese editor.

La comprobación en navegador fue de lectura y apertura/cierre de formularios. Una
firma de datos antes y después confirmó la conservación de asignaciones, períodos,
evidencias activas y heredadas, archivos registrados, versiones, solicitudes,
observaciones y revisiones. Esta transición no requiere cambios de esquema.

## Comprobación manual siguiente

1. Con `MrRey`, abrir `http://localhost:4200/asignaciones?periodo=2`.
2. Comprobar que hay una única entrada de alta y que abre la selección del marco,
   con unidad y encargado.
3. Abrir la edición de una asignación operativa existente: debe mostrar su editor
   de unidad/período/estado, sin una selección para añadir nuevos indicadores.
4. Abrir el detalle y las evidencias de una asignación anterior para continuar su
   trabajo según el estado y permisos actuales.
5. Seleccionar un período finalizado y comprobar que conserva solo consulta.
