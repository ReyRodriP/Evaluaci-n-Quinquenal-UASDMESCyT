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
