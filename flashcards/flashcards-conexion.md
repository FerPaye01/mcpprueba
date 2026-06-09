# Flashcards: Conexión y Sincronización en OpenEnergy

Este juego de tarjetas de estudio (flashcards) resume las soluciones técnicas y de red implementadas para la conexión dinámica, el control de ciclo de vida del chat y la compatibilidad con Gemini.

---

### Tarjeta 1: Detección Dinámica de la URL del Servidor
**P:** ¿Cómo evitar que un frontend de React hardcodeado en `localhost:8080` falle con errores de red o de CORS (`ERR_FAILED`) cuando se accede desde otra PC de la red corporativa?
**R:**
```typescript
// frontend/src/api/chainlitClient.ts
import { ChainlitAPI } from '@chainlit/react-client';

// Resuelve dinámicamente el protocolo e IP del servidor anfitrión, manteniendo el puerto 8080 del backend.
const CHAINLIT_SERVER_URL = `${window.location.protocol}//${window.location.hostname}:8080`;

export const apiClient = new ChainlitAPI(CHAINLIT_SERVER_URL, "webapp");
```

---

### Tarjeta 2: Limpieza de Historial sin Bloqueo de Carga (Loading Lock)
**P:** ¿Cómo reiniciar/limpiar una conversación en el backend y frontend de Chainlit sin romper la máquina de estados del SDK de React (lo que dejaría la variable `loading = true` bloqueando futuros mensajes)?
**R:**
```typescript
// frontend/src/ui/App.tsx
const handleClearChat = () => {
  try {
    clear(); // Borra los mensajes de la interfaz localmente
    disconnect(); // Cierra el WebSocket actual para anular el turno en curso
    
    // Inicia una nueva conexión websocket tras un breve delay, levantando una sesión backend limpia
    setTimeout(() => {
      connect({ userEnv: {} });
    }, 100);
  } catch (err) {
    console.error("Error clearing chat session:", err);
  }
};
```

---

### Tarjeta 3: Captura de la Firma de Pensamiento (Thought Signature) de Gemini 3.x
**P:** ¿Cómo extraer la firma obligatoria de razonamiento (`thought_signature`) de Gemini 3.x del chunk del stream del SDK de OpenAI de Python para evitar el error `400 INVALID_ARGUMENT` en el siguiente turno de herramienta?
**R:**
```python
# agente-mcp/app.py (Bucle de acumulación de stream chunks)
if delta.tool_calls:
    for tc in delta.tool_calls:
        # ... acumulación estándar de id, name y arguments ...
        
        # Extraer thought_signature del model_extra del SDK de OpenAI
        tc_extra = getattr(tc, "model_extra", None) or {}
        extra_content = tc_extra.get("extra_content") or getattr(tc, "extra_content", None)
        if extra_content:
            if "extra_content" not in tool_calls_chunks[idx]:
                tool_calls_chunks[idx]["extra_content"] = {}
            for k, v in extra_content.items():
                if isinstance(v, dict) and k in tool_calls_chunks[idx]["extra_content"]:
                    if not isinstance(tool_calls_chunks[idx]["extra_content"][k], dict):
                        tool_calls_chunks[idx]["extra_content"][k] = {}
                    tool_calls_chunks[idx]["extra_content"][k].update(v)
                else:
                    tool_calls_chunks[idx]["extra_content"][k] = v
```

---

### Tarjeta 4: Re-sincronización Automática de Datasets e Inyección de Metadatos
**P:** ¿Cómo garantizar que el LLM pueda llamar a la herramienta `query_data` (la cual requiere `schema` e `id_catalogo` obligatorios) en el primer mensaje tras limpiar la conversación?
**R:**
```typescript
// 1. Sincronizar desde el frontend en la reconexión (App.tsx)
useEffect(() => {
  if (connected) {
    const activeEnergies = Object.entries(filters.energyMatrix)
        .filter(([_, active]) => active).map(([name]) => name);
        
    updateChatSettings({
      ubicacion: filters.geography,
      periodo: "Todos",
      categoria: activeEnergies,
      entidad: [],
      datasets_activos: importedDatasets.map(d => ({
        table_name: d.title,
        schema: d.schema || '',
        id_catalogo: d.id_catalogo || 0
      }))
    });
  }
}, [connected]);
```
```python
# 2. Inyectar metadatos completos en el System Prompt del Backend (app.py)
datasets_activos = filtros_activos.get("datasets_activos", [])
datasets_info = []
for ds in datasets_activos:
    if isinstance(ds, dict):
        table_name = ds.get("table_name") or ds.get("title") or ""
        schema = ds.get("schema") or "ES_DATGOB_CV"
        id_cat = ds.get("id_catalogo") or 0
        datasets_info.append(f"{table_name} (Esquema: {schema}, ID Catálogo: {id_cat})")
    else:
        datasets_info.append(str(ds))

datasets_str = ", ".join(datasets_info) if datasets_info else "Ninguno"
# ... filtros_context se añade al mensaje del sistema original ...
```

---

### Tarjeta 5: Detector y Generador Automático de Cartas de Datasets
**P:** ¿Cómo escanear quirúrgicamente la respuesta de texto del LLM para inyectar dinámicamente bloques estructurados de cartas de datasets (`json-datasets`) si se mencionan tablas o identificadores del catálogo real?
**R:**
```python
# agente-mcp/app.py
# Escaneo de palabras clave y números de ID en el texto de salida del LLM
numeros = re.findall(r"\b\d{4,5}\b", full_text)
palabras = re.findall(r"\b[A-Za-z0-9_]{5,}\b", full_text)
tablas_agregadas = set()
datasets_list = []

# Coincidencia con catálogo cargado en memoria
for num in numeros:
    num_int = int(num)
    for item in catalogo_completo:
        id_cat = item.get("ID_CATALOGO_DATO")
        if id_cat and int(id_cat) == num_int:
            # Construir dict e inyectar en el array
            datasets_list.append({
                "title": item.get("NO_TABLA"),
                "description": item.get("DE_TABLA") or "Tabla de datos.",
                "format": "SQL Table",
                "license": "Osinergmin",
                "organization": "Gobernanza de Datos",
                "schema": item.get("NO_ESQUEMA_ORIGEN"),
                "id_catalogo": id_cat
            })
```

---

### Tarjeta 6: Router de Resiliencia y Fallback de Modelos
**P:** ¿Cómo configurar un bucle estructurado de llamadas a LLM que intente utilizar modelos prioritarios (por ejemplo, Gemini 3.1 con 500 peticiones) y pase secuencialmente a respaldos en caso de errores de cuota (429)?
**R:**
```python
# agente-mcp/app.py
async def stream_llm_response(messages, tools=None):
    models = ["gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
    for idx, model in enumerate(models):
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    await asyncio.sleep(4) # Delay para limpiar cuota por segundo
                # Intentar crear completado en streaming
                stream = await client.chat.completions.create(model=model, messages=messages, stream=True)
                return stream, model
            except Exception as e:
                is_rate_limit = "429" in str(e) or "rate" in str(e).lower()
                if is_rate_limit and attempt < max_retries - 1:
                    continue
                if idx == len(models) - 1:
                    raise e
                break # Pasa al siguiente modelo de respaldo
```

---

### Tarjeta 7: Generador Automático de Gráficos (Fallback Heurístico)
**P:** ¿Cómo programar una rutina que genere y renderice automáticamente un gráfico moderno en Plotly basado en los datos almacenados en la sesión si el usuario pide una visualización de forma implícita (ej. "tendencia", "grafica") y el LLM no llamó a la herramienta local?
**R:**
```python
# agente-mcp/app.py
# Al finalizar el turno, si no se generó gráfico y hay datos del catálogo activos
chart_keywords = ["grafic", "tendencia", "curva", "evolucion", "gráfico"]
last_result = cl.user_session.get("last_tool_result")
chart_already_generated = cl.user_session.get("chart_generated_in_turn", False)

if not chart_already_generated and any(kw in clean_query for kw in chart_keywords) and isinstance(last_result, list):
    # Genera la imagen y metadatos Plotly dinámicamente
    chart_path = try_generate_chart(last_result, message.content)
    chart_json = try_generate_chart_json(last_result, message.content)
    if chart_json and chart_path:
        image_element = cl.Image(path=chart_path, name="tendencia", display="inline")
        await cl.Message(content="Gráfico generado:", elements=[image_element]).send()
```

---

### Tarjeta 8: Exposición del Servidor de Desarrollo en Red Corporativa
**P:** ¿Cómo configurar el servidor local de desarrollo de Vite para que escuche en toda la red corporativa (`0.0.0.0`) y admita acceso externo en el puerto `5173`?
**R:**
```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Expone el servidor en la IP LAN/Corporativa
    port: 5173       // Puerto por defecto
  }
})
```
