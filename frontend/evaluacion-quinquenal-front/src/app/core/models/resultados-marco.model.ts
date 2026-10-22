export interface ResumenResultadosMarco {
  asignaciones: number;
  con_archivos: number;
  aprobadas_globalmente: number;
  pendientes_cierre: number;
  documentos_solicitados: number;
  documentos_entregados: number;
  documentos_aprobados: number;
  documentos_en_revision: number;
  documentos_observados: number;
  aprobacion_global_porcentaje: number;
}

export interface OpcionDimensionMarco { id: number; codigo: string; nombre: string; orden: number; }
export interface OpcionEstandarMarco { id: number; codigo: string; nombre: string; dimension_id: number; }

export interface GrupoResultadosMarco extends ResumenResultadosMarco {
  version: { id: number; nombre: string };
  dimension: OpcionDimensionMarco;
  estandar: OpcionEstandarMarco | null;
}

export interface ReporteResultadosMarco {
  periodo: { id: number; nombre: string } | null;
  version_periodo: { id: number; nombre: string } | null;
  agrupar: 'dimension' | 'estandar';
  resumen: ResumenResultadosMarco;
  rows: GrupoResultadosMarco[];
  opciones: { dimensiones: OpcionDimensionMarco[]; estandares: OpcionEstandarMarco[] };
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
