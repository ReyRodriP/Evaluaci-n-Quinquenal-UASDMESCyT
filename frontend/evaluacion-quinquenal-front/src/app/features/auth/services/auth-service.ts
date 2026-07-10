import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { LoginRequest, LoginResponse, Usuario } from '../../../core/models/user.model';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  baseUrl = 'http://127.0.0.1:8000/api/';

  constructor(private http: HttpClient) {}

  login(user: LoginRequest): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}login`, user).pipe(
      tap((res) => {
        localStorage.setItem('auth_token', res.token);
        localStorage.setItem('user_data', JSON.stringify(res.user));
      })
    );
  }

  register(user: any): Observable<any> {
    return this.http.post(`${this.baseUrl}register`, user);
  }

  logout(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
  }

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  getCurrentUser(): Usuario | null {
    const data = localStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  me(): Observable<Usuario> {
    return this.http.get<Usuario>(`${this.baseUrl}me`);
  }

  changePassword(data: { old_password: string; new_password: string }): Observable<any> {
    return this.http.post(`${this.baseUrl}change_password`, data);
  }
}
