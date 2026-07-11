export interface Periodo {
  id?: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  activo: boolean;
}

export interface Criterio {
  id?: number;
  nombre: string;
  descripcion: string;
  periodo: number;
  periodo_nombre?: string;
  activo: boolean;
}

export interface Indicador {
  id?: number;
  nombre: string;
  descripcion: string;
  criterio: number;
  criterio_nombre?: string;
  obligatorio: boolean;
  activo: boolean;
}

export interface Asignacion {
  id?: number;
  indicador: number;
  indicador_nombre?: string;
  departamento: number;
  departamento_nombre?: string;
  periodo: number;
  periodo_nombre?: string;
  estado: string;
  estado_display?: string;
}
