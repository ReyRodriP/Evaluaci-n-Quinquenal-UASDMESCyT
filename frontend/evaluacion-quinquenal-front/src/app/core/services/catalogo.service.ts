import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class CatalogoService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private toList(obs: Observable<any>): Observable<any[]> {
    return obs.pipe(map((data: any) => (Array.isArray(data) ? data : data?.results ?? [])));
  }

  listarVersiones(): Observable<any[]> {
    return this.toList(this.http.get<any>(`${this.apiUrl}/catalogo/versiones/`));
  }

  listarDimensiones(versionSlug: string): Observable<any[]> {
    return this.toList(
      this.http.get<any>(`${this.apiUrl}/catalogo/dimensiones/`, {
        params: { version: versionSlug },
      })
    );
  }

  listarComponentes(dimensionId: number): Observable<any[]> {
    return this.toList(
      this.http.get<any>(`${this.apiUrl}/catalogo/componentes/`, {
        params: { dimension: String(dimensionId) },
      })
    );
  }

  listarCriterios(componenteId: number): Observable<any[]> {
    return this.toList(
      this.http.get<any>(`${this.apiUrl}/catalogo/criterios/`, {
        params: { componente: String(componenteId) },
      })
    );
  }

  listarEstandares(criterioId: number): Observable<any[]> {
    return this.toList(
      this.http.get<any>(`${this.apiUrl}/catalogo/estandares/`, {
        params: { criterio: String(criterioId) },
      })
    );
  }

  listarIndicadores(estandarId: number): Observable<any[]> {
    return this.toList(
      this.http.get<any>(`${this.apiUrl}/catalogo/indicadores/`, {
        params: { estandar: String(estandarId) },
      })
    );
  }

  exportarCsv(versionSlug: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/catalogo/exportar/`, {
      params: { version: versionSlug },
      responseType: 'blob',
    });
  }
}
