import { Injectable } from '@angular/core';
import { AuthService } from '../../features/auth/services/auth-service';

export interface MenuItem {
  path: string;
  label: string;
  icon: string;
  grupos: string[] | null;
}

@Injectable({ providedIn: 'root' })
export class PermisosService {
  readonly menuItems: MenuItem[] = [
    { path: '/dashboard', label: 'Dashboard', icon: 'bx-home', grupos: null },
    { path: '/usuarios', label: 'Usuarios', icon: 'bx-user', grupos: ['Administrador General', 'Coordinador Quinquenal'] },
    { path: '/roles', label: 'Roles', icon: 'bx-shield-quarter', grupos: ['Administrador General', 'Coordinador Quinquenal'] },
    { path: '/facultades', label: 'Facultades', icon: 'bx-arch', grupos: ['Administrador General', 'Coordinador Quinquenal'] },
    { path: '/departamentos', label: 'Departamentos', icon: 'bx-building', grupos: ['Administrador General', 'Coordinador Quinquenal'] },
    { path: '/periodos', label: 'Períodos', icon: 'bx-calendar', grupos: ['Administrador General', 'Coordinador Quinquenal'] },
    { path: '/criterios', label: 'Criterios', icon: 'bx-list-ul', grupos: ['Administrador General', 'Coordinador Quinquenal'] },
    { path: '/indicadores', label: 'Indicadores', icon: 'bx-bar-chart', grupos: ['Administrador General', 'Coordinador Quinquenal'] },
    { path: '/asignaciones', label: 'Asignaciones', icon: 'bx-task', grupos: null },
    { path: '/evidencias', label: 'Evidencias', icon: 'bx-file', grupos: null },
    { path: '/notificaciones', label: 'Notificaciones', icon: 'bx-bell', grupos: null },
    { path: '/auditorias', label: 'Auditorías', icon: 'bx-archive', grupos: ['Administrador General', 'Coordinador Quinquenal', 'Revisor Institucional'] },
  ];

  constructor(private authService: AuthService) {}

  get grupos(): string[] {
    return this.authService.getUser()?.groups ?? [];
  }

  get permisos(): string[] {
    return this.authService.getUser()?.permisos ?? [];
  }

  get rol(): string | null {
    return this.authService.getUser()?.rol ?? null;
  }

  tieneGrupo(grupo: string): boolean {
    return this.grupos.includes(grupo);
  }

  tienePermiso(codename: string): boolean {
    return this.permisos.includes(codename);
  }

  tieneAlgunPermiso(codenames: string[]): boolean {
    return codenames.some(c => this.permisos.includes(c));
  }

  menuVisible(): MenuItem[] {
    return this.menuItems.filter(item => {
      if (!item.grupos) return true;
      return item.grupos.some(g => this.tieneGrupo(g));
    });
  }

  puedeAccederRuta(path: string): boolean {
    const item = this.menuItems.find(m => m.path === path);
    if (!item) return true;
    if (!item.grupos) return true;
    return item.grupos.some(g => this.tieneGrupo(g));
  }
}
