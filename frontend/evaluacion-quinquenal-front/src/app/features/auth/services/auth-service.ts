import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  baseUrl="http://127.0.0.1:8000/api/";

  constructor(private http:HttpClient) {

  }

  register(user:any):Observable<any> {
    return this.http.post(`${this.baseUrl}register`,user);
  }

  login(user:any):Observable<any> {
    return this.http.post(`${this.baseUrl}login`,user/*, {withCredentials: true}*/);
  }

  // Facultades CRUD operations
  crearFacultades(facultad:any):Observable<any> {
    return this.http.post(`${this.baseUrl}facultades/`, facultad);
  }

  listarFacultades(): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}facultades/`);
  }

  actualizarFacultad(id:any, facultad:any): Observable<any> {
    return this.http.patch(`${this.baseUrl}facultades/${id}/`, facultad);
  }

  eliminarFacultad(id:any): Observable<any> {
    return this.http.delete(`${this.baseUrl}facultades/${id}/`);
  }
}
