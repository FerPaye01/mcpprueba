**Dataset Context Optimization**
Tabular datasets can easily scale to millions of rows, making it highly inefficient to pass raw data directly into the LLM's prompt window. Doing so introduces massive token costs, increases latency, and risks context saturation. Instead, **extract and serialize structural metadata, data distributions (summary statistics), and a few sample rows (e.g., the first 5 rows)**. Providing this concise structural context allows the LLM to write highly accurate plotting code without needing the full dataset. 

**Handling Session-Based State**
Deploying data-intensive assistants requires strict multi-user concurrency isolation. Standard Python web frameworks use shared threads, meaning global variables will cause data corruption and collisions across concurrent users. **Always store your datasets and intermediate states using `cl.user_session`**. 
*   **Dataframes:** Store the loaded `pd.DataFrame` via `cl.user_session.set("dataset", df)` upon file upload. This isolates the data cryptographically to the duration of that specific user's active WebSocket session.
*   **Memory Management:** Transient plot objects (like `io.BytesIO` streams) should be re-evaluated on every request, and previous references should be cleared to prevent memory overhead.

**Defining Custom Plotting Tools & Safe Execution**
The LLM acts as the planner, while your Chainlit application acts as the local executor. You will define the tool using either Gemini's `types.Tool` (native Python functions) or OpenRouter's OpenAI-compatible JSON schemas.
When executing the LLM-generated plotting code:
*   **Build a safe execution sandbox:** Restrict the execution environment by passing an isolated local scope. Bind safe built-ins, required libraries (`pd`, `plt`), and the active user's dataframe (`df = cl.user_session.get("dataset")`) into the `sandbox_globals` dictionary before executing.
*   **Human-in-the-Loop (HITL):** Because executing unstructured code carries operational risks, consider adding a HITL step that pauses tool execution and waits for explicit user approval via the UI before running the Python code.

**Rendering Inline Images with Minimal Friction**
A common UI friction point in asynchronous Chainlit apps is out-of-order rendering, where tool steps resolve out of order and appear *after* the final text answer. **To ensure proper chronological synchronization, you must execute tool calls sequentially inside a unified coroutine and explicitly `await` step creations using `cl.Step` or the `@cl.step` decorator**.

For the actual visual rendering, Chainlit offers distinct elements depending on your interactivity and performance needs:
*   **`cl.Pyplot` (Matplotlib):** Compiles a static image on the server and transfers pixel maps to the client. **Use this for high-performance static rendering** that avoids client-side JavaScript overhead.
*   **`cl.Plotly`:** Serializes full layout configurations to the browser, allowing dynamic zooming, hover tools, and legend toggling. Best for exploratory data views. 
*   **`cl.Image`:** If you want to avoid browser lag entirely but still use Plotly's rendering engine, you can **convert interactive Plotly charts into static PNG bytes on the server using Kaleido**, and then serve those raw bytes using the lightweight `cl.Image` element.

Implementar un paso de aprobación humana (HITL) en Chainlit es una medida fundamental para mitigar los riesgos operativos que conlleva la ejecución de código no estructurado en tiempo real. 

Para diseñar este flujo de aprobación dentro de tu aplicación, puedes seguir estas recomendaciones:

*   **Pausar la ejecución:** Cuando el LLM genere la solicitud para usar la herramienta (por ejemplo, ejecutar el código de generación de gráficos), tu aplicación debe pausar temporalmente la ejecución y serializar el contexto actual.
*   **Solicitar aprobación explícita en la interfaz (UI):** Debes requerir la confirmación del usuario antes de que el código se ejecute localmente. Para hacer esto con una fricción mínima, puedes crear botones interactivos directamente en el chat enviando objetos `cl.Action` como parte de un mensaje a través del argumento `actions`. Además, Chainlit dispone de elementos como `AskActionMessage` diseñados específicamente para pausar el flujo y esperar la acción del usuario.
*   **Procesar la decisión del usuario:** Utiliza el decorador `@cl.action_callback` vinculado al nombre del botón (o acción) para escuchar y capturar la decisión que toma el usuario en la interfaz.
*   **Gestión estricta de cancelaciones:** Si el usuario decide rechazar o cancelar la ejecución del código, la aplicación debe abortar el proceso inmediatamente. Es fundamental que el sistema respete esta decisión y no intente reintentar la llamada a la herramienta de forma automática.

**Convertir gráficos de Plotly usando Kaleido:** 
Para entornos donde el rendimiento del navegador es limitado, puedes usar Kaleido en el servidor para **convertir la figura interactiva de Plotly en bytes sin procesar** (por ejemplo, en formato PNG llamando al método `to_image`, el cual devuelve un objeto de bytes). Una vez convertida, puedes servir la imagen directamente enviándola a la interfaz a través del elemento ligero **`cl.Image`** de Chainlit.

**Diferencias al definir herramientas (Gemini vs. OpenRouter):**
*   **Gemini:** Envuelve las declaraciones de funciones dentro de un objeto unificado **`types.Tool`**. Te permite proporcionar directamente funciones nativas de Python (utilizando *type hints* y *docstrings*) para que el SDK autogenere el esquema, o usar un sistema basado en tipos de *Protocol Buffer*. Cuando el modelo solicita una herramienta, emite un objeto **`functionCall`**.
*   **OpenRouter:** Utiliza el protocolo estándar de OpenAI, donde las herramientas se definen utilizando un **esquema JSON anidado** bajo la estructura `{"type": "function", "function": {...}}` y los argumentos van bajo la clave `parameters`. Al ejecutar una solicitud de herramienta, OpenRouter emite la petición dentro de un array llamado **`tool_calls`**.

**Enviar botones de confirmación con `cl.Action`:**
Puedes integrar botones en la interfaz de usuario de Chainlit definiendo la acción y pasándola como parte de un mensaje. Esto se hace enviando objetos `cl.Action` mediante el argumento **`actions`** en tu mensaje. Para escuchar y procesar la decisión cuando el usuario hace clic, debes conectar ese botón a una función de tu código Python utilizando el decorador **`@cl.action_callback("nombre_del_boton")`**.

**Usar `AskActionMessage` para pausar el chat:**
`AskActionMessage` es un elemento de la API de Chainlit que se categoriza bajo las funciones para solicitar interacción ("Ask User"). Su propósito (como se trató en nuestra conversación) es **pausar temporalmente el flujo de ejecución** del backend y esperar explícitamente a que el usuario interactúe tomando una decisión en la interfaz antes de que el código reanude su procesamiento.

**Abortar la ejecución si el usuario cancela:**
Durante un flujo de validación humana (HITL), si el usuario decide rechazar o cancelar la ejecución del código, la aplicación **debe respetar esa decisión y abortar la ejecución de inmediato**. La principal regla de seguridad aquí es asegurarse de que el sistema se detenga y no intente reintentar la llamada a la herramienta de forma automática.