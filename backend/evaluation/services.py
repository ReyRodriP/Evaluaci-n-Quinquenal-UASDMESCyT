from django.utils import timezone
from django.core.exceptions import ValidationError

from auditoria.utils import registrar_auditoria

from .models import EstadoAsignacion, Periodo


def relaciones_indicador(prefijo=""):
    return tuple(prefijo + ruta for ruta in (
        "indicador__criterio",
        "indicador_marco__version_marco",
        "indicador_marco__estandar__criterio_marco__componente__dimension",
    ))


def validar_referencia_marco(indicador, periodo):
    if not periodo.version_marco_id:
        raise ValidationError({"periodo": "Seleccione explícitamente una versión del marco para el período."})
    estandar = indicador.estandar
    criterio = estandar.criterio_marco
    componente = criterio.componente
    dimension = componente.dimension
    if any(nodo.version_marco_id != periodo.version_marco_id for nodo in (indicador, estandar, criterio, componente, dimension)):
        raise ValidationError({"indicador_marco": "El indicador y todos sus ancestros deben pertenecer a la versión del período."})


def validar_encargado(encargado, unidad):
    from organization.models import PerfilUsuario

    if encargado is None:
        raise ValidationError({"encargado": "Seleccione un encargado para la asignación del marco."})
    if not encargado.is_active or not PerfilUsuario.objects.filter(usuario=encargado, unidad_organizacional=unidad).exists():
        raise ValidationError({"encargado": "El encargado debe estar activo y pertenecer a la unidad responsable."})
    permisos = ["evaluation.view_asignacion", "evidence.view_evidencia", "evidence.add_evidencia"]
    if encargado.groups.filter(name="Evaluador Externo").exists() or not encargado.has_perms(permisos):
        raise ValidationError({"encargado": "El encargado debe estar autorizado para consultar y aportar evidencias."})

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
