import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ContextoCorrespondencias,
  Correspondencia,
  CorrespondenciaCreacion,
  FiltroCorrespondencias,
  RespuestaPaginada,
} from '../models/vinculacion.model';

@Injectable({
  providedIn: 'root',
})
export class VinculacionService {
  private apiUrl = environment.apiUrl;
  private base = `${this.apiUrl}/vinculacion/correspondencias`;

  constructor(private http: HttpClient) {}

  listarCorrespondencias(filtro: FiltroCorrespondencias = {}): Observable<RespuestaPaginada<Correspondencia>> {
    let params = new HttpParams();
    if (filtro.estado) params = params.set('estado', filtro.estado);
    if (filtro.version !== undefined && filtro.version !== null) params = params.set('version', String(filtro.version));
    if (filtro.criterio_op != null) params = params.set('criterio_op', String(filtro.criterio_op));
    if (filtro.indicador_op != null) params = params.set('indicador_op', String(filtro.indicador_op));
    if (filtro.page != null) params = params.set('page', String(filtro.page));
    return this.http.get<RespuestaPaginada<Correspondencia>>(`${this.base}/`, { params });
  }

  obtenerCorrespondencia(id: number): Observable<Correspondencia> {
    return this.http.get<Correspondencia>(`${this.base}/${id}/`);
  }

  contextoCriterio(criterioId: number): Observable<ContextoCorrespondencias> {
    return this.http.get<ContextoCorrespondencias>(`${this.apiUrl}/vinculacion/contexto/criterio/${criterioId}/`);
  }

  contextoIndicador(indicadorId: number): Observable<ContextoCorrespondencias> {
    return this.http.get<ContextoCorrespondencias>(`${this.apiUrl}/vinculacion/contexto/indicador/${indicadorId}/`);
  }

  crearCorrespondencia(payload: CorrespondenciaCreacion): Observable<Correspondencia> {
    return this.http.post<Correspondencia>(`${this.base}/`, payload);
  }

  confirmarCorrespondencia(id: number, comentario = ''): Observable<Correspondencia> {
    return this.http.post<Correspondencia>(`${this.base}/${id}/confirmar/`, { comentario });
  }

  rechazarCorrespondencia(id: number, comentario: string): Observable<Correspondencia> {
    return this.http.post<Correspondencia>(`${this.base}/${id}/rechazar/`, { comentario });
  }

  desconfirmarCorrespondencia(id: number, comentario: string): Observable<Correspondencia> {
    return this.http.post<Correspondencia>(`${this.base}/${id}/desconfirmar/`, { comentario });
  }
}
