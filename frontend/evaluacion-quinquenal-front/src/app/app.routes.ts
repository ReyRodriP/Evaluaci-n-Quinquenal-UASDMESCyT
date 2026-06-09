import { Routes } from '@angular/router';
import { AdminLayout } from './layouts/admin-layout/admin-layout/admin-layout';
import { Dashboard } from './layouts/admin-layout/dashboard/dashboard';
import { Usuarios } from './layouts/admin-layout/usuarios/usuarios';

export const routes: Routes = [
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
        redirectTo: 'index'
    }
];
