import { Routes } from '@angular/router';
import { AdminLayout } from './layouts/admin-layout/admin-layout/admin-layout';
import { AuthLayout } from './layouts/auth-layout/auth-layout/auth-layout';
import { Dashboard } from './features/dashboard/pages/dashboard/dashboard';
import { Usuarios } from './features/usuarios/usuarios';
import { Roles } from './features/roles/roles';
import { Register } from './features/auth/pages/register/register';
import { Login } from './features/auth/pages/login/login';
import { ForgotPassword } from './features/auth/pages/forgot-password/forgot-password';
import { ResetPassword } from './features/auth/pages/reset-password/reset-password';
import { Facultades } from './features/facultades/facultades';
<<<<<<< HEAD
import { Departamentos } from './features/departamentos/departamentos';
import { Periodos } from './features/periodos/periodos';
import { Indicadores } from './features/indicadores/indicadores';
import { Criterios } from './features/criterios/criterios';
import { Asignaciones } from './features/asignaciones/asignaciones';
import { Evidencias } from './features/evidencias/evidencias';
import { EvidenciaDetalle } from './features/evidencias/evidencia-detalle/evidencia-detalle';
import { AuthGuard } from './core/guards/auth.guard';
import { Perfil } from './features/perfil/perfil';

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
            {
                path: 'register',
                component: Register
            },
            {
                path: 'login',
                component: Login
            },
            {
                path: 'forgot-password',
                component: ForgotPassword
            },
            {
                path: 'reset-password',
                component: ResetPassword
            }
        ]
    },
    {
        path: '',
        component: AdminLayout,
        canActivate: [AuthGuard],
        children: [
            {
                path: 'dashboard',
                component: Dashboard
            },
            {
                path: 'usuarios',
                component: Usuarios
            },
            {
                path: 'facultades',
                component: Facultades
            },
            {
                path: 'departamentos',
                component: Departamentos
            },
            {
                path: 'periodos',
                component: Periodos
            },
            {
                path: 'criterios',
                component: Criterios
            },
            {
                path: 'indicadores',
                component: Indicadores
            },
            {
                path: 'asignaciones',
                component: Asignaciones
            },
            {
                path: 'evidencias',
                component: Evidencias
            },
            {
                path: 'evidencias/:id/detalle',
                component: EvidenciaDetalle
            },
            {
                path: 'roles',
                component: Roles
            },
            {
                path: 'perfil',
                component: Perfil
            }
            //Seguir insertando rutas hijas
        ]
    },
    {
        path: '**',
        redirectTo: 'auth/login' //Cambiar a una ruta mas conveniente a futuro
    }
=======
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
>>>>>>> Ramon_Paulino_Gil_100345706
];
