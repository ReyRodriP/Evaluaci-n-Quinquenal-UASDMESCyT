import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class EvidenciasService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private toList(obs: Observable<any>): Observable<any[]> {
    return obs.pipe(map((data: any) => (Array.isArray(data) ? data : data?.results ?? [])));
  }

  // Evidencias
  listarEvidencias(periodoId?: number | string | null): Observable<any[]> {
    const params: Record<string, string> = {};
    if (periodoId) params['periodo'] = String(periodoId);
    return this.toList(this.http.get<any>(`${this.apiUrl}/evidencias/`, { params }));
  }

  descargarMasiva(evidenciaIds: number[]): Observable<Blob> {
    return this.http.post(
      `${this.apiUrl}/evidencias/descargas-masivas/`,
      { evidencias: evidenciaIds },
      { responseType: 'blob' }
    );
  }

  crearEvidencia(payload: FormData): Observable<any> {
    return this.http.post(`${this.apiUrl}/evidencias/`, payload);
  }

  actualizarEvidencia(id: number, payload: any, periodoId?: number | string | null): Observable<any> {
    const params: Record<string, string> = {};
    if (periodoId) params['periodo'] = String(periodoId);
    return this.http.patch(`${this.apiUrl}/evidencias/${id}/`, payload, { params });
  }

  eliminarEvidencia(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/evidencias/${id}/`);
  }

  subirVersionEvidencia(id: number, payload: FormData, periodoId?: number | string | null): Observable<any> {
    const params: Record<string, string> = {};
    if (periodoId) params['periodo'] = String(periodoId);
    return this.http.post(`${this.apiUrl}/evidencias/${id}/subir_version/`, payload, { params });
  }

  editarVersionEvidencia(id: number, payload: FormData, periodoId?: number | string | null): Observable<any> {
    const params: Record<string, string> = {};
    if (periodoId) params['periodo'] = String(periodoId);
    return this.http.patch(`${this.apiUrl}/evidencias/${id}/editar_version/`, payload, { params });
  }

  detalleEvidencia(id: number, periodoId?: number | string | null): Observable<any> {
    const params: Record<string, string> = {};
    if (periodoId) params['periodo'] = String(periodoId);
    return this.http.get(`${this.apiUrl}/evidencias/${id}/detalle/`, { params });
  }

  obtenerHistorial(id: number, periodoId?: number | string | null): Observable<any[]> {
    const params: Record<string, string> = {};
    if (periodoId) params['periodo'] = String(periodoId);
    return this.http.get<any[]>(`${this.apiUrl}/evidencias/${id}/historial/`, { params });
  }

  // Versiones
  descargarVersion(id: number, periodoId?: number | string | null): Observable<Blob> {
    const params: Record<string, string> = {};
    if (periodoId) params['periodo'] = String(periodoId);
    return this.http.get(`${this.apiUrl}/versiones/${id}/descargar/`, { params, responseType: 'blob' });
  }

  previewVersion(id: number, periodoId?: number | string | null): Observable<Blob> {
    const params: Record<string, string> = {};
    if (periodoId) params['periodo'] = String(periodoId);
    return this.http.get(`${this.apiUrl}/versiones/${id}/preview/`, { params, responseType: 'blob' });
  }

  // Observaciones
  crearObservacion(payload: { version: number; comentario: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/observaciones/`, payload);
  }
}