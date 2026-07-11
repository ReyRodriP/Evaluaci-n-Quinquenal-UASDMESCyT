<<<<<<< HEAD
import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { AuthService } from '../../features/auth/services/auth-service';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean | UrlTree {
    if (this.authService.isLoggedIn()) {
      return true;
    }

    return this.router.parseUrl('/auth/login');
  }
}
=======
import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const token = localStorage.getItem('auth_token');
  const user = localStorage.getItem('user_data');

  if (token && user) {
    return true;
  }

  router.navigate(['/auth/login']);
  return false;
};
>>>>>>> Ramon_Paulino_Gil_100345706
