import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Usuario } from '../models/user.model';
import { Facultad, Departamento, PerfilUsuario } from '../models/organization.model';
import { Periodo, Criterio, Indicador, Asignacion } from '../models/evaluation.model';
import { Evidencia, AuditoriaEntry, Notificacion } from '../models/evidencia.model';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = 'http://127.0.0.1:8000/api/';

  constructor(private http: HttpClient) {}

  /* Usuarios */
  getUsuarios(): Observable<Usuario[]> {
    return this.http.get<Usuario[]>(`${this.baseUrl}usuarios/`);
  }

  getUsuario(id: number): Observable<Usuario> {
    return this.http.get<Usuario>(`${this.baseUrl}usuarios/${id}/`);
  }

  updateUsuario(id: number, data: any): Observable<Usuario> {
    return this.http.put<Usuario>(`${this.baseUrl}usuarios/${id}/`, data);
  }

  getUsuarioPermisos(id: number): Observable<any> {
    return this.http.get(`${this.baseUrl}usuarios/${id}/permisos/`);
  }

  /* Roles */
  getRoles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}roles/`);
  }

  createRol(data: any): Observable<any> {
    return this.http.post(`${this.baseUrl}roles/`, data);
  }

  updateRol(id: number, data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}roles/${id}/`, data);
  }

  deleteRol(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}roles/${id}/`);
  }

  getPermisos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}permisos/`);
  }

  /* Profile */
  updateProfile(data: any): Observable<any> {
    return this.http.put(`${this.baseUrl}profile/`, data);
  }

  /* Facultades */
  getFacultades(): Observable<Facultad[]> {
    return this.http.get<Facultad[]>(`${this.baseUrl}facultades/`);
  }

  getFacultad(id: number): Observable<Facultad> {
    return this.http.get<Facultad>(`${this.baseUrl}facultades/${id}/`);
  }

  createFacultad(data: Facultad): Observable<Facultad> {
    return this.http.post<Facultad>(`${this.baseUrl}facultades/`, data);
  }

  updateFacultad(id: number, data: Facultad): Observable<Facultad> {
    return this.http.put<Facultad>(`${this.baseUrl}facultades/${id}/`, data);
  }

  deleteFacultad(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}facultades/${id}/`);
  }

  /* Departamentos */
  getDepartamentos(): Observable<Departamento[]> {
    return this.http.get<Departamento[]>(`${this.baseUrl}departamentos/`);
  }

  getDepartamento(id: number): Observable<Departamento> {
    return this.http.get<Departamento>(`${this.baseUrl}departamentos/${id}/`);
  }

  createDepartamento(data: Departamento): Observable<Departamento> {
    return this.http.post<Departamento>(`${this.baseUrl}departamentos/`, data);
  }

  updateDepartamento(id: number, data: Departamento): Observable<Departamento> {
    return this.http.put<Departamento>(`${this.baseUrl}departamentos/${id}/`, data);
  }

  deleteDepartamento(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}departamentos/${id}/`);
  }

  /* Perfiles */
  getPerfiles(params?: { departamento?: number }): Observable<PerfilUsuario[]> {
    let httpParams = new HttpParams();
    if (params?.departamento) httpParams = httpParams.set('departamento', params.departamento);
    return this.http.get<PerfilUsuario[]>(`${this.baseUrl}perfiles/`, { params: httpParams });
  }

  createPerfil(data: PerfilUsuario): Observable<PerfilUsuario> {
    return this.http.post<PerfilUsuario>(`${this.baseUrl}perfiles/`, data);
  }

  /* Periodos */
  getPeriodos(): Observable<Periodo[]> {
    return this.http.get<Periodo[]>(`${this.baseUrl}periodos/`);
  }

  createPeriodo(data: Periodo): Observable<Periodo> {
    return this.http.post<Periodo>(`${this.baseUrl}periodos/`, data);
  }

  updatePeriodo(id: number, data: Periodo): Observable<Periodo> {
    return this.http.put<Periodo>(`${this.baseUrl}periodos/${id}/`, data);
  }

  deletePeriodo(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}periodos/${id}/`);
  }

  /* Criterios */
  getCriterios(): Observable<Criterio[]> {
    return this.http.get<Criterio[]>(`${this.baseUrl}criterios/`);
  }

  createCriterio(data: Criterio): Observable<Criterio> {
    return this.http.post<Criterio>(`${this.baseUrl}criterios/`, data);
  }

  updateCriterio(id: number, data: Criterio): Observable<Criterio> {
    return this.http.put<Criterio>(`${this.baseUrl}criterios/${id}/`, data);
  }

  deleteCriterio(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}criterios/${id}/`);
  }

  /* Indicadores */
  getIndicadores(): Observable<Indicador[]> {
    return this.http.get<Indicador[]>(`${this.baseUrl}indicadores/`);
  }

  createIndicador(data: Indicador): Observable<Indicador> {
    return this.http.post<Indicador>(`${this.baseUrl}indicadores/`, data);
  }

  updateIndicador(id: number, data: Indicador): Observable<Indicador> {
    return this.http.put<Indicador>(`${this.baseUrl}indicadores/${id}/`, data);
  }

  deleteIndicador(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}indicadores/${id}/`);
  }

  /* Asignaciones */
  getAsignaciones(): Observable<Asignacion[]> {
    return this.http.get<Asignacion[]>(`${this.baseUrl}asignaciones/`);
  }

  createAsignacion(data: Asignacion): Observable<Asignacion> {
    return this.http.post<Asignacion>(`${this.baseUrl}asignaciones/`, data);
  }

  updateAsignacion(id: number, data: Asignacion): Observable<Asignacion> {
    return this.http.put<Asignacion>(`${this.baseUrl}asignaciones/${id}/`, data);
  }

  deleteAsignacion(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}asignaciones/${id}/`);
  }

  /* Evidencias */
  getEvidencias(asignacionId?: number): Observable<Evidencia[]> {
    let params = new HttpParams();
    if (asignacionId) params = params.set('asignacion', asignacionId);
    return this.http.get<Evidencia[]>(`${this.baseUrl}evidencias/`, { params });
  }

  createEvidencia(formData: FormData): Observable<Evidencia> {
    return this.http.post<Evidencia>(`${this.baseUrl}evidencias/`, formData);
  }

  deleteEvidencia(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}evidencias/${id}/`);
  }

  descargarEvidencia(id: number): Observable<Blob> {
    return this.http.get(`${this.baseUrl}evidencias/${id}/descargar/`, {
      responseType: 'blob'
    });
  }

  /* Auditoria */
  getAuditoria(): Observable<AuditoriaEntry[]> {
    return this.http.get<AuditoriaEntry[]>(`${this.baseUrl}auditoria/`);
  }

  /* Notificaciones */
  getNotificaciones(): Observable<Notificacion[]> {
    return this.http.get<Notificacion[]>(`${this.baseUrl}notificaciones/`);
  }

  marcarNotificacionLeida(id: number): Observable<any> {
    return this.http.patch(`${this.baseUrl}notificaciones/${id}/leer/`, {});
  }
}
