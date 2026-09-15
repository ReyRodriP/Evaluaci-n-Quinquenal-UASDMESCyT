import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, filter, switchMap, take } from 'rxjs/operators';
import { AuthService } from '../../features/auth/services/auth-service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private isRefreshing = false;
  private refreshTokenSubject: BehaviorSubject<string | null> = new BehaviorSubject<string | null>(null);

  constructor(private authService: AuthService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = this.authService.getToken();

    if (token) {
      req = req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      });
    }

    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status !== 401 || !token || req.url.includes('/token/')) {
          return throwError(() => error);
        }

        return this.handle401Error(req, next);
      }),
    );
  }

  private handle401Error(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (!this.isRefreshing) {
      this.isRefreshing = true;
      this.refreshTokenSubject.next(null);

      const refreshToken = this.authService.getRefreshToken();

      if (!refreshToken) {
        this.isRefreshing = false;
        this.authService.logout();
        return throwError(() => new Error('Sesion expirada'));
      }

      return this.authService.refreshAccessToken(refreshToken).pipe(
        switchMap((data: any) => {
          this.isRefreshing = false;
          const newToken = data?.access ?? data?.token;
          if (newToken) {
            this.authService.saveToken(newToken);
            if (data?.refresh) {
              this.authService.saveRefreshToken(data.refresh);
            }
          }
          this.refreshTokenSubject.next(newToken);
          return next.handle(
            request.clone({
              setHeaders: {
                Authorization: `Bearer ${newToken}`,
              },
            }),
          );
        }),
        catchError((err) => {
          this.isRefreshing = false;
          this.authService.logout();
          return throwError(() => err);
        }),
      );
    }

    return this.refreshTokenSubject.pipe(
      filter((token) => token !== null),
      take(1),
      switchMap((token) =>
        next.handle(
          request.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`,
            },
          }),
        ),
      ),
    );
  }
}