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
import { Departamentos } from './features/departamentos/departamentos';
import { Periodos } from './features/periodos/periodos';
import { Indicadores } from './features/indicadores/indicadores';
import { Criterios } from './features/criterios/criterios';
import { Asignaciones } from './features/asignaciones/asignaciones';
import { Evidencias } from './features/evidencias/evidencias';
import { EvidenciaDetalle } from './features/evidencias/evidencia-detalle/evidencia-detalle';
import { AuditoriaComponent } from './features/auditoria/auditoria.component';
import { authGuard } from './core/guards/auth.guard';
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
            { path: 'register', component: Register },
            { path: 'login', component: Login },
            { path: 'forgot-password', component: ForgotPassword },
            { path: 'reset-password', component: ResetPassword }
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
            { path: 'departamentos', component: Departamentos },
            { path: 'periodos', component: Periodos },
            { path: 'criterios', component: Criterios },
            { path: 'indicadores', component: Indicadores },
            { path: 'asignaciones', component: Asignaciones },
            { path: 'evidencias', component: Evidencias },
            { path: 'evidencias/:id/detalle', component: EvidenciaDetalle },
            { path: 'auditoria', component: AuditoriaComponent },
            { path: 'roles', component: Roles },
            { path: 'perfil', component: Perfil }
        ]
    },
    {
        path: '**',
        redirectTo: 'auth/login'
    }
];
