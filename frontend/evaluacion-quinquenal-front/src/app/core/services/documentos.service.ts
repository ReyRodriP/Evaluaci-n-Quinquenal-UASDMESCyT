import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { EMPTY, Observable } from 'rxjs';
import { expand, reduce } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class DocumentosService {
  private url = `${environment.apiUrl}/solicitudes-documentales`;
  constructor(private http: HttpClient) {}

  contexto(asignacion: number): Observable<any> {
    return this.http.get(`${this.url}/contexto/`, { params: { asignacion } });
  }

  listar(asignacion: number): Observable<any[]> {
    return this.http.get<any>(`${this.url}/`, { params: { asignacion } }).pipe(
      expand((pagina) => pagina.next ? this.http.get<any>(pagina.next) : EMPTY),
      reduce((todos: any[], pagina: any) => todos.concat(Array.isArray(pagina) ? pagina : pagina.results ?? []), [])
    );
  }

  crear(asignacion: number, titulo: string, descripcion: string): Observable<any> {
    return this.http.post(`${this.url}/`, { asignacion, titulo, descripcion });
  }

  editar(id: number, titulo: string, descripcion: string): Observable<any> {
    return this.http.patch(`${this.url}/${id}/`, { titulo, descripcion });
  }

  eliminar(id: number): Observable<any> { return this.http.delete(`${this.url}/${id}/`); }

  subir(id: number, archivo: File, comentario: string): Observable<any> {
    const data = new FormData();
    data.append('archivo', archivo);
    data.append('comentario', comentario);
    return this.http.post(`${this.url}/${id}/subir_version/`, data);
  }

  accion(id: number, accion: string, version_id?: number, comentario = ''): Observable<any> {
    return this.http.post(`${this.url}/${id}/${accion}/`, { version_id, comentario });
  }

  aprobarGlobal(asignacion: number): Observable<any> {
    return this.http.post(`${environment.apiUrl}/asignaciones/${asignacion}/aprobar/`, {});
  }

  descargar(id: number, version: number): Observable<Blob> {
    return this.http.get(`${this.url}/${id}/descargar/`, { params: { version }, responseType: 'blob' });
  }
}
