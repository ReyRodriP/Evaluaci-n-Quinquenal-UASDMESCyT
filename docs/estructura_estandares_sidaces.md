# Estructura de los Estándares Marco EQ-SIDACES (Referencia para ampliar la base de datos)

> **Fuente:** *Estándares Marco para la Evaluación y Acreditación Institucional en la Educación Superior Dominicana*, MESCYT – Viceministerio de Evaluación y Acreditación de las IES, Departamento de Evaluación Quinquenal. Aprobado mediante **Resolución 27-2019 del CONESCyT** (27 de septiembre de 2019). Sep/2019.
>
> **Propósito de este documento:** servir de referencia técnica para ampliar el modelo de datos del Sistema de Evaluación Quinquenal UASD–MESCyT al esquema oficial. **No implica cambios de código.** Solo describe cómo está estructurada cada dimensión en el documento oficial.

---

## 1. Modelo conceptual oficial

El documento oficial organiza la evaluación en una **jerarquía de seis niveles**, de mayor a menor generalidad:

```
Dimensión (8)
  └── Componente (36)
        └── Criterio (77)
              └── Estándar (~210)
                    └── Indicador (~909)
                          └── Evidencia (~915)
```

### 1.1 Definiciones oficiales

| Nivel | Definición oficial |
|-------|--------------------|
| **Dimensión** | Elemento estructural primario de mayor generalidad, contentivo de otros elementos con grados de generalidad decreciente, mediante los cuales se identifican y definen los aspectos formales y funcionales de una entidad educativa para fines de medición y valoración de su calidad. |
| **Componente** | Aspecto funcional que configura una dimensión institucional; aporta el conjunto coherente de actividades, actuaciones o subprocesos explícitos y secuenciados para desplegar las funciones de cada dimensión. |
| **Criterio** | Condición ideal que debe cumplir un determinado componente, actividad, actuación o proceso para ser considerado idóneo. |
| **Estándar** | Grado o magnitud en que se cumple o alcanza el criterio; rango (mínimo–máximo) en el que resulta aceptable el nivel de cumplimiento del criterio de calidad del objeto evaluado. |
| **Indicador** | Expresión cualitativa o cuantitativa que revela la concreción empírica del estándar en la realidad evaluada y muestra el nivel exacto o ponderación precisa en que se alcanza dicho estándar en el marco de un criterio. |
| **Evidencia** | Recurso, información o dato verificable, fiable, consistente e inequívoco sobre la entidad, actividad o actuación que alude al indicador y estándar bajo examen (cualitativa o cuantitativa). |

> **Nota de totales:** el texto oficial (Sec. 2.3) declara **8 dimensiones, 36 componentes, 77 criterios, 210 estándares, 909 indicadores y 915 evidencias indicativas**. La Figura 2 del mismo documento da cifras ligeramente diferentes (212 estándares, 915 indicadores, 1082 evidencias). La extracción automática del PDF arrojó **36 componentes, ~211 estándares y ~77 criterios**, muy cercana a los valores oficiales.

### 1.2 Codificación de identificadores (útil para modelar la BD)

Los ítems usan códigos numéricos encadenados según el nivel:

```
Dimensión:          I, II, III, ... VIII
Componente:         1.1  (dimensión . ordinal)
Criterio:           1.1.1  (componente . ordinal)
Estándar:           1.1.1.1  (criterio . ordinal)
Indicador:          (los indicadores van numerados dentro de cada estándar)
Evidencia:          (bullets asociados al indicador)
```

> La jerarquía 1.1.1.* es un prefijo natural de clave compuesta para las tablas nuevas (Dimensión → Componente → Criterio → Estándar → Indicador → Evidencia).

---

## 2. Comparativa con el modelo actual del sistema

El sistema hoy implementa `backend/evaluation/models.py`:

```
Periodo → Criterio → Indicador → Asignacion (indicador + unidad_responsable + periodo) → Evidencia(s)
```

| Nivel oficial | ¿Existe hoy? | Observación para ampliación |
|---------------|--------------|-----------------------------|
| Dimensión (8) | ❌ No | Nueva tabla raíz. |
| Componente (36) | ❌ No | Nueva tabla hija de Dimensión. |
| Criterio (77) | ⚠️ Parcial | Hoy `Criterio` cuelga de `Periodo`; en el modelo oficial cuelga de `Componente`. |
| Estándar (~210) | ❌ No | Nueva tabla hija de Criterio. |
| Indicador (~909) | ⚠️ Parcial | Hoy `Indicador` cuelga directamente de `Criterio`; en el oficial cuelga de `Estándar`. |
| Evidencia (~915) | ⚠️ Parcial | Ya existe gestión de evidencias, hoy asociada a la `Asignacion` de un indicador. |

**Diferencias clave a contemplar cuando se amplíe la BD:**
1. El criterio debe dejar de depender únicamente de `Periodo` y pasar a depender de `Componente` (oficialmente el criterio es transversal a los períodos de evaluación).
2. Se inserta el nivel **Estándar** entre Criterio e Indicador.
3. El componente oficial **define criterio "ideal"** y el estándar fija el **rango mínimo–máximo** aceptable (muchos estándares son cuantitativos, ej. "≥85%…", "≥25% del personal…"). Esto puede requerir campos de tipo/rango en la BD.
4. Las evidencias oficiales se enumeran **por indicador**, lo que encaja con el modelo actual de asignación a nivel de indicador.

---

## 3. Desglose por dimensión

Resumen cuantitativo por dimensión (criterios y estándares estimados de la extracción del PDF; los totales oficiales son 77/210…212):

| Dimensión | Componentes | Criterios ≈ | Estándares ≈ |
|-----------|-------------|-------------|--------------|
| I. Gestión Institucional | 8 | 15 | 40 |
| II. Gestión Académica | 6 | 17 | 44 |
| III. Investigación | 4 | 4 | 21 |
| IV. Vinculación con el Medio / Extensión | 6 | 11 | 22 |
| V. Estudiantes | 3 | 8 | 19 |
| VI. Personal Académico | 2 | 6 | 17 |
| VII. Servicios y Estructuras de Apoyo Institucional | 3 | 12 | 28 |
| VIII. Aseguramiento de la Calidad | 4 | 5 | 20 |
| **Total** | **36** | **≈78** | **≈211** |

---

### 3.1 DIMENSIÓN I — GESTIÓN INSTITUCIONAL

**Definición:** conjunto articulado de componentes, instancias, mecanismos y procesos que identifican, definen, organizan y despliegan los recursos y las acciones que conducen a la consecución de la misión y propósitos institucionales, a través de la gestión. Es contentiva del plan de desarrollo institucional, la estructura organizacional y de gobierno, la gestión administrativa y financiera, el marco legal y normativo interno, los recursos humanos para la gestión administrativa y de apoyo; incluye identidad y bienestar institucional, y el compromiso social con la ética, transparencia y rendición de cuentas.

| Comp. | Componente | Definición | Criterios≈ | Estándares≈ |
|-------|------------|------------|-----------|-------------|
| 1.1 | Filosofía y plan de desarrollo institucional | Declaración y adopción de misión y visión con principios y valores éticos y morales en un contexto definido. Contempla el Plan de Desarrollo para definir estrategia y marco de actuación hacia metas de la misión. | 2 | 6 |
| 1.2 | Estructura organizacional y sistema de gobierno | Configuración organizacional, jerárquica de funciones y autoridades (académicas, técnico-administrativas y financieras) en coherencia con políticas y marco legal; distribución de responsabilidades en la dirección y gestión. | 3 | 6 |
| 1.3 | Marco legal y normativo | Base legal y normatividad que establece y sustenta la legitimidad institucional y funcional de la IES en la realización de la misión e interacción con el medio. | 1 | 2 |
| 1.4 | Gestión administrativa y financiera | Capacidad de la IES para planificar, organizar, coordinar, monitorear y controlar procesos, actividades y recursos, permitiendo alcanzar objetivos y metas institucionales. | 2 | 6 |
| 1.5 | Bienestar institucional | Mecanismos, servicios o instrumentos articulados y suficientes que favorecen un ambiente de desempeño y convivencia de la comunidad académica; mejora progresiva del clima institucional. | 1 | 4 |
| 1.6 | Recursos humanos administrativos y de apoyo | Sistema de gestión del talento humano para procesos administrativos y de apoyo: reclutamiento, selección, capacitación, evaluación del desempeño, promoción, permanencia y salida, conforme a perfiles y funciones definidos. | 1 | 5 |
| 1.7 | Identidad institucional | Percepción que sobre la IES tienen los grupos de interés internos y externos; se estructura a partir de misión, visión, valores, políticas y prácticas, incluyendo símbolos, imagen y comunicación oficial. | 1 | 3 |
| 1.8 | Ética y transparencia | Compromiso social de la IES con buenas prácticas en la gestión de recursos, integridad institucional, rendición de cuentas y apego a principios, filosofía y misión. | 4 | 8 |

---

### 3.2 DIMENSIÓN II — GESTIÓN ACADÉMICA

**Definición:** integra las estrategias, acciones y procedimientos de diagnóstico, planeación, planificación, programación, organización, desarrollo, control y regulación de la oferta formativa y la docencia como función sustantiva de la IES, en el marco de la filosofía institucional, a través de la propuesta formativa que se entrega a la sociedad.

| Comp. | Componente | Definición | Criterios≈ | Estándares≈ |
|-------|------------|------------|-----------|-------------|
| 2.1 | Políticas educativas | Conjunto de prioridades y régimen procedimental que proporciona el marco de actuación para el desarrollo institucional y el logro de metas misionales inherentes a la gestión académica. | 1 | 6 |
| 2.2 | Articulación funcional desde la docencia | Configuración coherente y retroalimentación mutua entre la función de docencia y las demás funciones, incluyendo investigación y vinculación, para la mejora continua de la actividad docente. | 1 | 7 |
| 2.3 | Gestión de la oferta educativa | Procesos de diseño, coordinación, implementación, evaluación y mejora de la oferta académica conforme a filosofía, modelo institucional, normas vigentes y necesidades del contexto; se actualiza permanentemente. | 5 | 8 |
| 2.4 | Admisión | Proceso de recepción y aceptación del ingreso de estudiantes: validación de requisitos, evaluación de competencias, trámites administrativos, apertura de expediente y registro de matrícula. | 3 | 7 |
| 2.5 | Registro académico | Asiento de datos personales, preservación, certificación y entrega de la información académica que identifica la condición de estudiante, en un sistema centralizado y confiable. | 3 | 8 |
| 2.6 | Desarrollo y evaluación del proceso enseñanza-aprendizaje | Concepción, organización, coordinación y desarrollo de las actividades de enseñanza y aprendizaje en todas las ofertas: competencias, contenidos, estrategias didácticas, medios y evaluaciones, orientados al perfil de egreso. | 4 | 8 |

---

### 3.3 DIMENSIÓN III — INVESTIGACIÓN

**Definición:** aspecto misional de búsqueda, generación y sistematización de nuevos conocimientos, su transferencia y aplicación al desarrollo de la ciencia y la tecnología, al proceso formativo y a las intervenciones sociales. Identifica y prioriza políticas, recursos y medios para lograr metas de investigación, asegurando su relación con la docencia y la vinculación social.

| Comp. | Componente | Definición | Criterios≈ | Estándares≈ |
|-------|------------|------------|-----------|-------------|
| 3.1 | Política y normativa de investigación | Existencia de políticas y normativas que promuevan, apoyen y orienten la generación y difusión de nuevos conocimientos, y los mecanismos idóneos para planeación, asignación de recursos, desarrollo, publicación y uso de resultados. | 1 | 3 |
| 3.2 | Gestión de la investigación | Definición, implementación, seguimiento y evaluación de los procesos de investigación a través de una instancia responsable, con recursos humanos, logísticos, tecnológicos, materiales y financieros acordes a líneas de investigación. | 1 | 9 |
| 3.3 | Articulación funcional desde la investigación | Mecanismos de vinculación de la investigación con la actividad académica y las necesidades de la comunidad, aportando conocimientos, instrumentos y tecnologías a la docencia. | 1 | 4 |
| 3.4 | Resultados de la investigación | Productos y hallazgos generados por la actividad investigativa difundidos mediante publicaciones (revistas indexadas, libros, artículos), seminarios, conferencias y patentes, concordantes con las políticas y la misión. | 1 | 5 |

---

### 3.4 DIMENSIÓN IV — VINCULACIÓN CON EL MEDIO / EXTENSIÓN

**Definición:** aspecto misional que atiende el compromiso, interacciones y nexos con el medio natural, cultural, institucional y socioeconómico en que está inserta la IES. Incluye la validación/inserción de sus egresados y la internacionalización, en correspondencia con las necesidades de desarrollo del contexto.

| Comp. | Componente | Definición | Criterios≈ | Estándares≈ |
|-------|------------|------------|-----------|-------------|
| 4.1 | Políticas de Vinculación con el medio / Extensión | Conjunto de disposiciones que orientan planes, proyectos e iniciativas para definir estrategias y promover interacciones y nexos con el medio social, económico, ambiental, cultural y científico. | 2 | 4 |
| 4.2 | Gestión de la vinculación con el medio | Definición, ejecución, seguimiento y evaluación de procesos de vinculación/extensión que fortalecen la relación con el medio externo y responden a necesidades sociales diagnosticadas. | 2 | 4 |
| 4.3 | Articulación funcional e institucional | Mecanismos y acciones concretas de articulación del funcionamiento de la IES con otros actores del medio externo para mutuo beneficio y fortalecimiento del sistema de educación superior. | 2 | 4 |
| 4.4 | Resultados de la vinculación con el medio | Acciones realizadas y beneficios obtenidos de manera conjunta: recursos invertidos, actividades o programas desarrollados, contribuciones e impactos producidos en el medio. | 2 | 4 |
| 4.5 | Egresados | Registro oficial, organizado y trazable de personas tituladas; inserción laboral, desarrollo profesional, seguimiento al desempeño, retroalimentación incorporada y satisfacción de empleadores y grupos de interés. | 2 | 3 |
| 4.6 | Internacionalización | Políticas, mecanismos e iniciativas de proyección, cooperación y reconocimiento en el contexto internacional: relaciones con instituciones extra-nacionales para objetivos académicos, de investigación, intercambio o movilidad. | 1 | 3 |

---

### 3.5 DIMENSIÓN V — ESTUDIANTES

**Definición:** destinatario y actor clave de la naturaleza y contexto institucional en el cumplimiento de su misión y objetivos. Incluye admisión, orientación, integración y seguimiento a la trayectoria de vida, así como programas de asistencia y bienestar para desarrollo integral, permanencia, progreso y egreso exitoso.

| Comp. | Componente | Definición | Criterios≈ | Estándares≈ |
|-------|------------|------------|-----------|-------------|
| 5.1 | Sistema de gestión y bienestar estudiantil | Política y mecanismo efectivo para la gestión de condiciones de bienestar: becas, orientación académica, transporte, salud, alimentación, estímulos, financiamiento y residencia, garantizando permanencia y progreso. | 4 | 10 |
| 5.2 | Organización y participación de los estudiantes en la gestión institucional | Existencia y funcionamiento de mecanismos que establecen derechos, atribuciones y obligaciones de los estudiantes, régimen disciplinario y participación en órganos de gobierno y criterios académicos. | 1 | 3 |
| 5.3 | Vida y progreso académico | Dispositivos y procesos de registro y seguimiento del desempeño estudiantil, comunicación y diálogo, análisis de situaciones académicas y reconocimiento a la excelencia y contribuciones. | 3 | 6 |

---

### 3.6 DIMENSIÓN VI — PERSONAL ACADÉMICO

**Definición:** gestiona los recursos humanos responsables de las funciones académicas. Comprende la política de un sistema de carrera académica (selección, contratación, ingreso, categorización, evaluación del desempeño, desarrollo, certificación, promociones y desvinculación) y la participación del actor académico en la gestión institucional.

| Comp. | Componente | Definición | Criterios≈ | Estándares≈ |
|-------|------------|------------|-----------|-------------|
| 6.1 | Sistema de carrera académica | Política institucional de carrera académica orientada al desarrollo cualitativo y sostenibilidad: estructura progresiva con protocolo y dispositivos de captación, selección, contratación, evaluación, categorización, promoción y perfeccionamiento. | 5 | 13 |
| 6.2 | Participación en la gestión institucional | Existencia de mecanismos funcionales, claros y vigentes que garantizan y estimulan la participación de los profesores en la selección, organización, dirección y oferta curricular de la institución. | 1 | 4 |

---

### 3.7 DIMENSIÓN VII — SERVICIOS Y ESTRUCTURAS DE APOYO INSTITUCIONAL

**Definición:** conjunto articulado de elementos, mecanismos, recursos, facilidades e instrumentos que determinan la dinámica del funcionamiento institucional sobre los que descansa el cumplimiento de las funciones sustantivas: infraestructura física y tecnológica, recursos de apoyo, plataforma operativa y sistema de información.

| Comp. | Componente | Definición | Criterios≈ | Estándares≈ |
|-------|------------|------------|-----------|-------------|
| 7.1 | Infraestructura física | Instalaciones físicas, equipamiento y plataforma tecnológica para el desarrollo de las funciones del PDI, con mecanismos de dotación, mantenimiento y ampliación de espacios y equipos. | 8 | 18 |
| 7.2 | Sistema de información y comunicación | Dispositivo sistémico para la gestión de la información y la comunicación capaz de generar información confiable y oportuna para planeación, evaluación interna y toma de decisiones. | 3 | 7 |
| 7.3 | Recursos de apoyo a las funciones sustantivas y administrativas | Dotación, adecuación y suficiencia de recursos financieros, materiales y tecnológicos de apoyo, con protocolos de uso para alcanzar propósitos y metas del proyecto de desarrollo institucional. | 1 | 3 |

---

### 3.8 DIMENSIÓN VIII — ASEGURAMIENTO DE LA CALIDAD

**Definición:** configura la instancia, estructura, mecanismos y procesos orientados al fomento, regulación, control y garantía de la calidad interna de la IES y sus ofertas programáticas, para la construcción de una cultura de la calidad y mejora continua.

| Comp. | Componente | Definición | Criterios≈ | Estándares≈ |
|-------|------------|------------|-----------|-------------|
| 8.1 | Política de la calidad y herramientas para la mejora | Política institucional de aseguramiento de la calidad con criterios y mecanismos funcionales orientados a mejores prácticas basadas en estándares reconocidos internacionalmente. | 1 | 3 |
| 8.2 | Gestión de los resultados | Generación, manejo y uso de la información sobre el estado de la calidad institucional, disponible para análisis, valoración y sustento de decisiones de los actores legítimamente interesados. | 2 | 4 |
| 8.3 | Sistema interno de gestión de la calidad | Subsistema de gestión de la calidad que articula estructuras y procesos orientados a una cultura de evaluación y acreditación, con una unidad estructural interna y responsable definido. | 1 | 7 |
| 8.4 | Reducción de riesgos | Mecanismo funcional para identificación, monitoreo, valoración y mitigación de riesgos en las distintas esferas de la vida institucional, con un plan ejecutable y acciones de alta legitimidad social. | 1 | 6 |

---

## 4. Ejemplo completo de desglose (Componente 1.1)

Estructura real de la matriz oficial. Ilustra cómo cada nivel se concatena hasta la evidencia.

**Componente 1.1 — Filosofía y plan de desarrollo institucional**

> Se refiere a la declaración y adopción de una misión y visión institucional que incluyen un conjunto coherente de principios y valores éticos y morales en un contexto definido. Contempla la formulación de un Plan de Desarrollo mediante el cual la institución define una estrategia y un marco de actuación hacia la consecución de metas que corresponden a su misión.

| Criterio (1.1.1) | Estándar (1.1.1.x) | Indicadores (bullets) | Evidencias |
|------------------|--------------------|-----------------------|------------|
| **1.1.1. Establecimiento de la Filosofía institucional** | 1.1.1.1 | • La misión está claramente definida. • Describen la naturaleza de la institución. • Responde a necesidades del medio social y lineamientos de desarrollo nacional. • Es revisada periódicamente. • Fue actualizada con participación de actores clave. • Cuenta con medios para su divulgación y socialización. | − Acta de revisión y actualización de la filosofía institucional. − Actividades de socialización de la filosofía. − Ley 1-12 Estrategia Nacional de Desarrollo. − Informe de coherencia de la misión con la ley 1-12. − Estatuto orgánico. − Fundamentos filosóficos actualizados. − Lista de actores participantes. − Medios de difusión institucionales. − Resolución del máximo organismo de decisión. |
| | 1.1.1.2 | • La visión es coherente con el tipo de institución. • Alcanzable en el plazo indicado. • Revisada periódicamente. • Coherente con los objetivos de la END. | − Fundamentos filosóficos actualizados. − Informe de coherencia de la visión con la ley 1-12. |
| | 1.1.1.3 | • Valores/principios coherentes con el marco legal aplicable. • Coherentes con el SIDACES. • Revisados periódicamente. | − Constitución Dominicana. − Ley de Educación Superior. − Reglamentos de educación superior. − Fundamentos filosóficos actualizados. − Acta de revisión y actualización de la filosofía. − Documento de estándares marco SIDACES. |
| | 1.1.1.4 | • Objetivos expresados de manera clara y específica. • Expresan propósitos o metas medibles. • Alcanzables. • Corresponden con necesidades de desarrollo del país. | − Fundamentos filosóficos actualizados. − Documento de correspondencia objetivos–END. − Documento de Ley END 2030. |
| **1.1.2. Ejecución del Plan de Desarrollo Institucional** | 1.1.2.1 | • El PEI presenta descripción de la institución, contexto y políticas. • Contiene diagnóstico interno/externo. • Objetivos y ejes estratégicos a mediano y largo plazo. • Proyectos/programas por eje. • Resultados esperados. • Se formula con participación de actores clave. | − Plan Estratégico Institucional documentado y comunicado. − Cuadro de mando integral. − Memoria institucional. − Listado de actores clave participantes. |
| | 1.1.2.2 | • El plan operativo es coherente con las líneas estratégicas. • Objetivos de corto plazo. • Actividades por línea. • Cada actividad incluye responsable(s). • Cumplimiento de ≥85%. • Identifica recursos necesarios. | − Documento de plan operativo anual. − Cuadro de mando integral / matriz de seguimiento. − Reporte de cumplimiento del POA. − Memoria institucional. |

> Los códigos del ejemplo coinciden exactamente con los extraídos del PDF (2 criterios y 6 estándares para el componente 1.1); el resto de componentes sigue el mismo patrón de concurrencia entre criterios y estándares.

---

## 5. Observaciones finales para la ampliación de la BD

1. **Modelado sugerido (a futuro):** `Dimension` → `Componente` → `Criterio` → `Estándar` → `Indicador` → `Evidencia`, integrando el vínculo de `Criterio` a `Periodo` que el sistema usa hoy (el período podría asociarse a la asignación, no al criterio).
2. **Conteos oficiales** (para estimar volumen de datos): 8 dimensiones / 36 componentes / 77 criterios / ~210 estándares / ~909 indicadores / ~915 evidencias.
3. **Estándares cuantitativos:** muchos estándares expresan rangos o mínimos ("≥85%…", "≥25%…"), por lo que podría requerirse un tipo de dato (umbral/valor/booleano) al modelar la tabla `Estándar`.
4. **Evidencias por indicador:** el documento enumera las evidencias dentro de cada indicador; esto encaja con la asignación actual a nivel de indicador y con el módulo de evidencias ya existente.
5. Este documento se generó a partir de una extracción textual del PDF oficial; los conteos por componente marcados como "≈" son estimaciones de la extracción (los totales oficiales son los de la Sec. 1.1).