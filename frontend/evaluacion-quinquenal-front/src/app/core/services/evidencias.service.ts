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
  listarEvidencias(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/evidencias/`));
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

  obtenerHistorial(id: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/evidencias/${id}/historial/`);
  }

  // Versiones
  descargarVersion(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/versiones/${id}/descargar/`, { responseType: 'blob' });
  }

  previewVersion(id: number): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/versiones/${id}/preview/`, { responseType: 'blob' });
  }

  // Observaciones
  crearObservacion(payload: { version: number; comentario: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/observaciones/`, payload);
  }
}