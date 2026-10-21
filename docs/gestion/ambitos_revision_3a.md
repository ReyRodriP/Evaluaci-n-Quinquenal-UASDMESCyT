# 3A — Ámbitos explícitos de revisión interna

`AmbitoRevision` autoriza a un Revisor Institucional sobre una unidad raíz y sus
descendientes en un período concreto. No concede el rol ni permisos adicionales.
Los ámbitos externos continúan en `AmbitoEvaluacion` y no autorizan revisión interna.

## Puesta en servicio (pendiente de autorización)

1. Aplicar `organization.0008_ambitorevision` en el entorno autorizado. Es una migración
   de esquema: no crea ámbitos ni modifica usuarios existentes.
2. Sincronizar los permisos de los grupos con el mecanismo existente (`sync_roles`)
   para que Administración General y Coordinación reciban los permisos de gestión del
   nuevo modelo. Los revisores no reciben permisos para concederse ámbitos.
3. Revisar usuarios, unidades raíz y períodos autorizados. Registrar los ámbitos
   aprobados desde Usuarios → Ámbitos de revisión.
4. Configurar `AMBITOS_REVISION_EXPLICITOS=True` y reiniciar los procesos del backend
   (Docker Compose transmite esta variable). Hasta ese momento el valor por defecto
   es `False`: se mantiene el alcance anterior basado en el perfil. Angular informa
   del modo actual mediante `/api/ambitos-revision/configuracion/`.
5. Verificar facultad, centro, descendientes, períodos y descargas con cuentas de cada
   ámbito. Sin ámbitos activos, el modo explícito devuelve cero datos operativos.

Una vez activado, revocar el último ámbito NO restaura el alcance del perfil.
Desactivar el interruptor constituye una reversión del despliegue, no una forma de
revocación: vuelve a habilitar el comportamiento anterior para todos los revisores.

## Contratos y reglas

- `/api/ambitos-revision/`: listado, creación, actualización y desactivación mediante
  DELETE (conserva la fila); auditoría de creación, cambios y revocación.
- Gestión limitada a Administración General/Coordinación con el permiso de modelo
  correspondiente; el evaluador externo no hereda acceso a este endpoint.
- Unicidad por usuario + unidad + período. Para reactivar se actualiza la fila existente.
- Cada filtro mantiene la pareja unidad-período. Los ámbitos solapados no duplican filas.
- El catálogo de criterios/indicadores conserva su política de referencia institucional;
  su lectura no autoriza acceso a las entregas.
- Métricas cacheadas: la clave incluye la firma de los ámbitos activos y sus unidades
  descendientes para no reutilizar resultados previos a una revocación o cambio de alcance.
- Se mantiene la precedencia existente: superusuario y roles globales no se restringen;
  el rol externo conserva sus reglas si se combina con un rol interno restringido.

## Verificación

Las regresiones específicas están en `backend/organization/test_ambitos_revision.py`.
Verifican modo explícito y transición desactivada; deben ejecutarse con PostgreSQL en
una base de pruebas separada, nunca sustituyendo la base de desarrollo.

Los estados y las aprobaciones actuales no se redefinen en 3A. La revisión por
documento y el cierre global del diseño objetivo corresponden a incrementos posteriores.

### Resultado de la implementación (20/10/2026)

| Verificación | Resultado |
|---|---|
| Backend, 13 aplicaciones, PostgreSQL aislado | 419 pruebas satisfactorias, incluidas 26 de ámbitos internos y las existentes de concurrencia |
| Frontend, Edge headless mediante ChromeHeadless | 241 pruebas satisfactorias, incluidas 10 nuevas de gestión y servicio de ámbitos |
| Angular `npm run build` | Satisfactorio |
| `makemigrations --check --dry-run` | Sin cambios pendientes respecto de los modelos |
| Ruff sobre la migración y el nuevo archivo de pruebas | Satisfactorio |

La suite PostgreSQL creó y destruyó una base temporal con nombre único. Una primera
ejecución completa alcanzó el timeout de cuatro minutos; se repitió con tiempo
suficiente y se retiró la base temporal inactiva que dejó la interrupción.
No se aplicó la migración sobre desarrollo ni se configuraron revisores existentes.
