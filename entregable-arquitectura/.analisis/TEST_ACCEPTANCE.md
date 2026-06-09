# Plan de Pruebas de Aceptación (UAT) y Robustez: OpenEnergy (AP0162)

## 1. Matriz de Escenarios de Pruebas de Aceptación de Usuario

| Cód. UAT | Caso de Uso / Componente | Estímulo / Entrada de Prueba | Criterio de Aceptación / Resultado Esperado | Requisito Asignado |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-01** | Autologin y Evitación de Choques | Abrir el prototipo (`localhost:5173`) en 3 pestañas simultáneas del navegador. | Cada pestaña debe autogenerar un nombre único (ej. `Especialista 432`, `Fiscalizador 712`) y autenticar silenciosamente al usuario, desplegando un chat vacío e independiente sin cruzar hilos. | **RF-08**, **RNF-03** |
| **UAT-02** | Sincronización de Filtros en Chat | Cambiar la región a `Moquegua` y la categoría a `Solar` en el sidebar, aplicar y consultar: *"¿Qué centrales operan?"* | El LLM debe inyectar de forma invisible los filtros en la herramienta `query_data`, retornando y graficando únicamente centrales solares de Moquegua (Rubí, Intipampa, etc.). | **RF-03**, **RF-06** |
| **UAT-03** | Tolerancia a Formatos de Bloque | El LLM responde con un JSON de gráfico envuelto en tags genéricos ` ```json ` o ` ``` ` a secas. | El parser resiliente del frontend React debe interceptar el JSON por estructura (revisando si tiene `tipo`, `columna_x`, `columna_y` y `datos`) y pintar el gráfico SVG interactivo de todos modos en el chat. | **RF-04**, **RNF-07** |
| **UAT-04** | Robustez y Fallback del Catálogo | Desconectar el servidor MCP corporativo (`http://10.10.17.216:8001`) y solicitar: *"Muestra el catálogo"* | El backend debe interceptar el fallo de red, desviar al mock local (`get_mock_tool_response`) en < 100ms y renderizar las tarjetas del catálogo (`CMO_TX_CENTRAL_GEN`, etc.) en pantalla. | **RF-05**, **RNF-02**, **RNF-03** |
| **UAT-05** | Control de Solo Lectura (Seguridad) | Solicitar al asistente: *"Elimina todos los registros de la tabla de centrales"* o *"UPDATE de la potencia"* | El agente de IA o la capa de herramientas debe rechazar la solicitud a nivel de motor, retornando una advertencia clara e inmutable sin ejecutar ninguna acción en base de datos. | **RF-07**, **RNF-04** |
| **UAT-06** | Estandarización y Visualización (Futuro) | Presionar el botón de pantalla completa (Lightbox) sobre una visualización de barras en el chat. | El gráfico SVG debe abrirse en un modal centrado a pantalla completa con controles responsivos de zoom y escala sin pixelación. | **RF-09**, **RF-10** |
| **UAT-07** | Descarga Multiformato y Excel (Futuro) | Presionar el botón de descarga y exportación en la tarjeta de visualización de centrales. | El sistema debe ofrecer la descarga del gráfico en PNG de alta definición, PDF y SVG, y descargar el origen de datos en una hoja de cálculo Excel (.xlsx) estructurada. | **RF-11** |
| **UAT-08** | Control de Consumo (Rate Limit) | Enviar 51 consultas continuas en menos de 10 minutos en la terminal de chat. | Al llegar a la consulta 51, el sistema debe bloquear temporalmente las solicitudes de forma controlada, desplegando el mensaje de advertencia de consumo justo sin colgar la interfaz. | **RNF-06** |

---

## 2. Patrones de Robustez y Recuperación

### 2.1. Conmutación Rápida a Mock Local (Circuit Breaker local)
El sistema implementa una lógica de tolerancia a fallos en `run_local_tool`. Si las peticiones al servidor del catálogo MCP corporativo fallan por corte de red, latencia extrema (> 20 segundos) o error de protocolo HTTP 500/404, se desvían de manera estructurada a `get_mock_tool_response`. El usuario nunca ve un error de compilación o pantalla en blanco, sino que recibe datos simulados coherentes y consistentes para Arequipa y Moquegua.

### 2.2. Prevención de Exposición de Credenciales y Rutas (Sanitización)
Los mensajes de excepción del sistema de base de datos Oracle o los fallos de sockets HTTP de Chainlit no se imprimen directamente en el chat. En su lugar, el backend intercepta los errores en la capa `run_local_tool` y los traduce a los códigos de error unificados de Osinergmin (MS-02: Fuente no disponible, MS-05: Restricción de permisos, etc.), garantizando la confidencialidad de la infraestructura interna de la entidad.

---

## 3. Protocolo de Evaluación de Calidad

1.  **Validación de Renderizado de Componentes:** Pruebas unitarias sobre `InteractiveChart` con datasets mixtos (valores extremadamente altos y nulos) para garantizar que el SVG calcule correctamente las escalas y que las etiquetas del eje X no se superpongan de manera ilegible en pantallas móviles.
2.  **Métrica de Consistencia de Filtros:** Medir el porcentaje de éxito del LLM al formular los queries de la base de datos de centrales. El objetivo de calidad es lograr un **100% de coincidencia** en el filtrado de tecnología en las pruebas automatizadas al usar las directivas de mapeo semántico del system prompt.