export interface DestinoDocumentalNotificacion {
  asignacion_id: number;
  periodo_id: number;
  solicitud_id: number | null;
  version_id: number | null;
}

export function destinoNotificacion(notificacion: any): { comandos: (string | number)[]; queryParams: Record<string, number> } | null {
  const destino = notificacion?.destino as DestinoDocumentalNotificacion | null;
  const positivo = (valor: any) => Number.isSafeInteger(valor) && valor > 0;
  if (!destino || !positivo(destino.asignacion_id) || !positivo(destino.periodo_id)) return null;
  const queryParams: Record<string, number> = { periodo: destino.periodo_id };
  if (positivo(destino.solicitud_id)) {
    queryParams['documento'] = destino.solicitud_id!;
    if (positivo(destino.version_id)) queryParams['version_documento'] = destino.version_id!;
  }
  return { comandos: ['/asignaciones', destino.asignacion_id, 'detalle'], queryParams };
}
