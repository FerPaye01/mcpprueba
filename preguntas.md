Antes de escribir el prompt, sí tengo algunas preguntas. No porque sean imprescindibles, sino porque pueden cambiar muchísimo la calidad del Deep Research.

Las respondería como si fuera un arquitecto entrevistando al Product Owner de OpenEnergy.

---

## 1. ¿Cuál es el objetivo real de OpenEnergy?

¿Cuál de estas opciones describe mejor el producto?

A) Portal de consulta de datos energéticos

```text
Usuario
 ↓
Busca datos
 ↓
Visualiza
 ↓
Descarga
```

B) Plataforma de análisis energético

```text
Usuario
 ↓
Explora
 ↓
Filtra
 ↓
Compara
 ↓
Analiza
 ↓
Exporta
```

C) Copiloto energético con IA

```text
Usuario
 ↓
Pregunta en lenguaje natural
 ↓
IA
 ↓
Genera análisis
 ↓
Genera tablas
 ↓
Genera gráficos
```

D) Las tres anteriores.

---

## 2. ¿La IA será una característica central?

Esta pregunta es importantísima.

¿Tu visión es algo parecido a:

> "Muéstrame la demanda eléctrica de Lima entre 2020 y 2025"

y la IA construye:

* consulta
* tabla
* gráfico
* exportación

automáticamente.

¿O la IA será solo una ayuda secundaria?

---

## 3. ¿Qué tan importante es Angular?

Porque hay dos escenarios muy distintos.

### Escenario A

```text
React
↓
Quizá algún día Angular
```

No vale la pena optimizar demasiado.

---

### Escenario B

```text
React (prototipo)
↓
Angular 19 (producción)
```

Entonces sí debemos investigar tecnologías agnósticas.

---

## 4. ¿Qué tamaño de datos esperas?

¿Estamos hablando de:

### Pequeño

```text
100 - 10,000 filas
```

### Mediano

```text
100,000 filas
```

### Grande

```text
millones de registros
```

Esto cambia completamente la arquitectura.

---

## 5. ¿Qué tan parecida quieres que sea la experiencia a Excel?

Porque existen niveles.

### Nivel 1

* ordenar
* filtrar
* buscar

---

### Nivel 2

* ocultar columnas
* redimensionar columnas
* agrupar

---

### Nivel 3

* fórmulas
* pivots
* drag & drop

---

### Nivel 4

Prácticamente:

> "Excel en el navegador"

---

## 6. ¿Quién usará OpenEnergy?

Esto también cambia mucho las decisiones.

* público general
* analistas energéticos
* reguladores
* directivos
* investigadores
* todos los anteriores

---

## Lo que sospecho que ocurrirá

Si me baso en todo lo que me has contado durante meses, creo que tu visión se acerca a:

```text
OpenEnergy
│
├─ Datos energéticos
├─ Dashboards
├─ IA conversacional
├─ Tablas avanzadas
├─ Exportación
├─ Reportes
└─ Futura migración Angular
```

Y si esa hipótesis es correcta, entonces el Deep Research no debería preguntar:

> "¿Qué librería de tablas es mejor?"

sino algo mucho más ambicioso:

> "¿Cómo diseñan su arquitectura las plataformas modernas de Business Intelligence y los copilotos analíticos basados en IA?"

Porque ahí están los verdaderos referentes:

* Microsoft
* Salesforce
* Grafana Labs
* Datadog
* Google
* OpenAI (para la capa IA)

---

Si me respondes esas 6 preguntas, puedo ayudarte a construir un prompt de Deep Research de nivel arquitecto principal (principal architect), mucho más potente que un simple "compara librerías".




quí tienes mis respuestas y recomendaciones estratégicas para cada una de las 6 preguntas clave. Están alineadas con lo que hemos construido en la arquitectura técnica de
  OpenEnergy y el contexto real de Osinergmin:                                                                                                                               
  ──────                                                                                                                                                                     
  ### 1. ¿Cuál es el objetivo real de OpenEnergy?                                                                                                                            
                                                                                                                                                                             
  • Respuesta Recomendada: D) Las tres anteriores.                                                                                                                           
  • Justificación: OpenEnergy es un ecosistema analítico integral. Actúa como Copiloto con IA (C) al permitir que un directivo consulte en lenguaje natural y reciba un      
  análisis interpretado con gráficos autogenerados. Sin embargo, una vez que la IA responde, el usuario técnico (fiscalizadores o reguladores) necesita Explorar, comparar y 
  filtrar (B) esos resultados en el sidebar, para finalmente Visualizarlos y descargarlos (A) a formatos corporativos como Excel o SVG. Las tres capacidades deben coexistir 
  de forma armónica.                                                                                                                                                         
  ──────                                                                                                                                                                     
  ### 2. ¿La IA será una característica central?                                                                                                                             
                                                                                                                                                                             
  • Respuesta Recomendada: Sí, la IA es el orquestador central (Core).                                                                                                       
  • Justificación: En este prototipo, la IA no es un chatbot pasivo de soporte; es el motor que ejecuta de manera autónoma el flujo de datos. Al pedir "Demanda eléctrica en 
  Lima", la IA decide qué tabla consultar en el catálogo MCP, genera el JSON del gráfico interactivo, estructura la tabla markdown y el frontend la renderiza en el canvas.  
  La interfaz visual y las tablas interactivas son el receptor y refinador de lo que la IA construye dinámicamente.                                                          
  ──────                                                                                                                                                                     
  ### 3. ¿Qué tan importante es Angular?                                                                                                                                     
                                                                                                                                                                             
  • Respuesta Recomendada: Escenario B (React Prototipo → Angular 19 Producción).                                                                                            
  • Justificación: Dado el comentario de tu jefe sobre las coordinaciones con los arquitectos Rafael y Edgar y el equipo de desarrollo corporativo, el estándar de producción
  a largo plazo en la institución es Angular. Por lo tanto, sí vale la pena optimizar y elegir tecnologías agnósticas (Headless) desde hoy. Usar TanStack Table y motores    
  lógicos matemáticos puros en TypeScript (como  TimeSeriesEngine.ts ) nos ahorrará meses de reescritura de código cuando el equipo de Osinergmin migre la app a Angular 19. 
  ──────                                                                                                                                                                     
  ### 4. ¿Qué tamaño de datos esperas?                                                                                                                                       
                                                                                                                                                                             
  • Respuesta Recomendada: Híbrido (Backend maneja millones de registros, Frontend procesa entre 100 y 10,000 filas por vista activa).                                       
  • Justificación: La base de datos MCP de Osinergmin maneja millones de registros históricos de transacciones de energía y precios spot. Para evitar colapsar la memoria del
  navegador y garantizar 60 FPS constantes:                                                                                                                                  
      1. El backend de Python e IA ejecutan queries con agregaciones y filtros optimizados.                                                                                  
      2. El frontend de React/Angular recibe el dataset refinado (ej: 500 filas de promedios diarios o mensuales).                                                           
      3. Esto permite que las tablas del navegador respondan al instante y que los gráficos vectoriales se exporten de inmediato.                                            
                                                                                                                                                                             
  ──────                                                                                                                                                                     
  ### 5. ¿Qué tan parecida quieres que sea la experiencia a Excel?                                                                                                           
                                                                                                                                                                             
  • Respuesta Recomendada: Nivel 1 (Ordenar, filtrar, buscar) + Nivel 2 (Paginación y redimensionamiento de columnas).                                                       
  • Justificación: Para un prototipo ágil en el sector gubernamental, los Nivel 1 y 2 cubren el 95% de las necesidades del analista promedio sin pagar licencias de          
  componentes costosos (como AG Grid Enterprise) ni sobrecargar el bundle. Además, delegamos el "Nivel 3" (fórmulas complejas o pivots) al Copiloto con IA: el usuario puede 
  simplemente escribir "Agrúpame las centrales de generación por tipo de tecnología y saca el promedio de potencia" y la IA realiza el pivote antes de entregar la tabla     
  interactiva terminada.                                                                                                                                                     
  ──────                                                                                                                                                                     
  ### 6. ¿Quién usará OpenEnergy?                                                                                                                                            
                                                                                                                                                                             
  • Respuesta Recomendada: Analistas energéticos, reguladores y directivos de Osinergmin.                                                                                    
  • Justificación: El diseño debe ser bifocal, basado en roles (habrá tablas autorizadas para ciertos roles):                                                                                                                                
      • Para los directivos y gerentes: Debe ser visualmente impactante, rápido, con resúmenes ejecutivos en lenguaje natural y gráficos interactivos fáciles de interpretar 
      en un clic.                                                                                                                                                            
      • Para los analistas técnicos y reguladores: Debe ser preciso, con tablas estructuradas donde puedan verificar las columnas, exportar a Excel real para sus propios    
      informes externos y tener filtros regionales exactos. 
                                                                                                     
                                                                 