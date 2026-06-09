# Hoja de Ruta del Proyecto & Plan de Sprints: OpenEnergy (AP0162)

## 1. Cronograma de Desarrollo por Componentes

### 🏃 Sprint 1: Autenticación, Login Temporal y WebSocket (COMPLETADO)
*   **Enfoque:** Establecer el canal de comunicación bidireccional mediante WebSockets entre el cliente de React (Vite) y el backend de Python (Chainlit). Implementar el autologin silencioso de usuarios temporales analíticos únicos para evitar el choque de hilos y sesiones.
*   **Entregables por Componente:**
    *   *Frontend:* Integración de `@chainlit/react-client` y `useAuth` en `App.tsx`. Formulario de login convencional reemplazado por animación de carga silenciosa de analistas temporales (`Especialista 964`, etc.).
    *   *Backend:* Función `@cl.password_auth_callback` adaptada en `app.py` para aceptar usuarios al vuelo de forma dinámica e independiente.
    *   *Hito de Control:* Dos pestañas del navegador pueden abrir la aplicación simultáneamente y obtener hilos de conversación y tokens JWT separados sin interferencia mutua.

### 🏃 Sprint 2: Catálogo Dinámico, Gráficos Interactivos y Mock Resiliente (COMPLETADO)
*   **Enfoque:** Diseñar y habilitar la visualización interactiva de gráficos vectoriales SVG en la burbuja de chat y tarjetas dinámicas de datasets para el catálogo. Implementar la resiliencia local en el backend en caso de caída de la red o desconexión del servidor MCP.
*   **Entregables por Componente:**
    *   *Frontend:* Creación del componente `InteractiveChart.tsx` (SVG nativo con tooltips HTML reactivos). Actualización de `App.tsx` con un parser de código Markdown JSON resiliente a la sintaxis del LLM.
    *   *Backend:* Implementación de `get_mock_tool_response` en `app.py` que provee datos consistentes y simula filtros para centrales eléctricas y grifos. Detección automática en `app.py` de la herramienta `get_catalogo_datos` para inyectar bloques `json-datasets`.
    *   *Hito de Control:* El usuario puede consultar centrales operativas, ver y descargar el gráfico interactivo SVG, y explorar las tarjetas dinámicas del catálogo de base de datos aun si el servidor MCP remoto está apagado.

### 🏃 Sprint 3: Estandarización de Gráficos, Modal y Descargas Avanzadas (EN DESARROLLO)
*   **Enfoque:** Desarrollar los requerimientos de estandarización visual corporativa y facilidad de exportación de visualizaciones.
*   **Entregables por Componente:**
    *   *Frontend:*
        *   Implementar tokens de diseño (colores corporativos de Osinergmin, tipografías y espaciados fijos) en `InteractiveChart.tsx`.
        *   Creación del modal de ampliación (Lightbox) de gráficos interactivos a pantalla completa.
        *   Integración de librerías en caliente (o lógica local) para exportar el gráfico SVG a imágenes de alta definición PNG, informes PDF vectorizados, y descargar la tabla de datos subyacente en formato Microsoft Excel (.xlsx).
    *   *Backend:*
        *   Actualizar la herramienta de gráficos del backend para admitir paletas cromáticas institucionales adicionales y formatear los datos exportables en Excel de manera estructurada.
    *   *Hito de Control:* El usuario puede hacer clic en un gráfico de barras, verlo expandido en un modal y descargarlo como PDF o exportar su origen de datos a un archivo Excel (.xlsx) listo para hojas de cálculo.

### 🏃 Sprint 4: Filtros en Caliente de Visualización y Seguridad de Consulta
*   **Enfoque:** Dotar a las visualizaciones de autonomía mediante filtros en caliente locales y robustecer los mecanismos de seguridad y prevención de inyección en las consultas del piloto.
*   **Entregables por Componente:**
    *   *Frontend:* Incorporación de inputs y checkboxes de filtrado rápido dentro de la propia tarjeta del gráfico en `InteractiveChart.tsx` para refinar las barras en memoria sin requerir un nuevo mensaje de chat.
    *   *Backend:* Sanitizador de consultas SQL e inyecciones de código en `app.py` que evalúe y limpie de forma estricta los parámetros del WHERE enviados a la herramienta `query_data`.
    *   *Hito de Control:* Si el usuario solicita grifos, puede filtrarlos en caliente en pantalla directamente desde el gráfico por provincia, y si intenta enviar una consulta SQL maliciosa, el sistema la bloquea en menos de 50 ms.

---

## 2. Dependencias de Bloqueo Críticas (Ruta Crítica)
1.  **Mapeo Semántico del Prompt (Semana 2 - Resuelto):** El LLM depende de las reglas inyectadas en su prompt de sistema para traducir "Solar" o "Hidráulica" a valores SQL correctos (`TI_TIPO_CENTRAL = 'CENTRAL SOLAR'`). Si estas reglas fallaban, `query_data` devolvía datos vacíos, bloqueando la generación de gráficos.
2.  **Soporte de Formato en Frontend (Semana 2 - Resuelto):** La visualización interactiva dependía de que el LLM generara exactamente la etiqueta `json-chart`. La implementación del parser resiliente de JSON estructura-compatible mitigó este riesgo de bloqueo, permitiendo que cualquier LLM dibuje el gráfico.
3.  **Librerías de Exportación en React (Semana 3 - Crítica):** La descarga en PNG/PDF y exportación a Excel en el cliente de React requiere empaquetadores ligeros y compatibles para evitar que el bundle de Vite se vuelva pesado o falle en su compilación.