import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  baseUrl="http://127.0.0.1:8000/api/";

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

  saveToken(token:string): void {
    localStorage.setItem('auth_token', token);
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
