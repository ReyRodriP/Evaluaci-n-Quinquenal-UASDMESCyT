import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { AuthService } from '../../features/auth/services/auth-service';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean | UrlTree | Observable<boolean | UrlTree> {
    const user = this.authService.getUser();
    if (!this.authService.isLoggedIn()) {
      if (!user) return this.router.parseUrl('/auth/login');

      return this.authService.me().pipe(
        map(() => true),
        catchError(() => {
          this.authService.logout();
          return of(this.router.parseUrl('/auth/login'));
        })
      );
    }

    if (user?.is_superuser) {
      return true;
    }
    const hasRole = user?.groups && user.groups.length > 0;
    if (!hasRole) {
      return this.router.parseUrl('/auth/espera');
    }

    return true;
  }
}
