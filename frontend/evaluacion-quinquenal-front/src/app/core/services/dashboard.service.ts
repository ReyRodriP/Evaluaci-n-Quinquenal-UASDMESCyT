import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  obtenerResumen(filtros: Record<string, string> = {}): Observable<any> {
    const params = { ...filtros };
    return this.http.get(`${this.apiUrl}/dashboard/resumen/`, { params });
  }

  obtenerAvance(filtros: Record<string, string> = {}, agrupar = ''): Observable<any[]> {
    const params = { ...filtros };
    if (agrupar) params['agrupar'] = agrupar;
    return this.http.get<any[]>(`${this.apiUrl}/dashboard/avance/`, { params });
  }

  obtenerPendientes(filtros: Record<string, string> = {}): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/dashboard/pendientes/`, { params: { ...filtros } });
  }

  obtenerDashboardDepartamento(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/dashboard/departamento/${id}/`);
  }

  obtenerDashboardPeriodo(id: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/dashboard/periodo/${id}/`);
  }
}