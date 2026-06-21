import { Routes } from '@angular/router';
import { AdminLayout } from './layouts/admin-layout/admin-layout/admin-layout';
import { AuthLayout } from './layouts/auth-layout/auth-layout/auth-layout';
import { Dashboard } from './features/dashboard/pages/dashboard/dashboard';
import { Usuarios } from './features/usuarios/usuarios';
import { Register } from './features/auth/pages/register/register';
import { Login } from './features/auth/pages/login/login';

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
            }
        ]
    },
    {
        path: '',
        component: AdminLayout,
        children: [
            {
                path: 'dashboard',
                component: Dashboard
            },
            {
                path: 'usuarios',
                component: Usuarios
            },
            //Seguir insertando rutas hijas
        ]
    },
    {
        path: '**',
        redirectTo: 'auth/login' //Cambiar a una ruta mas conveniente a futuro
    }
];
