# Especificación de Requisitos de Software: Prototipo OpenEnergy (AP0162)

## 1. Introducción y Propósito
El sistema **OpenEnergy** es un prototipo agente de analítica de datos desarrollado para la Gerencia de Sistemas y Tecnologías de la Información (GSTI) de Osinergmin. Su propósito es habilitar la exploración y consulta segura de información corporativa sobre generación eléctrica e hidrocarburos mediante lenguaje natural, eliminando la fricción técnica y proporcionando visualizaciones e informes listos para la toma de decisiones gerenciales.

---

## 2. Requisitos Funcionales (RF)

### 2.1. Funcionalidades Logradas (Fase Actual)
*   **RF-01: Consulta Asistida en Lenguaje Natural:** El usuario puede ingresar solicitudes libres (ej. *"¿Cuáles son las centrales en servicio en Arequipa y su potencia?"*) sin necesidad de conocer la sintaxis SQL ni la estructura interna de la base de datos Oracle.
*   **RF-02: Consulta de Esquemas Gobernados (Oracle/MCP):** El sistema permite realizar consultas exclusivas sobre las fuentes y objetos autorizados del esquema `ES_DATGOB_CV` (capa silver/verde) y `ES_DATGOB_CG` (capa gold/azul) de forma controlada.
*   **RF-03: Sincronización Dinámica de Filtros (Sidebar):** Permite aplicar filtros en el panel lateral (ubicación geográfica y matriz energética) y propagarlos en tiempo real vía WebSockets al backend para inyectarlos en el prompt del sistema del LLM.
*   **RF-04: Visualización Interactiva Nativa SVG (`json-chart`):** Si los datos contienen variables numéricas y categóricas, el frontend renderiza un componente de gráfico interactivo SVG con tooltips reactivos al hover y un botón de descarga vectorial rápida.
*   **RF-05: Catálogo Dinámico de Datasets (`json-datasets`):** Si el agente lista el catálogo mediante `get_catalogo_datos`, el frontend interpreta el resultado y renderiza un carrusel de tarjetas interactivas de base de datos (`DatasetCard`).
*   **RF-06: Conservación de Contexto de Trabajo:** El sistema mantiene el hilo conversacional, los filtros activos del sidebar y los resultados de las últimas consultas para permitir análisis sucesivos y comparativos.
*   **RF-07: Control de Autoconsulta Seguro (Solo Lectura):** Bloqueo estricto que impide al agente y al usuario realizar operaciones de alteración de base de datos (INSERT, UPDATE, DELETE, DROP, ALTER, etc.), respetando el principio de inmutabilidad de los datos de origen.
*   **RF-08: Autologin e Identidad Temporal Dinámica:** Autogenera identidades analíticas temporales (ej. `Especialista 964`) y realiza un login silencioso al abrir la web para evitar colisiones de sesión y credenciales hardcodeadas en fase de prototipo.

### 2.2. Funcionalidades Planificadas (A Futuro)
*   **RF-09: Estandarización Cromática y Estilística de Gráficas:** Establecer una paleta de colores institucional rígida (azul corporativo, gris neutro y colores curados RER) y espaciados responsivos estandarizados para que todos los gráficos sean consistentes visualmente.
*   **RF-10: Modal de Ampliación de Gráficos (Zoom/Lightbox):** Botón integrado en la tarjeta del gráfico para expandir el SVG interactivo en un modal de pantalla completa, permitiendo una inspección detallada de las barras, leyendas y puntos de datos.
*   **RF-11: Descarga Multiformato Avanzada:** Habilitar la exportación del gráfico en formatos **PNG de alta resolución**, **PDF vectorizado para informes** y **SVG original**, además de descargar la tabla de datos subyacente en formato **Microsoft Excel (.xlsx)**.
*   **RF-12: Filtros Locales Integrados (Filtros en Caliente):** Incorporar controles de filtrado (inputs de búsqueda, selectores rápidos de tecnologías o rangos) en la misma tarjeta del gráfico para refinar los datos visualizados en memoria sin afectar el hilo conversacional del chat ni el sidebar general.

---

## 3. Requisitos No Funcionales (RNF)

*   **RNF-01: Rendimiento del Backend (SLA-01):** La inyección del primer token de respuesta del LLM y el enrutador de resiliencia del MCP deben responder en menos de **8.0 segundos** para consultas complejas.
*   **RNF-02: Rendimiento Local del Mock (SLA-02):** Si la base de datos o el servidor MCP remoto fallan, el mock de resiliencia local debe responder con datos consistentes y estructurados en menos de **500 ms** sin interrumpir la experiencia.
*   **RNF-03: Resiliencia ante Desconexión:** El backend debe tolerar la desconexión del servidor MCP corporativo (`http://10.10.17.216:8001`), conmutando automáticamente al mock local resiliente en menos de **100 ms** (RNF-RESIL-01).
*   **RNF-04: Confidencialidad y Seguridad:** Bajo ninguna circunstancia el sistema debe exponer credenciales de base de datos Oracle, contraseñas de API en texto plano, tokens JWT ni URLs internas de túneles en los mensajes del chat o elementos visuales.
*   **RNF-05: Trazabilidad Integral (RNF-LOG-01):** Registro estructurado en `log_uso.txt` de: usuario temporal, fecha/hora exacta, modelo de LLM activo, tokens de entrada, tokens de salida y consulta original efectuada para auditoría interna.
*   **RNF-06: Control de Consumo Justo (Rate Limit):** Límite máximo de **50 consultas en 10 minutos** por sesión de usuario para mitigar abusos de la API Key corporativa.
*   **RNF-07: Tolerancia a Formatos de Datos:** El parser de Markdown del frontend debe inspeccionar la estructura del código JSON de forma agnóstica para renderizar gráficos y datasets interactivos, aun si el LLM no genera la etiqueta de lenguaje exacta (ej: usando `json` en vez de `json-chart`).
*   **RNF-08: Portabilidad y Estándares:** Los componentes interactivos (React, TypeScript, Tailwind) y los datos JSON deben estructurarse de modo que faciliten su futura migración/reutilización en un portal unificado basado en **Angular 18+**.
