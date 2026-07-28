import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { AuthService } from '../../features/auth/services/auth-service';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean | UrlTree {
    if (!this.authService.isLoggedIn()) {
      return this.router.parseUrl('/auth/login');
    }

    const user = this.authService.getUser();
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
