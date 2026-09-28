import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class OrganizacionService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private toList(obs: Observable<any>): Observable<any[]> {
    return obs.pipe(map((data: any) => (Array.isArray(data) ? data : data?.results ?? [])));
  }

  // Facultades
  crearFacultades(facultad: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/facultades/`, facultad);
  }

  listarFacultades(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/facultades/`));
  }

  actualizarFacultad(id: any, facultad: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/facultades/${id}/`, facultad);
  }

  eliminarFacultad(id: any): Observable<any> {
    return this.http.delete(`${this.apiUrl}/facultades/${id}/`);
  }

  // Departamentos
  crearDepartamento(departamento: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/departamentos/`, departamento);
  }

  listarDepartamentos(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/departamentos/`));
  }

  actualizarDepartamento(id: any, departamento: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/departamentos/${id}/`, departamento);
  }

  eliminarDepartamento(id: any): Observable<any> {
    return this.http.delete(`${this.apiUrl}/departamentos/${id}/`);
  }

  // Usuarios
  listarUsuarios(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/usuarios/`));
  }

  crearUsuario(usuario: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/usuarios/`, usuario);
  }

  actualizarUsuario(id: any, usuario: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/usuarios/${id}/`, usuario);
  }

  eliminarUsuario(id: any): Observable<any> {
    return this.http.delete(`${this.apiUrl}/usuarios/${id}/`);
  }

  // Roles y permisos
  listarRoles(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/roles/`));
  }

  listarPermisos(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/permisos/`));
  }

  crearRol(rol: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/roles/`, rol);
  }

  actualizarRol(id: any, rol: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/roles/${id}/`, rol);
  }

  // Perfiles
  listarPerfiles(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/perfiles/`));
  }

  crearPerfil(perfil: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/perfiles/`, perfil);
  }

  actualizarPerfil(id: any, perfil: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/perfiles/${id}/`, perfil);
  }
}