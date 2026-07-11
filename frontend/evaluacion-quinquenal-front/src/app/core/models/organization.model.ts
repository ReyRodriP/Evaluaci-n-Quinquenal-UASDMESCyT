export interface Facultad {
  id?: number;
  nombre: string;
  descripcion: string;
  activo: boolean;
  fecha_creacion?: string;
}

export interface Departamento {
  id?: number;
  nombre: string;
  descripcion: string;
  facultad: number;
  facultad_nombre?: string;
  activo: boolean;
  fecha_creacion?: string;
}

export interface PerfilUsuario {
  id?: number;
  usuario: number;
  usuario_nombre?: string;
  departamento: number | null;
  departamento_nombre?: string;
}
