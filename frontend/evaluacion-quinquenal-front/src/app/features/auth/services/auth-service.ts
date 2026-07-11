import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { LoginRequest, LoginResponse, Usuario } from '../../../core/models/user.model';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
<<<<<<< HEAD
  baseUrl="http://127.0.0.1:8000/api/";
  private readonly userStorageKey = 'auth_user';
=======
  baseUrl = 'http://127.0.0.1:8000/api/';
>>>>>>> Ramon_Paulino_Gil_100345706

  constructor(private http: HttpClient) {}

  login(user: LoginRequest): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}login`, user).pipe(
      tap((res) => {
        localStorage.setItem('auth_token', res.token);
        localStorage.setItem('user_data', JSON.stringify(res.user));
      })
    );
  }

  register(user: any): Observable<any> {
    return this.http.post(`${this.baseUrl}register`, user);
  }

  logout(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  getCurrentUser(): Usuario | null {
    const data = localStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  me(): Observable<Usuario> {
    return this.http.get<Usuario>(`${this.baseUrl}me`);
  }

  changePassword(data: { old_password: string; new_password: string }): Observable<any> {
    return this.http.post(`${this.baseUrl}change_password`, data);
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

  saveToken(token:string): void {
    localStorage.setItem('auth_token', token);
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
    return localStorage.getItem('auth_token');
  }

  removeToken(): void {
    localStorage.removeItem('auth_token');
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
}
