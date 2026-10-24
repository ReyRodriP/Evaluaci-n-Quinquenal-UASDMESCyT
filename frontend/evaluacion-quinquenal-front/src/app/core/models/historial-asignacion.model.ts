export interface RegistroHistorialAsignacion {
  id: number;
  asignacion: number;
  estado_anterior: string | null;
  estado_anterior_display: string | null;
  estado_nuevo: string;
  estado_nuevo_display: string;
  usuario: number | null;
  usuario_nombre: string;
  usuario_identificador: string | null;
  comentario: string | null;
  fecha: string;
}

export interface PaginaHistorialAsignacion {
  count: number;
  next: string | null;
  previous: string | null;
  results: RegistroHistorialAsignacion[];
  page: number;
  page_size: number;
}
