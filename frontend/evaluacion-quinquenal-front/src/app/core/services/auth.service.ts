import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Periodos
  listarPeriodos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/periodos/`);
  }

  crearPeriodo(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/periodos/`, payload);
  }

  actualizarPeriodo(id: number, payload: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/periodos/${id}/`, payload);
  }

  eliminarPeriodo(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/periodos/${id}/`);
  }

  patchPeriodo(id: number, payload: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/periodos/${id}/`, payload);
  }

  // Criterios
  listarCriterios(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/criterios/`);
  }

  crearCriterio(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/criterios/`, payload);
  }

  actualizarCriterio(id: number, payload: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/criterios/${id}/`, payload);
  }

  patchCriterio(id: number, payload: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/criterios/${id}/`, payload);
  }

  eliminarCriterio(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/criterios/${id}/`);
  }

  // Asignaciones
  listarAsignaciones(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/asignaciones/`);
  }

  crearAsignacion(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/asignaciones/`, payload);
  }

  actualizarAsignacion(id: number, payload: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/asignaciones/${id}/`, payload);
  }

  patchAsignacion(id: number, payload: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/asignaciones/${id}/`, payload);
  }

  eliminarAsignacion(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/asignaciones/${id}/`);
  }

  aprobarAsignacion(id: number, comentario?: string): Observable<any> {
    const payload: any = {};
    if (comentario) payload.comentario = comentario;
    return this.http.post(`${this.apiUrl}/asignaciones/${id}/aprobar/`, payload);
  }

  rechazarAsignacion(id: number, comentario?: string): Observable<any> {
    const payload: any = {};
    if (comentario) payload.comentario = comentario;
    return this.http.post(`${this.apiUrl}/asignaciones/${id}/rechazar/`, payload);
  }

  enviarARevision(id: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/asignaciones/${id}/en_revision/`, {});
  }

  solicitarCambios(id: number, comentario?: string): Observable<any> {
    const payload: any = {};
    if (comentario) payload.comentario = comentario;
    return this.http.post(`${this.apiUrl}/asignaciones/${id}/observada/`, payload);
  }

  resumenAsignacion(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/asignaciones/${id}/resumen/`);
  }

  // Evidencias
  listarEvidencias(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/evidencias/`);
  }

  crearEvidencia(payload: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}/evidencias/`, payload);
  }

  actualizarEvidencia(id: number, payload: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/evidencias/${id}/`, payload);
  }

  eliminarEvidencia(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/evidencias/${id}/`);
  }

  subirVersionEvidencia(id: number, payload: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}/evidencias/${id}/subir_version/`, payload);
  }

  editarVersionEvidencia(id: number, payload: FormData): Observable<any> {
    return this.http.patch(`${this.apiUrl}/evidencias/${id}/editar_version/`, payload);
  }

  detalleEvidencia(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/evidencias/${id}/detalle/`);
  }

  crearObservacion(payload: { version: number; comentario: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/observaciones/`, payload);
  }

  descargarVersion(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/versiones/${id}/descargar/`, { responseType: 'blob' });
  }

  previewVersion(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/versiones/${id}/preview/`, { responseType: 'blob' });
  }

  obtenerHistorial(id: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/evidencias/${id}/historial/`);
  }

  // Indicadores
  listarIndicadores(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/indicadores/`);
  }

  crearIndicador(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/indicadores/`, payload);
  }

  actualizarIndicador(id: number, payload: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/indicadores/${id}/`, payload);
  }

  patchIndicador(id: number, payload: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/indicadores/${id}/`, payload);
  }

  eliminarIndicador(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/indicadores/${id}/`);
  }

  // Departamentos
  listarDepartamentos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/departamentos/`);
  }

  crearDepartamento(payload: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/departamentos/`, payload);
  }

  actualizarDepartamento(id: number, payload: any): Observable<any> {
    return this.http.put(`${this.apiUrl}/departamentos/${id}/`, payload);
  }

  eliminarDepartamento(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/departamentos/${id}/`);
  }

  // Facultades
  listarFacultades(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/facultades/`);
  }

  // Usuarios
  listarUsuarios(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/usuarios/`);
  }

  // Roles
  listarRoles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/roles/`);
  }

  // Reportes
  reporteGeneral(params: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/reportes/general/`, { params });
  }

  reporteFacultad(id: number, params: any = {}): Observable<any> {
    return this.http.get(`${this.apiUrl}/reportes/facultad/${id}/`, { params });
  }

  reporteDepartamento(id: number, params: any = {}): Observable<any> {
    return this.http.get(`${this.apiUrl}/reportes/departamento/${id}/`, { params });
  }

  reporteEvidencias(params: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/reportes/evidencias/`, { params });
  }

  reporteObservaciones(params: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/reportes/observaciones/`, { params });
  }

  reporteAuditoria(params: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/reportes/auditoria/`, { params });
  }

  reporteUsuarios(params: any): Observable<any> {
    return this.http.get(`${this.apiUrl}/reportes/usuarios/`, { params });
  }

  exportarReporte(reporte: string, formato: string, params: any): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/reportes/${reporte}/exportar/`, {
      params: { ...params, formato },
      responseType: 'blob',
    });
  }

  // Dashboard
  obtenerResumen(): Observable<any> {
    return this.http.get(`${this.apiUrl}/dashboard/resumen/`);
  }

  obtenerAvance(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/dashboard/avance/`);
  }

  obtenerDashboardDepartamento(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/dashboard/departamento/${id}/`);
  }

  obtenerDashboardPeriodo(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/dashboard/periodo/${id}/`);
  }
}
