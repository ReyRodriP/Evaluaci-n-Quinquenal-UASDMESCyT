# 3E — Alta de asignaciones del marco desde la interfaz

## Estado

Implementado y verificado automáticamente y en navegador de desarrollo después
de la validación manual de 3D. El usuario confirmó que funciona perfectamente.

## Recorrido funcional

1. En **Períodos**, la edición y creación permiten seleccionar explícitamente una
   versión del marco. La tabla muestra la versión asociada a cada período. El
   selector incluye versiones globalmente activas e inactivas y consulta todas
   las páginas disponibles.
2. En **Asignaciones**, Administración y Coordinación disponen del botón
   **Asignar indicador del marco** para el período activo seleccionado.
3. El formulario presenta el período y su versión y permite seleccionar dimensión,
   componente, criterio, estándar e indicador, con limpieza de las selecciones
   descendientes al cambiar de rama.
4. La unidad se identifica por su ruta organizacional completa para distinguir
   unidades de igual nombre. El encargado se elige entre usuarios activos de esa
   unidad autorizados para consultar y aportar evidencias.
5. La ruta completa del indicador permite revisar la selección antes del alta. Los
   códigos sintéticos siguen identificándose como internos, no oficiales.
6. Si ya existe la combinación indicador + unidad + período, se ofrece abrir esa
   asignación y se deshabilita el alta duplicada.
7. **Crear y abrir gestión documental** guarda la asignación pendiente mediante el
   contrato existente de 3B y abre su detalle. Allí se definen las solicitudes
   obligatorias de 3C, activando el flujo documental al crear la primera solicitud.

Durante la implementación de 3E coexistieron las dos opciones de alta. Tras la
validación del usuario, la transición de `transicion_alta_marco_3f.md` deja el marco
como única entrada de creación de asignaciones desde la interfaz. Las referencias
al marco se guardan directamente en `indicador_marco`, con encargado explícito.

## Contratos y validaciones

- `GET /api/asignaciones/contexto-marco/?periodo=<id>&unidad=<id opcional>` devuelve
  período, versión, unidades activas con sus rutas, indicadores activos de la
  versión, encargados elegibles y asignaciones existentes de la unidad y período.
- El contexto requiere autenticación, rol global de Administración/Coordinación y
  permisos de consulta y alta de asignaciones. Revisor, responsable y externo no
  acceden a este endpoint de preparación.
- El período debe estar activo y tener una versión explícita. No se infiere una
  versión a partir de su estado global ni se activa el catálogo al seleccionarla.
- Cada indicador y sus ancestros se comprueban con `validar_referencia_marco`.
  Los indicadores inactivos o de una jerarquía incoherente no aparecen en el alta.
- Los candidatos a encargado se comprueban con `validar_encargado`, la misma
  validación usada al guardar la asignación. No basta con pertenecer a la unidad.
- El guardado continúa en `POST /api/asignaciones/`, con `periodo`,
  `indicador_marco`, `unidad_responsable` y `encargado`. El servidor revalida sus
  condiciones y la unicidad; las opciones de la pantalla no sustituyen esas reglas.
- La interfaz evita envíos duplicados mientras guarda, conserva los datos al
  recibir errores de validación y descarta respuestas de unidades anteriores.
- La selección de versión en Períodos mantiene la protección existente: no puede
  sustituirse cuando el período ya tiene asignaciones del marco. El mensaje del
  servidor se presenta en la interfaz.

## Verificación

| Comprobación | Resultado |
|---|---|
| Backend completo, 13 aplicaciones, PostgreSQL aislado | 473 pruebas satisfactorias |
| Nuevas regresiones de contexto/alta | 7 incluidas: permisos, elegibilidad, versión, jerarquía, duplicados y revalidación |
| Frontend completo, Edge headless | 284 pruebas satisfactorias |
| Nuevas regresiones frontend | 11 incluidas: formulario, integración, versión del período y paginación |
| Build Angular | Satisfactorio |
| Ruff en contexto y pruebas nuevos | Satisfactorio |
| `makemigrations --check --dry-run` | Sin cambios detectados |
| Comprobaciones HTTP reales | Contexto correcto para coordinación; 403 para revisor, responsable y externo |
| Navegador con `MrRey` | Selección jerárquica, encargado elegible, ruta completa, duplicado bloqueado y selector de versión correctos |
| Navegador con `jorge` | Botón de alta del marco oculto |
| Pantalla de 390 px | Sin desbordamiento horizontal |

El guardado y la disponibilidad posterior de la gestión documental se verificaron
en PostgreSQL de pruebas. En el navegador de desarrollo se preparó el formulario
sin enviarlo y se comparó una firma de los datos antes y después: asignaciones,
períodos, solicitudes, versiones, revisiones y versiones del catálogo se conservaron.

El incremento no requiere migraciones de esquema. Las bases temporales utilizadas
por las suites se destruyen al finalizar.

## Prueba manual siguiente

1. Iniciar sesión con **`MrRey`** y abrir
   `http://localhost:4200/asignaciones?periodo=2`.
2. Pulsar **Asignar indicador del marco** y verificar la versión seleccionada para
   2025–2030.
3. Como escenario de prueba disponible durante la verificación, seleccionar:
   dimensión **VI** → componente **6.1** → criterio **6.1.1** → estándar
   **6.1.1.2** → indicador de orden **3**, «Las jerarquías están diferenciadas por
   beneficios y remuneración».
4. Seleccionar **Unidad de Postgrado- UASD Barahona** y el encargado **`usuario1`**.
   Revisar la ruta y pulsar **Crear y abrir gestión documental**. Si esa combinación
   ya se creó durante otra prueba, utilizar el enlace a la asignación existente.
5. Comprobar que la asignación está pendiente y que se pueden definir sus solicitudes
   documentales con coordinación. Crear solicitudes de muestra claramente
   identificadas y continuar con carga y revisión usando `usuario1` y `jorge`.
6. Volver al alta y elegir la misma combinación: debe ofrecer la asignación ya
   existente. Elegir una unidad sin candidatos válidos: debe impedir el guardado.
7. En **Períodos**, comprobar que el período conserva su versión explícita y que
   las versiones inactivas se identifican en el selector.

El usuario confirmó el funcionamiento de 3E y autorizó retirar el alta operativa
anterior de la interfaz, conservando el trabajo existente.
