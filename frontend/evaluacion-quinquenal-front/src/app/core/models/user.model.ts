export interface Usuario {
  id?: number;
  username: string;
  email: string;
  password?: string;
  first_name: string;
  last_name: string;
  telefono: string;
  is_active: boolean;
  rol: string;
  groups: number[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: Usuario;
}

export interface Grupo {
  id: number;
  name: string;
  permissions: number[];
}

export interface Permiso {
  id: number;
  name: string;
  codename: string;
}
