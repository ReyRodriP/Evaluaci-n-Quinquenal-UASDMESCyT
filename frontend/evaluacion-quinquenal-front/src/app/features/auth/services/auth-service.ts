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
}
