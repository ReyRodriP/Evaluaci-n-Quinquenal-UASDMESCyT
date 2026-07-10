import { Routes } from '@angular/router';
import { AdminLayout } from './layouts/admin-layout/admin-layout/admin-layout';
import { AuthLayout } from './layouts/auth-layout/auth-layout/auth-layout';
import { Dashboard } from './features/dashboard/pages/dashboard/dashboard';
import { Usuarios } from './features/usuarios/usuarios';
import { Register } from './features/auth/pages/register/register';
import { Login } from './features/auth/pages/login/login';
import { Facultades } from './features/facultades/facultades';
import { PeriodosComponent } from './features/periodos/periodos.component';
import { CriteriosComponent } from './features/criterios/criterios.component';
import { IndicadoresComponent } from './features/indicadores/indicadores.component';
import { AsignacionesComponent } from './features/asignaciones/asignaciones.component';
import { EvidenciasComponent } from './features/evidencias/evidencias.component';
import { AuditoriaComponent } from './features/auditoria/auditoria.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'auth',
    redirectTo: 'auth/login',
    pathMatch: 'full'
  },
  {
    path: 'auth',
    component: AuthLayout,
    children: [
      { path: 'register', component: Register },
      { path: 'login', component: Login }
    ]
  },
  {
    path: '',
    component: AdminLayout,
    canActivate: [authGuard],
    children: [
      { path: 'dashboard', component: Dashboard },
      { path: 'usuarios', component: Usuarios },
      { path: 'facultades', component: Facultades },
      { path: 'periodos', component: PeriodosComponent },
      { path: 'criterios', component: CriteriosComponent },
      { path: 'indicadores', component: IndicadoresComponent },
      { path: 'asignaciones', component: AsignacionesComponent },
      { path: 'evidencias', component: EvidenciasComponent },
      { path: 'auditoria', component: AuditoriaComponent },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
