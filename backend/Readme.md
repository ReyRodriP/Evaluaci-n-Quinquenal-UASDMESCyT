//-----Primeros pasos
1-py -m pip install virtualenv          //Instalar virtualenv
2-virtualenv venv                       //Creacion del entorno virtual
3-py -m pip install django              //Instalacion de django
4-py -m pip install djangoRestframework //Instalacion de django RestFramework
5-django-admin startproject <nombre> .  //Creacion del proyecto
6-py -m pip install django-cors-headers //Instalacion de CORS para comunicacion con el front

//-----Apps a utilizar 
1.py manage.py startapp accounts        //App accounts para lo relacionado a usuarios

//-----Super usuario actual
Username: omori
Email: suicidaloco@gmail.com
password: 12345678

//-----Roles y permisos (API)

Roles (Groups de Django):
  GET/POST   /api/roles/          // Listar / Crear rol
  GET/PUT/DELETE /api/roles/{id}/ // Ver / Actualizar / Eliminar rol

Permisos:
  GET /api/permisos/ // Listar permisos disponibles

Asignar permisos a un rol (via API):
  PUT /api/roles/{id}/  con {"name": "Admin", "permission_ids": [1, 2, 3]}

Asignar rol a usuario:
  PUT /api/profile/     con {"group_ids": [1, 2]}
  (el perfil del usuario devuelve groups con sus roles y permisos)

# Roles actuales con sus respectivos permisos 

1. Administrador General
-Todos

2. Coordinador Quinquenal
-Visualizar Dashboard
-Manejar Facultades
-Manejar Departamentos
-Manejar Periodos
-Manejar Criterios
-Manejar Indicadores
-Manejar Asignaciones
-Manejar Evidencias
-Visualizar Auditoria

3. Responsable Departamental
-Ver indicadores asignados
-Subir Evidencias
-Actualizar Evidencias
-Responder Observaciones
-Ver Dashboard

4. Revisor Institucional
-Revisar evidencias 
-Aprobar y rechazarlas
-Agregar observaciones 

5. Consulta 
-Ninguno