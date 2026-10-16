"""Validaciones centralizadas de la app de vinculación.

La coherencia entre la versión del marco registrada en una correspondencia y la
versión real del nodo de destino no puede imponerse con un CheckConstraint
(supone comparar el atributo de otra tabla). Se garantiza en la aplicación
mediante esta función reutilizable, invocada desde Correspondencia.clean() y
desde los servicios de dominio; las pruebas cubren ambos caminos.
"""

from django.core.exceptions import ValidationError


def validar_destino_en_version(version_marco, *, dimension=None, estandar=None, indicador_marco=None):
    """Comprueba que el destino del marco pertenece a la versión indicada.

    @param version_marco: instancia de VersionMarcoEvaluacion o su pk.
    @param dimension/estandar/indicador_marco: nodo destino (a lo sumo uno).
    @return: el nodo destino recibido.
    @raise ValidationError: si no hay destino, hay más de uno, o el destino
    no pertenece a version_marco.
    """
    version_id = getattr(version_marco, "pk", version_marco)
    destinos = [d for d in (dimension, estandar, indicador_marco) if d is not None]
    if len(destinos) != 1:
        raise ValidationError("Debe indicarse exactamente un destino del marco (dimensión, estándar o indicador).")
    destino = destinos[0]
    if destino.version_marco_id != version_id:
        raise ValidationError(
            "El destino seleccionado no pertenece a la versión del marco declarada en la correspondencia."
        )
    return destino
