import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { map, switchMap } from 'rxjs/operators';
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

  listarTiposUnidad(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/tipos-unidad-organizacional/`));
  }

  crearTipoUnidad(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/tipos-unidad-organizacional/`, payload);
  }

  actualizarTipoUnidad(id: number, payload: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/tipos-unidad-organizacional/${id}/`, payload);
  }

  eliminarTipoUnidad(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/tipos-unidad-organizacional/${id}/`);
  }

  listarUnidadesOrganizacionales(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/unidades-organizacionales/`));
  }

  crearUnidadOrganizacional(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/unidades-organizacionales/`, payload);
  }

  actualizarUnidadOrganizacional(id: number, payload: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/unidades-organizacionales/${id}/`, payload);
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

  listarAmbitosEvaluacion(usuarioId: number): Observable<any[]> {
    const params = { usuario: String(usuarioId) };
    return this.toList(this.http.get<any>(`${this.apiUrl}/ambitos-evaluacion/`, { params }));
  }

  crearAmbitoEvaluacion(payload: { usuario: number; unidad_organizacional: number; periodo: number }): Observable<any> {
    return this.http.post(`${this.apiUrl}/ambitos-evaluacion/`, payload);
  }

  actualizarAmbitoEvaluacion(id: number, payload: { activo: boolean }): Observable<any> {
    return this.http.patch(`${this.apiUrl}/ambitos-evaluacion/${id}/`, payload);
  }

  listarAmbitosRevision(usuarioId: number, page = 1): Observable<any[]> {
    return this.listarPaginasAmbitos('ambitos-revision', { usuario: String(usuarioId) }, page);
  }

  listarUnidadesParaAmbitos(): Observable<any[]> {
    return this.listarPaginasAmbitos('unidades-organizacionales');
  }

  listarPeriodosParaAmbitos(): Observable<any[]> {
    return this.listarPaginasAmbitos('periodos');
  }

  private listarPaginasAmbitos(recurso: string, params: Record<string, string> = {}, page = 1): Observable<any[]> {
    return this.http.get<any>(`${this.apiUrl}/${recurso}/`, {
      params: { ...params, page: String(page) },
    }).pipe(switchMap(data => {
      if (Array.isArray(data)) return of(data);
      const items = data?.results ?? [];
      return data?.next && items.length
        ? this.listarPaginasAmbitos(recurso, params, page + 1).pipe(map(siguientes => [...items, ...siguientes]))
        : of(items);
    }));
  }

  configuracionAmbitosRevision(): Observable<{ alcance_explicito_activo: boolean }> {
    return this.http.get<{ alcance_explicito_activo: boolean }>(`${this.apiUrl}/ambitos-revision/configuracion/`);
  }

  crearAmbitoRevision(payload: { usuario: number; unidad_organizacional: number; periodo: number }): Observable<any> {
    return this.http.post(`${this.apiUrl}/ambitos-revision/`, payload);
  }

  actualizarAmbitoRevision(id: number, payload: { activo: boolean }): Observable<any> {
    return this.http.patch(`${this.apiUrl}/ambitos-revision/${id}/`, payload);
  }
}
