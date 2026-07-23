# Sistema de GestiÃ³n de Evidencias para la EvaluaciÃ³n Quinquenal UASDâ€“MESCyT

Plataforma web para centralizar, administrar y dar seguimiento a las evidencias requeridas durante los procesos de evaluaciÃ³n institucional de la Universidad AutÃ³noma de Santo Domingo (UASD) ante el Ministerio de EducaciÃ³n Superior, Ciencia y TecnologÃ­a (MESCyT).

## Tech Stack

| Capa       | TecnologÃ­a          | VersiÃ³n  |
|------------|---------------------|----------|
| Backend    | Python + Django     | 6.0.5    |
| API        | Django REST Framework | -       |
| Frontend   | Angular             | 20.3     |
| Lenguaje   | TypeScript          | 5.9      |
| BD (dev)   | SQLite3             | -        |
| Auth       | Token Authentication | -       |

## Estructura del Proyecto

```
monografico/
â”œâ”€â”€ backend/                           # Django project
â”‚   â”œâ”€â”€ accounts/                      # AutenticaciÃ³n y usuarios
â”‚   â”œâ”€â”€ auditoria/                     # BitÃ¡cora de auditorÃ­a
â”‚   â”œâ”€â”€ evaluacionQuinquenal/          # Config del proyecto Django
â”‚   â”œâ”€â”€ evaluation/                    # PerÃ­odos, criterios, indicadores, asignaciones
â”‚   â”œâ”€â”€ evidencias/                    # GestiÃ³n de evidencias (core)
â”‚   â”œâ”€â”€ notificaciones/                # Notificaciones internas
â”‚   â”œâ”€â”€ organization/                  # Facultades, departamentos, perfiles
â”‚   â”œâ”€â”€ media/                         # Archivos subidos (evidencias)
â”‚   â”œâ”€â”€ manage.py
â”‚   â””â”€â”€ requirements.txt
â”‚
â”œâ”€â”€ frontend/
â”‚   â””â”€â”€ evaluacion-quinquenal-front/   # Angular standalone project
â”‚       â””â”€â”€ src/app/
â”‚           â”œâ”€â”€ core/                  # Modelos, servicios, guards, interceptors
â”‚           â”œâ”€â”€ features/              # PÃ¡ginas por mÃ³dulo
â”‚           â”‚   â”œâ”€â”€ auth/              # Login, registro
â”‚           â”‚   â”œâ”€â”€ dashboard/         # Tablero principal
â”‚           â”‚   â”œâ”€â”€ usuarios/          # CRUD usuarios
â”‚           â”‚   â”œâ”€â”€ facultades/        # CRUD facultades y departamentos
â”‚           â”‚   â”œâ”€â”€ periodos/          # CRUD perÃ­odos
â”‚           â”‚   â”œâ”€â”€ criterios/         # CRUD criterios
â”‚           â”‚   â”œâ”€â”€ indicadores/       # CRUD indicadores
â”‚           â”‚   â”œâ”€â”€ asignaciones/      # CRUD asignaciones
â”‚           â”‚   â”œâ”€â”€ evidencias/        # Subida/descarga/lista de evidencias
â”‚           â”‚   â””â”€â”€ auditoria/         # BitÃ¡cora de auditorÃ­a
â”‚           â”œâ”€â”€ layouts/               # AdminLayout y AuthLayout
â”‚           â””â”€â”€ shared/                # Sidebar y Navbar
â”‚
â”œâ”€â”€ plan.md                            # Documento de planificaciÃ³n del proyecto
â””â”€â”€ README.md
```

## Funcionalidades

### MÃ³dulos del Sistema

1. **AutenticaciÃ³n y Usuarios**
   - Login/registro con token
   - Perfil de usuario, cambio de contraseÃ±a
   - Roles y permisos (basado en grupos de Django)

2. **OrganizaciÃ³n**
   - CRUD de facultades
   - CRUD de departamentos (por facultad)
   - Perfiles de usuario por departamento

3. **EvaluaciÃ³n**
   - PerÃ­odos de evaluaciÃ³n
   - Criterios por perÃ­odo
   - Indicadores por criterio
   - Asignaciones (indicador + departamento + perÃ­odo) con flujo de estados: pendiente â†’ en_progreso â†’ completado â†’ aprobado/rechazado

4. **GestiÃ³n de Evidencias** (core)
   - Subida de archivos (PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF, TXT, ZIP, RAR; mÃ¡x. 50MB)
   - Versionado automÃ¡tico por asignaciÃ³n
   - Descarga de documentos
   - Filtro por asignaciÃ³n

5. **AuditorÃ­a**
   - Registro automÃ¡tico de todas las operaciones CRUD
   - Consulta de bitÃ¡cora con fecha, usuario, acciÃ³n y descripciÃ³n

6. **Notificaciones**
   - Notificaciones automÃ¡ticas al asignar indicadores
   - Notificaciones al cambiar estado de asignaciones

7. **Dashboard**
   - EstadÃ­sticas generales del sistema
   - Conteo de usuarios, facultades, departamentos, perÃ­odos, criterios, indicadores, asignaciones, evidencias

## InstalaciÃ³n y EjecuciÃ³n

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend/evaluacion-quinquenal-front
npm install --legacy-peer-deps
npm start
```

El backend corre en `http://127.0.0.1:8000` y el frontend en `http://localhost:4200`.

### Superusuario por defecto

```
Username: mrPopoMaster
Email: popomrMaster001@gmail.com
Password: 12345678
```

## API Endpoints

See `backend/Readme.md`.

## Frontend — Control de permisos en UI

### PermisosService (core/services/permisos.service.ts)

Servicio central que determina qué puede ver/hacer el usuario en la UI.

**Propiedades:**
- esSuperuser — true si el backend marcó is_superuser.
- grupos — lista de nombres de grupo del usuario.
- permisos — lista de codenames (ej. "evaluation.view_asignacion").
- ol — nombre del primer grupo (cómodo para lectura).

**Métodos:**
- 	ieneGrupo(nombre) — true si el grupo está en la lista o si es superuser.
- 	ienePermiso(codename) — true si el permiso está en la lista o si es superuser.
- 	ieneAlgunPermiso(lista) — true si tiene alguno de los permisos o es superuser.
- menuVisible() — filtra los ítems del sidebar según grupos del usuario.
- puedeAccederRuta(path) — usado por el guard para proteger rutas.

### MenuItems definidos

Cada item del menú lateral especifica los grupos permitidos (grupos: string[] | null). null = todos los autenticados.

### PermisoGuard (core/guards/permiso.guard.ts)

Guarda de ruta que verifica puedeAccederRuta(). Si el usuario no tiene acceso, redirige a /dashboard.

Aplicado en pp.routes.ts a las rutas restringidas (usuarios, roles, facultades, departamentos, periodos, criterios, indicadores, auditorias).

### Acciones CRUD condicionales

Cada página inyecta PermisosService y expone:
- puedeCrear: boolean — controla [showCreate] del SearchBar.
- ocultarAcciones: string[] — controla [ocultarAcciones] del CrudTable.

Ejemplo (asignaciones):
`	ypescript
get puedeCrear(): boolean {
  return this.permisos.tieneAlgunPermiso(['evaluation.add_asignacion']);
}
get ocultarAcciones(): string[] {
  if (this.permisos.tieneAlgunPermiso(['evaluation.change_asignacion', 'evaluation.delete_asignacion'])) {
    return [];
  }
  return ['edit', 'toggle', 'remove'];
}
`

### Búsqueda global

El navbar filtra los grupos de resultados según permisos. Si el usuario no tiene evaluation.view_indicador, no ve resultados de tipo Indicador en el dropdown de búsqueda.
