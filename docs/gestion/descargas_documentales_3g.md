# 3G — Descarga ZIP unificada de evidencias y documentos

## Estado

Implementado y verificado automáticamente y en navegador sobre desarrollo,
después de que el usuario confirmó la visualización de la transición 3F.
El usuario confirmó que funciona correctamente y autorizó continuar. Se da por
validada manualmente la descarga ZIP unificada.

## Recorrido funcional

- En **Evidencias**, los documentos entregados del nuevo flujo pueden seleccionarse
  para descarga masiva, individualmente o con **Seleccionar esta página**.
- El mismo ZIP puede contener evidencias del flujo anterior de la app `evidence`
  y documentos de solicitudes documentales. Las filas siguen identificando ambos
  recursos y sus archivos por separado.
- Cada evidencia/documento aporta su última versión. El ZIP incluye `manifest.csv`
  para identificar los archivos, asignaciones y versiones.
- El contador suma ambos tipos y aplica un máximo conjunto de **100 selecciones**.
  Los IDs de ambos modelos se conservan en conjuntos separados para evitar colisiones.
- Las solicitudes sin versiones no pueden seleccionarse desde la pantalla. Si un
  archivo registrado falta en almacenamiento, el ZIP autorizado informa el problema
  en `manifest.csv` y `errors.csv`.
- La selección se limpia al descargar correctamente, cambiar de período o perder
  acceso a los datos. Al recargar, se retiran selecciones que ya no estén visibles.
- Las respuestas de consultas anteriores se descartan para que un cambio rápido
  de período no restaure filas ni selecciones del período anterior.
- Mientras se prepara el ZIP se evita repetir el envío o cambiar el período de
  esa selección.

## Contrato API y compatibilidad

Se amplía el endpoint existente:

`POST /api/evidencias/descargas-masivas/`

```json
{
  "evidencias": [16],
  "solicitudes": [3, 4]
}
```

Las listas contienen IDs de evidencia y solicitud respectivamente, no IDs de
versiones. Puede enviarse solo una de las listas. Se admiten IDs enteros positivos
y se deduplican por tipo; un ID numérico coincidente de ambos modelos identifica
dos recursos independientes.

Las peticiones anteriores con solo `evidencias` conservan las columnas básicas
de `manifest.csv` y los nombres de archivo del flujo anterior. Cuando se incluyen
documentos se añaden:

- `tipo_recurso`: `evidencia` o `documento`.
- `solicitud_id`: ID de solicitud para documentos; vacío para una evidencia anterior.
- `titulo_documento`: título de la solicitud documental.
- `version_id`: identificador de la versión incorporada.

En una fila documental, `evidencia_id` queda vacío. Las rutas nuevas utilizan
`DOC-<id>`; las anteriores mantienen `EVID-<id>`. Así no se sobrescriben archivos
por coincidencia de IDs o nombres. Los textos del CSV se protegen frente a su
interpretación como fórmulas al abrirlos en una hoja de cálculo.

Las evidencias heredadas de la app `evidencias` mantienen sus rutas de consulta y
descarga existentes; no se reclasifican ni se incorporan implícitamente al lote.

## Permisos, límites y auditoría

- Se conserva el permiso de descarga existente. Incluir solicitudes documentales
  requiere además los permisos de consulta de asignación y evidencia utilizados
  por la API documental.
- Cada tipo de recurso se consulta mediante su alcance autorizado. Las solicitudes
  se limitan a las asignaciones visibles por rol y ámbito unidad-período, con los
  filtros directos del marco y de período cuando se proporcionan.
- Si algún ID solicitado no existe o no está autorizado, se rechaza el lote
  completo con **404**, sin generar un ZIP parcial de los elementos permitidos.
- El evaluador externo conserva su acceso únicamente a asignaciones globalmente
  aprobadas y a la versión actual de cada documento.
- Máximo conjunto de 100 elementos y **250 MB sin comprimir**. El tamaño se
  verifica con los metadatos y de nuevo al leer los archivos.
- Se utilizan buffers temporales que pasan a disco después de 8 MB; los recursos
  se cierran al terminar la respuesta o al fallar la operación.
- La auditoría registra cuenta, selección por tipo, períodos, archivos incluidos
  y bytes. La descarga no cambia estados, versiones ni decisiones.

## Verificación

| Comprobación | Resultado |
|---|---|
| Backend completo, 13 aplicaciones, PostgreSQL aislado | 481 pruebas satisfactorias |
| Nuevas regresiones backend de ZIP documental | 8 incluidas: versiones, mezcla de IDs, ámbitos, externo, límites, errores, entradas inválidas y cierre de buffers |
| Frontend completo | 296 pruebas satisfactorias |
| Nuevas regresiones frontend | 7 incluidas: selección independiente, envío único, límite combinado, pérdida de alcance, ausencia de archivo, respuestas fuera de orden y compatibilidad del contrato |
| Build Angular | Satisfactorio |
| Ruff en módulo y pruebas nuevos | Satisfactorio |
| `makemigrations --check --dry-run` | Sin cambios detectados |
| Navegador con `jorge` | Selección mixta, descarga real y limpieza del contador correctas |
| ZIP generado desde la interfaz | Tres archivos íntegros; manifiesto con versiones e IDs correspondientes; verificación CRC correcta |
| Cuenta fuera del ámbito | Lote mixto rechazado completo con 404 |
| Pantalla de 390 px | Barra adaptable sin desbordamiento de página |

En desarrollo se descargaron las solicitudes 3 y 4 junto con la evidencia 16. Se
compararon sus versiones con las informadas por las APIs individuales y se
verificó la integridad del archivo comprimido. Una firma de los datos confirmó
que asignaciones, períodos, archivos registrados, solicitudes, observaciones,
versiones y decisiones se conservaron; se generó el registro de auditoría de la
descarga.

No se requieren migraciones de esquema para este incremento.

## Comprobación manual siguiente

1. Con `jorge` o `MrRey`, abrir `http://localhost:4200/evidencias?periodo=2`.
2. Seleccionar los dos documentos de la asignación 27. Si hace falta, aumentar
   los registros por página para verlos juntos.
3. Añadir una evidencia del flujo anterior, por ejemplo la de la asignación 26.
   Comprobar que el contador incluye los tres elementos.
4. Pulsar **Descargar seleccionadas**, abrir el ZIP y revisar archivos y
   `manifest.csv`. Cada documento debe contener su última versión.
5. Probar **Seleccionar esta página** y quitar la selección, y comprobar que el
   contador vuelve a cero al cambiar de período.

El usuario confirmó «Funciona correctamente, podemos pasar a la siguiente parte».
