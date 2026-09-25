import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  baseUrl = environment.apiUrl + '/';
  private readonly userStorageKey = 'auth_user';

  constructor(private http:HttpClient) {

  }

  register(user:any):Observable<any> {
    return this.http.post(`${this.baseUrl}register`,user);
  }

  login(user:any):Observable<any> {
    return this.http.post(`${this.baseUrl}login`, user, { withCredentials: true });
  }

  refreshViaCookie(): Observable<any> {
    return this.http.post(`${this.baseUrl}token/refresh/cookie`, {}, { withCredentials: true });
  }

  refreshAccessToken(refresh: string): Observable<any> {
    return this.http.post(`${this.baseUrl}token/refresh/`, { refresh });
  }

  forgotPassword(payload:any): Observable<any> {
    return this.http.post(`${this.baseUrl}forgot_password`, payload);
  }

  resetPassword(payload:any): Observable<any> {
    return this.http.post(`${this.baseUrl}reset_password`, payload);
  }

  logoutApi(): Observable<any> {
    return this.http.post(`${this.baseUrl}logout`, {}, { withCredentials: true });
  }

  saveToken(token: string): void {
    document.cookie = `access_token=${token}; path=/; max-age=1800; SameSite=Lax; ${window.location.protocol === 'https:' ? 'Secure;' : ''}`;
  }

  saveRefreshToken(token: string): void {
    document.cookie = `refresh_token=${token}; path=/; max-age=604800; SameSite=Lax; ${window.location.protocol === 'https:' ? 'Secure;' : ''}`;
  }

  getRefreshToken(): string | null {
    const match = document.cookie.match(/(?:^|;\s*)refresh_token=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  removeRefreshToken(): void {
    document.cookie = 'refresh_token=; path=/; max-age=0';
  }

  saveUser(user: any): void {
    if (!user) {
      this.removeUser();
      return;
    }
    localStorage.setItem(this.userStorageKey, JSON.stringify(user));
  }

  getUser(): any {
    const storedUser = localStorage.getItem(this.userStorageKey);
    if (!storedUser) {
      return null;
    }

    try {
      return JSON.parse(storedUser);
    } catch {
      return null;
    }
  }

  removeUser(): void {
    localStorage.removeItem(this.userStorageKey);
  }

  getToken(): string | null {
    const match = document.cookie.match(/(?:^|;\s*)access_token=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  removeToken(): void {
    document.cookie = 'access_token=; path=/; max-age=0';
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  logout(): void {
    this.removeToken();
    this.removeRefreshToken();
    this.removeUser();
  }

  me(): Observable<any> {
    return this.http.get(`${this.baseUrl}me`);
  }

  updateProfile(profile: any): Observable<any> {
    return this.http.patch(`${this.baseUrl}profile`, profile);
  }

  changePassword(payload: any): Observable<any> {
    return this.http.post(`${this.baseUrl}change_password`, payload);
  }
}
