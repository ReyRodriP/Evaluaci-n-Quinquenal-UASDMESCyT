import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class NotificacionesService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private toList(obs: Observable<any>): Observable<any[]> {
    return obs.pipe(map((data: any) => (Array.isArray(data) ? data : data?.results ?? [])));
  }

  listarNotificaciones(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/notificaciones/`));
  }

  marcarNotificacionLeida(id: number): Observable<any> {
    return this.http.patch(`${this.apiUrl}/notificaciones/${id}/leer/`, {});
  }

  marcarTodasLeidas(): Observable<any> {
    return this.http.post(`${this.apiUrl}/notificaciones/marcar_todas/`, {});
  }
}