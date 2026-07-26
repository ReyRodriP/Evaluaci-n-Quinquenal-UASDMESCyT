# MANUAL DE USUARIO

## Sistema de Gestión de Evidencias para la Evaluación Quinquenal UASD–MESCyT

---

**República Dominicana**

**Universidad Autónoma de Santo Domingo**

**Facultad de Ciencias**

**Escuela de Informática**

---

**Sustentantes:**

- Reynaldo Rodríguez Polanco — 100655341
- Ramón Paulino Gil — 100345706
- José Manuel Otaño Hernández — 100320080

**Coordinador:** Mtro. Erick Minor

**Asesora Metodológica:** Mtra. Jacqueline Tejada Tio

**Asesora de Contenido:** Mtra. Martha Lidia Pérez Medina

---

**Santo Domingo, Distrito Nacional**

**Julio 2026**

---

## Contenido

1. [Introducción](#1-introducción)
2. [Acceso al Sistema](#2-acceso-al-sistema)
3. [Registro de Usuario](#3-registro-de-usuario)
4. [Recuperación de Contraseña](#4-recuperación-de-contraseña)
5. [Panel Principal (Dashboard)](#5-panel-principal-dashboard)
6. [Gestión de Usuarios](#6-gestión-de-usuarios)
7. [Gestión de Facultades y Departamentos](#7-gestión-de-facultades-y-departamentos)
8. [Gestión de Períodos](#8-gestión-de-períodos)
9. [Gestión de Criterios](#9-gestión-de-criterios)
10. [Gestión de Indicadores](#10-gestión-de-indicadores)
11. [Gestión de Asignaciones](#11-gestión-de-asignaciones)
12. [Gestión de Evidencias](#12-gestión-de-evidencias)
13. [Auditoría](#13-auditoría)
14. [Perfil y Configuración](#14-perfil-y-configuración)
15. [Cierre de Sesión](#15-cierre-de-sesión)

---

## 1. Introducción

El **Sistema de Gestión de Evidencias para la Evaluación Quinquenal UASD–MESCyT** es una plataforma web diseñada para centralizar, organizar y administrar las evidencias requeridas durante los procesos de evaluación institucional realizados por el Ministerio de Educación Superior, Ciencia y Tecnología (MESCyT) a la Universidad Autónoma de Santo Domingo (UASD).

Este manual de usuario tiene como propósito guiar a los diferentes actores que interactuarán con el sistema, describiendo de manera clara y detallada las funcionalidades disponibles, los procedimientos para realizar las operaciones más comunes y las recomendaciones para un uso eficiente de la plataforma.

El sistema está organizado en módulos que permiten la gestión de usuarios, facultades, departamentos, períodos de evaluación, criterios, indicadores, asignaciones y evidencias. Cada módulo cuenta con funcionalidades específicas que se describen en los capítulos siguientes.

---

## 2. Acceso al Sistema

### 2.1 Requisitos Técnicos

Para acceder al sistema, el usuario debe contar con:

- Un dispositivo (computadora, laptop, tablet o smartphone) con conexión a Internet.
- Un navegador web actualizado (Google Chrome, Microsoft Edge, Mozilla Firefox o Safari).
- Credenciales de acceso (usuario y contraseña) proporcionadas por el administrador del sistema.

### 2.2 Dirección de Acceso

Para ingresar a la plataforma, escribir la siguiente dirección en el navegador web:

**Frontend:** `http://localhost:4200` (entorno de desarrollo) o la URL proporcionada por la institución (entorno de producción).

### 2.3 Pantalla de Inicio de Sesión

Al acceder a la plataforma, se muestra la pantalla de inicio de sesión con los siguientes elementos:

1. **Logo de la UASD**: Identificación visual de la institución.
2. **Título**: "Inicio de Sesión".
3. **Subtítulo**: "Accede a tu seguimiento académico".
4. **Campo "Nombre de usuario"**: Ingresar el nombre de usuario asignado.
5. **Campo "Contraseña"**: Ingresar la contraseña correspondiente.
6. **Enlace "¿Olvidaste tu contraseña?"**: Permite recuperar la contraseña en caso de olvido.
7. **Botón "Ingresar"**: Para validar los datos e iniciar sesión.
8. **Enlace "Registrarse"**: Para crear una cuenta nueva.

**Procedimiento de inicio de sesión:**

1. Escribir el nombre de usuario en el campo correspondiente.
2. Ingresar la contraseña.
3. Verificar que los datos estén escritos correctamente (la contraseña se muestra oculta por seguridad).
4. Presionar el botón **"Ingresar"**.
5. Si los datos son correctos, el sistema redirigirá al panel principal (Dashboard).
6. Si los datos son incorrectos, se mostrará un mensaje de error: "Credenciales inválidas".

---

## 3. Registro de Usuario

Si el usuario no posee credenciales de acceso, puede registrarse en el sistema a través de la pantalla de registro.

### 3.1 Acceso al Registro

Desde la pantalla de inicio de sesión, hacer clic en el enlace **"Registrarse"** ubicado en la parte inferior.

### 3.2 Pantalla de Registro

La pantalla de registro presenta dos secciones:

**Sección izquierda (información institucional):**
- Logo de la UASD.
- Nombre de la universidad: "Universidad Autónoma de Santo Domingo".
- Logo del MESCyT.
- Descripción del sistema.

**Sección derecha (formulario de registro):**

Campos requeridos:

1. **Nombre de usuario**: Ingresar un nombre de usuario único para la identificación en el sistema.
2. **Correo electrónico**: Ingresar una dirección de correo electrónico válida.
3. **Nombre**: Ingresar el nombre real de la persona.
4. **Apellido**: Ingresar el apellido real de la persona.
5. **Teléfono**: Ingresar el número de teléfono (máximo 10 dígitos).
6. **Contraseña**: Ingresar una contraseña segura (mínimo 6 caracteres).
7. **Confirmar contraseña**: Repetir la contraseña para confirmación.

**Botón "Registrarse"**: Guarda los datos y crea la cuenta.

**Procedimiento de registro:**

1. Completar todos los campos del formulario.
2. Verificar que las contraseñas coincidan.
3. Presionar el botón **"Registrarse"**.
4. Si el registro es exitoso, se mostrará un mensaje de confirmación y se redirigirá a la pantalla de inicio de sesión.
5. Si hay errores, se mostrarán mensajes indicando los campos que deben corregirse.

---

## 4. Recuperación de Contraseña

En caso de olvidar la contraseña, el sistema ofrece un mecanismo de recuperación mediante correo electrónico.

### 4.1 Solicitud de Recuperación

1. En la pantalla de inicio de sesión, hacer clic en el enlace **"¿Olvidaste tu contraseña?"**.
2. Se abrirá la pantalla **"Recuperar Contraseña"**.
3. Ingresar el **correo electrónico** asociado a la cuenta.
4. Presionar el botón **"Enviar Instrucciones"**.
5. El sistema enviará un correo electrónico con las instrucciones para restablecer la contraseña.
6. Si el correo está registrado, se mostrará el mensaje: "Revisa tu correo para las instrucciones".

### 4.2 Restablecimiento de Contraseña

1. Abrir el correo electrónico recibido.
2. Hacer clic en el botón **"Restablecer Contraseña"** dentro del correo.
3. Será redirigido a la pantalla **"Nueva Contraseña"** en el sistema.
4. Ingresar la **nueva contraseña** (mínimo 6 caracteres).
5. **Confirmar la nueva contraseña**.
6. Presionar el botón **"Restablecer Contraseña"**.
7. Si el proceso es exitoso, se mostrará el mensaje: "Contraseña restablecida correctamente".
8. Será redirigido a la pantalla de inicio de sesión para ingresar con la nueva contraseña.

---

## 5. Panel Principal (Dashboard)

Después de iniciar sesión, el usuario accede al panel principal o Dashboard, que muestra un resumen general del sistema.

### 5.1 Estructura del Panel

El panel principal se compone de:

1. **Barra de navegación superior**: Muestra el logo de la UASD, el nombre del sistema "Sistema de Gestión de Evidencias", el nombre del usuario autenticado y un botón de cierre de sesión.
2. **Barra lateral (menú de navegación)**: Contiene los enlaces a los diferentes módulos del sistema.
3. **Área de contenido**: Muestra las tarjetas de estadísticas.

### 5.2 Tarjetas de Estadísticas

El dashboard presenta las siguientes tarjetas con los conteos actualizados del sistema:

| Tarjeta | Descripción |
|---------|-------------|
| Usuarios | Número total de usuarios registrados |
| Facultades | Número total de facultades |
| Departamentos | Número total de departamentos |
| Períodos | Número total de períodos de evaluación |
| Criterios | Número total de criterios |
| Indicadores | Número total de indicadores |
| Asignaciones | Número total de asignaciones |
| Evidencias | Número total de evidencias subidas |
| Asignaciones Pendientes/En Progreso | Asignaciones en estado pendiente o en progreso |
| Asignaciones Completadas/Aprobadas | Asignaciones completadas o aprobadas |

### 5.3 Menú de Navegación

La barra lateral contiene las siguientes opciones:

| Opción | Descripción |
|--------|-------------|
| Dashboard | Panel principal con estadísticas |
| Usuarios | Gestión de usuarios del sistema |
| Facultades | Gestión de facultades y departamentos |
| Períodos | Gestión de períodos de evaluación |
| Criterios | Gestión de criterios de evaluación |
| Indicadores | Gestión de indicadores |
| Asignaciones | Gestión de asignaciones |
| Evidencias | Subida y gestión de evidencias |
| Auditoría | Consulta de bitácora de actividades |
| Cerrar sesión | Salir del sistema |
| Modo oscuro | Alternar entre tema claro y oscuro |

---

## 6. Gestión de Usuarios

El módulo de usuarios permite visualizar y editar la información de los usuarios registrados en el sistema.

### 6.1 Pantalla de Usuarios

Al ingresar al módulo de usuarios, se muestra una tabla con los siguientes datos:

| Columna | Descripción |
|---------|-------------|
| Usuario | Nombre de usuario |
| Nombre | Nombre y apellido del usuario |
| Email | Correo electrónico |
| Teléfono | Número de teléfono |
| Rol | Rol asignado (Administrador General, Usuario, etc.) |
| Activo | Indicador de si la cuenta está activa |
| Acciones | Botones para editar el usuario |

### 6.2 Editar Usuario

1. Hacer clic en el botón **"Editar"** del usuario que se desea modificar.
2. Se abrirá una ventana modal con los datos del usuario.
3. Modificar los campos necesarios:
   - Email
   - Nombre
   - Apellido
   - Teléfono
   - Activo (marcar/desmarcar)
4. Presionar **"Guardar"** para confirmar los cambios.
5. Presionar **"Cancelar"** para descartar los cambios.
6. Si la operación es exitosa, se mostrará el mensaje "Usuario actualizado".

> **Nota:** La creación y eliminación de usuarios está disponible únicamente para usuarios con rol de Administrador General.

---

## 7. Gestión de Facultades y Departamentos

Este módulo permite administrar las facultades y sus departamentos asociados.

### 7.1 Pantalla de Facultades

Al ingresar al módulo, se muestran las facultades organizadas en tarjetas. Cada tarjeta contiene:

1. **Nombre de la facultad**.
2. **Descripción**.
3. **Estado** (Activo/Inactivo).
4. **Botones de acción**: Editar, Eliminar, + Depto.
5. **Lista de departamentos** asociados a la facultad, con su nombre, descripción, estado y acciones (Editar, Eliminar).

### 7.2 Crear una Facultad

1. Presionar el botón **"+ Nueva Facultad"**.
2. Completar los campos:
   - **Nombre**: Nombre de la facultad (requerido).
   - **Descripción**: Descripción de la facultad.
   - **Activo**: Marcar si la facultad está activa.
3. Presionar **"Guardar"**.

### 7.3 Editar una Facultad

1. Hacer clic en el botón **"Editar"** de la facultad deseada.
2. Modificar los campos necesarios.
3. Presionar **"Guardar"**.

### 7.4 Eliminar una Facultad

1. Hacer clic en el botón **"Eliminar"** de la facultad deseada.
2. Confirmar la eliminación en el cuadro de diálogo.
3. La facultad será eliminada junto con sus departamentos asociados.

### 7.5 Crear un Departamento

1. Hacer clic en el botón **"+ Depto"** de la facultad correspondiente.
2. Completar los campos:
   - **Nombre**: Nombre del departamento (requerido).
   - **Descripción**: Descripción del departamento.
   - **Facultad**: Seleccionar la facultad a la que pertenece.
   - **Activo**: Marcar si el departamento está activo.
3. Presionar **"Guardar"**.

### 7.6 Editar y Eliminar Departamento

- **Editar**: Hacer clic en el botón **"Editar"** del departamento, modificar los campos y guardar.
- **Eliminar**: Hacer clic en el botón **"Eliminar"** del departamento y confirmar la eliminación.

---

## 8. Gestión de Períodos

Los períodos definen los intervalos de tiempo para las evaluaciones.

### 8.1 Pantalla de Períodos

Al ingresar al módulo, se muestra una tabla con:

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre del período |
| Fecha Inicio | Fecha de inicio del período |
| Fecha Fin | Fecha de finalización del período |
| Activo | Indicador de si el período está activo |
| Acciones | Botones Editar y Eliminar |

### 8.2 Crear un Período

1. Presionar el botón **"+ Nuevo Período"**.
2. Completar los campos:
   - **Nombre**: Nombre del período (requerido).
   - **Fecha Inicio**: Fecha de inicio (requerido).
   - **Fecha Fin**: Fecha de finalización (requerido).
   - **Activo**: Marcar si está activo.
3. Presionar **"Guardar"**.

### 8.3 Editar o Eliminar un Período

- **Editar**: Hacer clic en **"Editar"**, modificar los datos y guardar.
- **Eliminar**: Hacer clic en **"Eliminar"** y confirmar la operación.

---

## 9. Gestión de Criterios

Los criterios definen las áreas de evaluación dentro de un período.

### 9.1 Pantalla de Criterios

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre del criterio |
| Descripción | Descripción del criterio |
| Período | Período al que pertenece |
| Activo | Indicador de actividad |
| Acciones | Botones Editar y Eliminar |

### 9.2 Crear un Criterio

1. Presionar **"+ Nuevo Criterio"**.
2. Completar los campos:
   - **Nombre**: Nombre del criterio (requerido).
   - **Descripción**: Descripción del criterio.
   - **Período**: Seleccionar el período al que pertenece.
   - **Activo**: Marcar si está activo.
3. Presionar **"Guardar"**.

### 9.3 Editar o Eliminar

- **Editar**: Modificar los datos del criterio y guardar.
- **Eliminar**: Confirmar la eliminación del criterio.

---

## 10. Gestión de Indicadores

Los indicadores son los elementos específicos que se evalúan dentro de cada criterio.

### 10.1 Pantalla de Indicadores

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre del indicador |
| Descripción | Descripción del indicador |
| Criterio | Criterio al que pertenece |
| Obligatorio | Indica si es obligatorio |
| Activo | Indicador de actividad |
| Acciones | Botones Editar y Eliminar |

### 10.2 Crear un Indicador

1. Presionar **"+ Nuevo Indicador"**.
2. Completar los campos:
   - **Nombre**: Nombre del indicador (requerido).
   - **Descripción**: Descripción del indicador.
   - **Criterio**: Seleccionar el criterio al que pertenece.
   - **Obligatorio**: Marcar si es un indicador obligatorio.
   - **Activo**: Marcar si está activo.
3. Presionar **"Guardar"**.

### 10.3 Editar o Eliminar

- **Editar**: Modificar los datos y guardar.
- **Eliminar**: Confirmar la eliminación.

---

## 11. Gestión de Asignaciones

Las asignaciones vinculan un indicador con un departamento y un período, estableciendo la responsabilidad de presentar evidencias.

### 11.1 Pantalla de Asignaciones

| Columna | Descripción |
|---------|-------------|
| Indicador | Nombre del indicador asignado |
| Departamento | Departamento responsable |
| Período | Período de evaluación |
| Estado | Estado de la asignación (color-coded) |
| Acciones | Botones Editar y Eliminar |

**Estados disponibles:**

| Estado | Descripción | Color |
|--------|-------------|-------|
| Pendiente | Asignación creada, sin evidencias | Amarillo |
| En progreso | Evidencias en proceso de carga | Azul |
| Completado | Evidencias completadas | Verde |
| Aprobado | Evidencias aprobadas | Azul oscuro |
| Rechazado | Evidencias rechazadas | Rojo |

### 11.2 Crear una Asignación

1. Presionar el botón **"+ Nueva Asignación"**.
2. Completar los campos:
   - **Indicador**: Seleccionar el indicador.
   - **Departamento**: Seleccionar el departamento responsable.
   - **Período**: Seleccionar el período de evaluación.
   - **Estado**: Seleccionar el estado inicial (generalmente "Pendiente").
3. Presionar **"Guardar"**.

### 11.3 Editar o Eliminar

- **Editar**: Modificar los campos y guardar.
- **Eliminar**: Confirmar la eliminación.

---

## 12. Gestión de Evidencias

El módulo de evidencias es el núcleo del sistema, permitiendo la subida, consulta y descarga de documentos.

### 12.1 Pantalla de Evidencias

Al ingresar al módulo, se muestra una tabla con las evidencias registradas:

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre del documento |
| Indicador | Indicador al que pertenece |
| Departamento | Departamento responsable |
| Versión | Número de versión del documento |
| Tamaño | Tamaño del archivo (B, KB, MB) |
| Subido por | Usuario que subió el archivo |
| Fecha | Fecha y hora de subida |
| Acciones | Botones Descargar y Eliminar |

### 12.2 Filtro por Asignación

En la parte superior de la tabla, hay un filtro desplegable que permite seleccionar una asignación específica para ver solo las evidencias relacionadas. La opción "Todas" muestra todas las evidencias.

### 12.3 Subir una Evidencia

1. Presionar el botón **"+ Subir Evidencia"**.
2. Completar los campos:
   - **Asignación**: Seleccionar la asignación relacionada.
   - **Nombre del documento**: Ingresar un nombre descriptivo (requerido).
   - **Descripción**: Descripción del documento.
   - **Archivo**: Seleccionar el archivo desde el dispositivo.
   - **Observaciones**: Comentarios adicionales.
3. **Formatos aceptados**: PDF, DOC, DOCX, XLS, XLSX, JPG, JPEG, PNG, GIF, TXT, ZIP, RAR.
4. **Tamaño máximo**: 50 MB por archivo.
5. Presionar **"Subir"** para cargar el archivo.

### 12.4 Descargar una Evidencia

1. Hacer clic en el botón **"Descargar"** de la evidencia deseada.
2. El archivo se descargará automáticamente al dispositivo.

### 12.5 Eliminar una Evidencia

1. Hacer clic en el botón **"Eliminar"** de la evidencia deseada.
2. Confirmar la eliminación en el cuadro de diálogo.
3. El archivo será eliminado del sistema.

---

## 13. Auditoría

El módulo de auditoría permite consultar el registro de todas las actividades realizadas en el sistema.

### 13.1 Pantalla de Auditoría

Se muestra una tabla con el historial de actividades:

| Columna | Descripción |
|---------|-------------|
| Fecha | Fecha y hora de la actividad |
| Usuario | Usuario que realizó la acción |
| Acción | Tipo de acción realizada |
| Modelo | Módulo afectado |
| Descripción | Detalle de la actividad |

### 13.2 Características

- **Solo lectura**: La bitácora de auditoría no puede ser modificada ni eliminada por los usuarios.
- **Registro automático**: Cada operación importante (inicio de sesión, creación, modificación, eliminación) queda registrada automáticamente.
- **Orden cronológico**: Los registros se muestran del más reciente al más antiguo.

**Ejemplos de actividades registradas:**

- "El usuario admin inició sesión"
- "Se registró el usuario jperez con email jperez@uasd.edu.do"
- "Se modificó el usuario mrodriguez"
- "Se creó la facultad Ciencias de la Salud"
- "El usuario jperez solicitó recuperación de contraseña"
- "El usuario mrodriguez restableció su contraseña"

---

## 14. Perfil y Configuración

### 14.1 Información del Usuario

En la barra de navegación superior se muestra el nombre del usuario autenticado (nombre y apellido), así como su rol dentro del sistema.

### 14.2 Modo Oscuro

El sistema cuenta con un modo oscuro que puede activarse desde la barra lateral, haciendo clic en el botón con el ícono de luna/sol. Esta opción permite alternar entre el tema claro y oscuro según la preferencia del usuario.

### 14.3 Perfil de Usuario

(Próximamente) Los usuarios podrán actualizar su información personal y cambiar su contraseña desde la sección de perfil.

---

## 15. Cierre de Sesión

Para cerrar la sesión de forma segura:

1. Hacer clic en el botón **"Cerrar sesión"** ubicado en la barra lateral (menú de navegación).
2. El sistema cerrará la sesión y redirigirá a la pantalla de inicio de sesión.
3. Se eliminarán los datos de autenticación almacenados en el dispositivo.

> **Recomendación:** Siempre cerrar sesión al finalizar el uso del sistema, especialmente en dispositivos compartidos o públicos.

---

## Apéndice: Solución de Problemas Comunes

| Problema | Posible Causa | Solución |
|----------|---------------|----------|
| No puedo iniciar sesión | Credenciales incorrectas | Verificar usuario y contraseña, usar recuperación de contraseña |
| No llega el correo de recuperación | Correo no registrado o spam | Verificar la bandeja de spam, contactar al administrador |
| Error al subir evidencia | Archivo muy grande o formato no soportado | Verificar tamaño (máx. 50MB) y formato del archivo |
| No veo algunos módulos | Permisos insuficientes | Contactar al administrador para asignación de roles |
| La página no carga | Problemas de conexión | Verificar conexión a Internet, recargar la página |

---

## Apéndice: Glosario de Términos

| Término | Definición |
|---------|------------|
| Evidencia | Documento o archivo que respalda el cumplimiento de un indicador |
| Indicador | Elemento específico sujeto a evaluación |
| Criterio | Área de evaluación que agrupa indicadores relacionados |
| Período | Intervalo de tiempo durante el cual se realiza la evaluación |
| Asignación | Relación entre un indicador, un departamento y un período |
| Facultad | Unidad académica principal de la universidad |
| Departamento | Subdivisión de una facultad |
| Auditoría | Registro histórico de las actividades realizadas en el sistema |
| Token | Código de autenticación que permite el acceso seguro al sistema |

---

**Documento elaborado por el equipo de desarrollo:**

- Reynaldo Rodríguez Polanco
- Ramón Paulino Gil
- José Manuel Otaño Hernández

**Universidad Autónoma de Santo Domingo (UASD)**

**Julio 2026**
