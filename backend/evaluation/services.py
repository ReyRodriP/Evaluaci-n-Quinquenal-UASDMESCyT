from django.utils import timezone

from auditoria.utils import registrar_auditoria

from .models import EstadoAsignacion, Periodo

TRANSICIONES_ESTADO = {
    EstadoAsignacion.PENDIENTE: [EstadoAsignacion.EN_PROGRESO, EstadoAsignacion.OBSERVADA],
    EstadoAsignacion.EN_PROGRESO: [
        EstadoAsignacion.APROBADO,
        EstadoAsignacion.RECHAZADO,
        EstadoAsignacion.OBSERVADA,
    ],
    EstadoAsignacion.OBSERVADA: [EstadoAsignacion.EN_PROGRESO, EstadoAsignacion.RECHAZADO],
    EstadoAsignacion.RECHAZADO: [EstadoAsignacion.EN_PROGRESO],
    EstadoAsignacion.APROBADO: [],
    EstadoAsignacion.COMPLETADO: [],
}


def transicion_valida(estado_actual, estado_nuevo):
    """Indica si la transición de estado de una asignación está permitida."""
    return estado_nuevo in TRANSICIONES_ESTADO.get(estado_actual, [])


def finalizar_periodos_vencidos(fecha=None):
    """Desactiva períodos cuya fecha de fin ya pasó en la zona horaria local."""
    fecha_actual = fecha or timezone.localdate()
    vencidos = Periodo.objects.filter(activo=True, fecha_fin__lt=fecha_actual).only("id", "nombre", "fecha_fin")
    cantidad = 0
    for periodo in vencidos:
        actualizado = Periodo.objects.filter(
            pk=periodo.pk,
            activo=True,
            fecha_fin__lt=fecha_actual,
        ).update(activo=False)
        if actualizado:
            registrar_auditoria(
                usuario=None,
                accion="Finalizar automáticamente",
                modelo="Periodo",
                registro_id=periodo.pk,
                descripcion=(
                    f"El período '{periodo.nombre}' se desactivó al terminar su fecha final "
                    f"({periodo.fecha_fin})."
                ),
            )
            cantidad += actualizado
    return cantidad
