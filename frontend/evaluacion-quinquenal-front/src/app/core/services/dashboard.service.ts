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