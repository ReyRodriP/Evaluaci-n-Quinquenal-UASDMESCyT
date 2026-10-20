export interface ResumenVersionMarco {
  id: number;
  nombre: string;
  slug: string;
  activo: boolean;
}

export type NivelCorrespondencia = 'criterio' | 'indicador' | 'dimension' | 'estandar' | 'indicador_marco';

export type EstadoCorrespondencia = 'propuesta' | 'confirmada' | 'rechazada';

export type ProcedenciaCorrespondencia = 'manual' | 'derivada';

export interface NodoCorrespondencia {
  nivel: NivelCorrespondencia;
  id: number;
  texto: string;
}

export interface Correspondencia {
  id: number;
  estado: EstadoCorrespondencia;
  procedencia: ProcedenciaCorrespondencia;
  criterio_op: number | null;
  indicador_op: number | null;
  dimension: number | null;
  estandar: number | null;
  indicador_marco: number | null;
  version_marco: ResumenVersionMarco;
  origen: NodoCorrespondencia | null;
  destino: NodoCorrespondencia | null;
  creado_por: string | null;
  fecha_creacion: string;
  confirmado_por: string | null;
  fecha_confirmacion: string | null;
  rechazado_por: string | null;
  fecha_rechazo: string | null;
  comentario: string;
}

export interface RespuestaPaginada<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ContextoCorrespondencias {
  origen: NodoCorrespondencia;
  correspondencias: Correspondencia[];
}

export interface CorrespondenciaCreacion {
  version_marco: number;
  criterio_op?: number | null;
  indicador_op?: number | null;
  dimension?: number | null;
  estandar?: number | null;
  indicador_marco?: number | null;
  procedencia?: ProcedenciaCorrespondencia;
  comentario?: string;
}

export interface FiltroCorrespondencias {
  estado?: EstadoCorrespondencia;
  version?: string | number;
  criterio_op?: number;
  indicador_op?: number;
  dimension?: number;
  componente?: number;
  estandar?: number;
  indicador_marco?: number;
  page?: number;
}
