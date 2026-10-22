import { RutaMarcoAsignacion } from './asignacion-marco.model';

export const MAX_PAGINAS_LISTADO = 20;
export const MAX_PAGINAS_CORRESPONDENCIAS = 10;

export type ClaveRevision =
  | 'sin_evidencia'
  | 'cancelada'
  | 'en_revision'
  | 'observada'
  | 'aprobada'
  | 'rechazada'
  | 'sin_enviar'
  | 'completada';

export type EstadoCorrespondenciaFila = 'confirmada' | 'pendiente' | 'sin' | 'desconocida' | 'directa';

export interface FilaSeguimiento {
  asignacionId: number;
  periodoNombre: string;
  unidadId: number | string;
  unidadNombre: string;
  indicadorId: number | string;
  indicadorNombre: string;
  criterioId: number | null;
  criterioNombre: string;
  estado: string;
  estadoDisplay: string;
  evidenciaId: number | null;
  claveRevision: ClaveRevision;
  estadoRevision: string;
  correspondenciaEstado: EstadoCorrespondenciaFila;
  codigoDestino: string;
  versionMarco: string;
  tipoOrigen?: 'operativo' | 'marco';
  indicadorMarcoId?: number;
  rutaMarco?: RutaMarcoAsignacion;
  documentosResumen?: { solicitados: number; entregados: number; aprobados: number; observados: number };
}

export interface Metricas {
  total: number;
  conEvidencia: number;
  sinEvidencia: number;
  pendientesRevision: number;
  observadas: number;
  conConfirmada: number | null;
  sinConfirmada: number | null;
  conAsignacionDirecta?: number;
}

export interface ResultadoPaginas<T> {
  items: T[];
  total: number;
  truncado: boolean;
}

export interface ResultadoSeguimiento {
  filas: FilaSeguimiento[];
  metricas: Metricas;
  avisosTruncado: string[];
  avisoCorrespondenciaTruncada: boolean;
  correspondenciasDisponibles: boolean;
}

export const ETIQUETAS_REVISION: Record<ClaveRevision, string> = {
  sin_evidencia: 'Sin evidencia',
  cancelada: 'Evidencia cancelada',
  en_revision: 'Pendiente de revisión',
  observada: 'Observada',
  aprobada: 'Aprobada internamente',
  rechazada: 'Rechazada',
  sin_enviar: 'Sin enviar a revisión',
  completada: 'Completada',
};

export const ETIQUETAS_CORRESPONDENCIA: Record<EstadoCorrespondenciaFila, string> = {
  confirmada: 'Confirmada',
  pendiente: 'Pendiente de validación',
  sin: 'Sin correspondencia confirmada',
  desconocida: 'No disponible',
  directa: 'Asignación directa al marco',
};

export function calcularMetricas(filas: FilaSeguimiento[], correspondenciasDisponibles: boolean): Metricas {
  const total = filas.length;
  const conEvidencia = filas.filter((fila) => fila.evidenciaId != null || (fila.documentosResumen?.entregados ?? 0) > 0).length;
  const pendientesRevision = filas.filter((fila) => fila.claveRevision === 'en_revision').length;
  const observadas = filas.filter((fila) => fila.claveRevision === 'observada').length;
  const directas = filas.filter(fila => fila.tipoOrigen === 'marco').length;
  const metricasDirectas = directas ? { conAsignacionDirecta: directas } : {};
  if (!correspondenciasDisponibles) {
    return {
      total,
      conEvidencia,
      sinEvidencia: total - conEvidencia,
      pendientesRevision,
      observadas,
      conConfirmada: null,
      sinConfirmada: null,
      ...metricasDirectas,
    };
  }
  const conConfirmada = filas.filter((fila) => fila.correspondenciaEstado === 'confirmada').length;
  return {
    total,
    conEvidencia,
    sinEvidencia: total - conEvidencia,
    pendientesRevision,
    observadas,
    conConfirmada,
    sinConfirmada: total - conConfirmada - directas,
    ...metricasDirectas,
  };
}
