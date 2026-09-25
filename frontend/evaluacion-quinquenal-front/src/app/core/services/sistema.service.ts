import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class SistemaService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private toList(obs: Observable<any>): Observable<any[]> {
    return obs.pipe(map((data: any) => (Array.isArray(data) ? data : data?.results ?? [])));
  }

  buscar(query: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/search/`, { params: { q: query } });
  }

  listarAuditorias(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/auditoria/`));
  }
}