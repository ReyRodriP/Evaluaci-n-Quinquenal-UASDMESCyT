import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { PermisosService } from '../services/permisos.service';

@Injectable({ providedIn: 'root' })
export class PermisoGuard implements CanActivate {
  constructor(private permisosService: PermisosService, private router: Router) {}

  canActivate(route: any): boolean | UrlTree {
    const path = '/' + route.routeConfig?.path;
    if (this.permisosService.puedeAccederRuta(path)) {
      return true;
    }
    return this.router.parseUrl('/dashboard');
  }
}
