import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ReportesService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

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
}