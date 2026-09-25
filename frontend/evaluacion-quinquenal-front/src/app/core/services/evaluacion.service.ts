import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class EvaluacionService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private toList(obs: Observable<any>): Observable<any[]> {
    return obs.pipe(map((data: any) => (Array.isArray(data) ? data : data?.results ?? [])));
  }

  // Periodos
  listarPeriodos(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/periodos/`));
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
    return this.toList(this.http.get<any>(`${this.apiUrl}/criterios/`));
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

  // Indicadores
  listarIndicadores(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/indicadores/`));
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

  // Asignaciones
  listarAsignaciones(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/asignaciones/`));
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
}