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

    let authReq = req.clone({ withCredentials: true });

    if (token) {
      authReq = authReq.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      });
    }

    return next.handle(authReq).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status !== 401 || !token || req.url.includes('/token/')) {
          return throwError(() => error);
        }

        return this.handle401Error(authReq, next);
      }),
    );
  }

  private handle401Error(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (!this.isRefreshing) {
      this.isRefreshing = true;
      this.refreshTokenSubject.next(null);

      return this.authService.refreshViaCookie().pipe(
        switchMap((data: any) => {
          this.isRefreshing = false;
          const newToken = data?.access ?? data?.token;

          if (!newToken) {
            this.authService.logout();
            return throwError(() => new Error('Sesion expirada'));
          }

          this.authService.saveToken(newToken);
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
          window.location.assign('/login');
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