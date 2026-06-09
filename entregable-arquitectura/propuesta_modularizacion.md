# Propuesta de Modularización y Limpieza de Código: Backend OpenEnergy

Actualmente, el backend de la aplicación (`agente-mcp/app.py`) es un archivo monolítico de aproximadamente **1,600 líneas de código**. Contiene desde la lógica de servidor de Chainlit y eventos de WebSocket, hasta definiciones de prompts de sistema, autenticación de usuarios, enrutamiento de LLMs, generación automática de gráficos con Plotly, y parsers de payloads JSON.

Esta estructura monolítica incrementa la deuda técnica, dificulta las pruebas unitarias y complica el mantenimiento a largo plazo. A continuación se presenta el plan de reorganización modular para estructurar el proyecto bajo principios de **Responsabilidad Única (SRP)** y eliminar el código espagueti.

---

## 🏛️ Nueva Estructura Modular Propuesta

Se propone fragmentar el monolito en módulos especializados dentro de la carpeta `agente-mcp/`:

```
agente-mcp/
│
├── app.py                      # Punto de entrada principal (Solo eventos Chainlit)
├── config.py                   # Carga de variables de entorno, modelos y prompts
├── auth.py                     # Autenticación de usuarios, roles y soporte OIDC/Keycloak
├── llm_router.py               # Enrutador resiliente de LLMs (Gemini, OpenRouter, etc.)
├── tools.py                    # Declaración de herramientas del sistema y enrutador de ejecución
├── osam_gateway.py             # [Existente] Compilador SQL, inyección de RLS y DuckDB
├── semantic_registry.py        # [Existente] Cliente MCP (SSE/REST) y catálogo de respaldo
├── visualizer.py               # Generador de gráficos fallback (Plotly) y parser/auto-repair de JSON
└── utils.py                    # Funciones utilitarias (Normalización, cuotas, log de uso)
```

---

## 🔍 Descomposición de Responsabilidades

### 1. `app.py` (Orquestador de Sockets y Eventos)
Debe ser un archivo minimalista (< 150 líneas) enfocado exclusivamente en inicializar Chainlit y enrutar los eventos de WebSocket:
*   `@cl.on_chat_start`: Delega a `auth.py` y carga la interfaz.
*   `@cl.on_settings_update`: Actualiza los filtros de sesión.
*   `@cl.on_message`: Captura el mensaje, llama a `llm_router.py` para procesarlo, y pasa el resultado a `visualizer.py` para renderizar o auto-reparar la UI.

### 2. `config.py` (Configuraciones y Prompts de Sistema)
Centraliza las constantes y variables del entorno:
*   Definición del `SYSTEM_PROMPT` base y reglas lógicas de OSAM.
*   Variables de entorno (`GEMINI_API_KEY`, `MCP_SERVER_URL`, etc.).
*   Modelos autorizados y configuraciones por defecto.

### 3. `auth.py` (Control de Acceso y Roles)
Aísla el flujo de seguridad, facilitando el cambio entre el mock de desarrollo y Keycloak:
*   Mapeo de perfiles (`DICCIONARIO_ROLES`).
*   Decorador `@cl.password_auth_callback` actual.
*   Lógica preparada para `@cl.oauth_callback` de Keycloak.

### 4. `llm_router.py` (Enrutamiento de Inteligencia Artificial)
Gestiona la comunicación con los proveedores de LLMs con políticas de reintentos y tolerancia a fallos:
*   Función `stream_llm_response` y cliente asíncrono de OpenAI.
*   Control de fallbacks de modelos (ej: si falla `gemini-3.1-flash-lite`, reintentar con `gemini-2.5-flash`).
*   Inyección dinámica de filtros activos de sesión en el prompt.

### 5. `tools.py` (Definición y Ejecución de Herramientas)
Registra las herramientas disponibles para el LLM y gestiona su ejecución:
*   Declaración de esquemas JSON de las herramientas (`query_data_osam`, `get_catalogo_datos`, `crear_grafico`).
*   Función `execute_tool(name, args)` que redirige la llamada al MCP real (`semantic_registry.py`) o al gateway local (`osam_gateway.py`).

### 6. `visualizer.py` (Capa Gráfica e Interpretación del Metamodelo)
Centraliza la lógica visual de respaldo y validación de componentes del frontend:
*   Funciones `try_generate_chart` y `try_generate_chart_json` utilizando Plotly.
*   Extractor de bloques markdown ```json-osam y ```json-chart.
*   **Mecanismo de Auto-Reparación** de esquemas JSON y casing antes del renderizado.

### 7. `utils.py` (Utilidades Genéricas del Sistema)
Funciones auxiliares puras y sin dependencias pesadas:
*   `normalize_text` (Limpieza de caracteres especiales).
*   `is_rate_limited` (Control de consumo justo de 50 preguntas/10 min).
*   `log_usage` (Registro de métricas en `log_uso.txt`).

---

## 📈 Beneficios de esta Arquitectura
1.  **Facilidad de Pruebas (Unit Testing):** Ahora es posible testear el compilador SQL (`osam_gateway.py`) o el parser de gráficos (`visualizer.py`) de forma aislada sin tener que simular un servidor Chainlit activo o un flujo de WebSocket.
2.  **Mantenibilidad:** Si se necesita cambiar el proveedor de identidad de contraseñas de Chainlit a Keycloak, solo se requiere modificar `auth.py` y `config.py`.
3.  **Legibilidad:** Cualquier desarrollador nuevo puede comprender el flujo de mensajes analizando las pocas líneas de `app.py`, en lugar de descifrar un archivo de 1,600 líneas con múltiples bucles anidados.
