import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  baseUrl = environment.apiUrl + '/';
  private readonly userStorageKey = 'auth_user';

  constructor(private http:HttpClient) {

  }

  register(user:any):Observable<any> {
    return this.http.post(`${this.baseUrl}register`,user);
  }

  login(user:any):Observable<any> {
    return this.http.post(`${this.baseUrl}login`,user/*, {withCredentials: true}*/);
  }

  forgotPassword(payload:any): Observable<any> {
    return this.http.post(`${this.baseUrl}forgot_password`, payload);
  }

  resetPassword(payload:any): Observable<any> {
    return this.http.post(`${this.baseUrl}reset_password`, payload);
  }

  logoutApi(): Observable<any> {
    return this.http.post(`${this.baseUrl}logout`, {});
  }

  saveToken(token: string): void {
    document.cookie = `access_token=${token}; path=/; max-age=1800; SameSite=Lax; ${window.location.protocol === 'https:' ? 'Secure;' : ''}`;
  }

  saveUser(user: any): void {
    if (!user) {
      this.removeUser();
      return;
    }
    localStorage.setItem(this.userStorageKey, JSON.stringify(user));
  }

  getUser(): any {
    const storedUser = localStorage.getItem(this.userStorageKey);
    if (!storedUser) {
      return null;
    }

    try {
      return JSON.parse(storedUser);
    } catch {
      return null;
    }
  }

  removeUser(): void {
    localStorage.removeItem(this.userStorageKey);
  }

  getToken(): string | null {
    const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  removeToken(): void {
    document.cookie = 'access_token=; path=/; max-age=0';
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  logout(): void {
    this.removeToken();
    this.removeUser();
  }

  me(): Observable<any> {
    return this.http.get(`${this.baseUrl}me`);
  }

  updateProfile(profile: any): Observable<any> {
    return this.http.patch(`${this.baseUrl}profile`, profile);
  }

  changePassword(payload: any): Observable<any> {
    return this.http.post(`${this.baseUrl}change_password`, payload);
  }

  // Facultades CRUD operations
  crearFacultades(facultad:any):Observable<any> {
    return this.http.post(`${this.baseUrl}facultades/`, facultad);
  }

  listarFacultades(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}facultades/`);
  }

  actualizarFacultad(id:any, facultad:any): Observable<any> {
    return this.http.patch(`${this.baseUrl}facultades/${id}/`, facultad);
  }

  eliminarFacultad(id:any): Observable<any> {
    return this.http.delete(`${this.baseUrl}facultades/${id}/`);
  }

  // Departamentos CRUD operations
  crearDepartamento(departamento:any): Observable<any> {
    return this.http.post(`${this.baseUrl}departamentos/`, departamento);
  }

  listarDepartamentos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}departamentos/`);
  }

  actualizarDepartamento(id:any, departamento:any): Observable<any> {
    return this.http.patch(`${this.baseUrl}departamentos/${id}/`, departamento);
  }

  eliminarDepartamento(id:any): Observable<any> {
    return this.http.delete(`${this.baseUrl}departamentos/${id}/`);
  }

  // Usuarios CRUD operations
  listarUsuarios(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}usuarios/`);
  }

  crearUsuario(usuario:any): Observable<any> {
    return this.http.post(`${this.baseUrl}usuarios/`, usuario);
  }

  actualizarUsuario(id:any, usuario:any): Observable<any> {
    return this.http.patch(`${this.baseUrl}usuarios/${id}/`, usuario);
  }

  eliminarUsuario(id:any): Observable<any> {
    return this.http.delete(`${this.baseUrl}usuarios/${id}/`);
  }

  // Roles CRUD operations
  listarRoles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}roles/`);
  }

  listarPermisos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}permisos/`);
  }

  crearRol(rol:any): Observable<any> {
    return this.http.post(`${this.baseUrl}roles/`, rol);
  }

  actualizarRol(id:any, rol:any): Observable<any> {
    return this.http.patch(`${this.baseUrl}roles/${id}/`, rol);
  }

  // Perfiles CRUD operations
  listarPerfiles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}perfiles/`);
  }

  crearPerfil(perfil:any): Observable<any> {
    return this.http.post(`${this.baseUrl}perfiles/`, perfil);
  }

  actualizarPerfil(id:any, perfil:any): Observable<any> {
    return this.http.patch(`${this.baseUrl}perfiles/${id}/`, perfil);
  }

  // Buscador
  buscar(query: string): Observable<any> {
    return this.http.get(`${this.baseUrl}search/`, { params: { q: query } });
  }

  // Auditoria
  listarAuditorias(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}auditoria/`);
  }

  // Notificaciones
  listarNotificaciones(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}notificaciones/`);
  }

  marcarNotificacionLeida(id: number): Observable<any> {
    return this.http.patch(`${this.baseUrl}notificaciones/${id}/leer/`, {});
  }

  marcarTodasLeidas(): Observable<any> {
    return this.http.post(`${this.baseUrl}notificaciones/marcar_todas/`, {});
  }
}
