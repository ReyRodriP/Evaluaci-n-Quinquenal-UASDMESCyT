export interface Evidencia {
  id?: number;
  asignacion: number;
  asignacion_indicador?: string;
  asignacion_departamento?: string;
  asignacion_periodo?: string;
  archivo: File | string;
  nombre: string;
  descripcion: string;
  tipo_archivo?: string;
  tamano?: number;
  subido_por?: number;
  subido_por_username?: string;
  fecha_subida?: string;
  version?: number;
  observaciones: string;
}

export interface AuditoriaEntry {
  id: number;
  usuario: number | null;
  usuario_nombre?: string;
  accion: string;
  modelo: string;
  registro_id: number | null;
  descripcion: string;
  fecha: string;
}

export interface Notificacion {
  id: number;
  usuario: number;
  titulo: string;
  mensaje: string;
  leida: boolean;
  fecha_creacion: string;
}
