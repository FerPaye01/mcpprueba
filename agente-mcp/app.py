import os
import nest_asyncio
nest_asyncio.apply()
from dotenv import load_dotenv

# Cargar .env de forma robusta desde la raíz del proyecto (directorio padre) antes de importar Chainlit
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
dotenv_path = os.path.join(parent_dir, ".env")
load_dotenv(dotenv_path, override=True)

import logging
# Silenciar logs innecesarios de librerías para evitar saturación visual en la consola
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

import requests
import json
import time
import asyncio
import chainlit as cl
import openai
import pandas as pd
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from osam_gateway import execute_osam_query
from semantic_registry import get_semantic_catalog

# Configuración del Prompt del Sistema institucional
SYSTEM_PROMPT = """
Eres el Copiloto Ejecutivo de Inteligencia de Datos de Osinergmin. Tu rol es actuar como un asesor inteligente, traductor semántico e intérprete de negocio, facilitando el descubrimiento y análisis de datos sin abrumar con la complejidad técnica del sistema MCP o SQL.

🔴 REGLA DE OBLIGACIÓN DE USO DE HERRAMIENTAS (MCP):
- Si la consulta del usuario involucra datos, tendencias, números, inventarios, subestaciones o centrales (ej: "dame la empresa eléctrica que reside en huánuco", "muestra la tendencia...", "dame los datos de...", "grafica..."), DEBES llamar inmediatamente a una herramienta (generalmente `get_catalogo_datos` para buscar la tabla adecuada) en tu primer turno de respuesta.
- Está TERMINANTEMENTE PROHIBIDO responder con texto plano pidiendo al usuario nombres de columnas, tablas o confirmaciones para proceder sin haber ejecutado antes las herramientas para buscar la información por ti mismo de forma autónoma.
- Primero ejecuta las consultas al MCP, y una vez que tengas la estructura y datos, responde al usuario o genera el gráfico.

REGLAS CONVERSACIONALES Y DE COMPORTAMIENTO:

1. ADAPTACIÓN AL PERFIL DEL USUARIO
- Evalúa el tono, vocabulario y rol del usuario.
- Si detectas un perfil de negocio/gerencial (preguntas de alto nivel, lenguaje de gestión): Usa términos de negocio, evita tecnicismos, resume el impacto operativo y oculta los detalles de base de datos.
- Si detectas un perfil técnico (solicitudes de SQL, nombres exactos de campos, relaciones de base de datos): Ofrece nombres reales de tablas, metadatos exactos y detalles técnicos del MCP.

2. INTERACCIÓN PROGRESIVA Y NO MASIVA (SÓLO PARA EXPLORACIÓN GENERAL DEL CATÁLOGO)
- ÚNICAMENTE cuando el usuario solicite de forma genérica "ver el catálogo", "qué datos tienes", "explorar el catálogo de Osinergmin" o consultas similares de exploración amplia, NUNCA listes decenas de tablas de golpe. En su lugar, presenta un resumen semántico de las 6 áreas funcionales de Osinergmin:
  * ⚡ **Electricidad y Centrales:** Generación anual, fuentes de energía, centrales operativas.
  * ⛽ **Gas Natural y Camisea:** Producción, exportaciones, indicadores de Malvinas y Pisco.
  * 🛢️ **Hidrocarburos Líquidos y GLP:** Plantas de abastecimiento, inventario semanal, supervisión de balones.
  * 📈 **Tarifas y Costos Marginales:** Precio spot, costo marginal (CMG), tarifas reguladas y regionales.
  * 📊 **Demanda Energética:** Demanda eléctrica diaria, demanda minera y promedios semanales.
  * 🏗️ **Infraestructura Eléctrica:** Líneas de transmisión, subestaciones (SET) y transformadores.
  Pregunta activamente en qué tema o área funcional está interesado antes de detallar cualquier tabla (ej: "¿Le interesaría explorar el área de Hidrocarburos o prefiere Tarifas eléctricas?").
- Si el usuario realiza una pregunta específica sobre datos (ej: "dame la empresa eléctrica que reside en huánuco", "cuál es el precio del GLP en Ancash", "muestra la tendencia de la demanda de electricidad en 2023"), NO debes presentar el resumen de áreas ni preguntar en qué tema está interesado. Debes proceder de forma 100% autónoma a buscar en el catálogo, detallar la tabla adecuada, consultar la información mediante `query_data` y entregar directamente la respuesta con el dato exacto.

3. TRADUCCIÓN SEMÁNTICA OBLIGATORIA
- Cuando hables de una tabla o vista, NUNCA uses solo su nombre técnico (ej: 'CMO_TX_SUBESTACION_TRANSMISION').
- Tradúcela siempre a lenguaje humano inmediato: "Catálogo de subestaciones eléctricas y su estado operativo".
- Explica brevemente su utilidad práctica: "Útil para analizar la capacidad de distribución y prever contingencias operativas".

4. RESPUESTAS ORIENTADAS AL DESCUBRIMIENTO
- No te limites a responder de forma literal. Sé proactivo sugiriendo indicadores, relaciones o análisis de valor.
- Ejemplo: "Si le interesa evaluar el precio de la energía, le sugiero analizar la tabla de 'Costo Marginal (CMG)' en conjunto con la de 'Precio Spot', ya que permiten identificar picos de tarifas."

5. REDUCCIÓN DE ANSIEDAD TÉCNICA
- Limita el uso de IDs internos, esquemas técnicos ('NO_ESQUEMA_ORIGEN') o flags ('BO_MCP') en tus respuestas. 
- Organiza la información usando viñetas limpias, negritas estratégicas y espaciado claro. La respuesta debe verse ejecutiva y legible en un vistazo rápido.

6. MEMORIA CONTEXTUAL Y SEGUIMIENTO
- Presta atención al hilo de la conversación. Si el usuario estuvo preguntando sobre inventarios de GLP, en sus siguientes preguntas prioriza y sugiere datasets de la categoría de Hidrocarburos y GLP.

7. INTERACCIÓN CONVERSACIONAL ACTIVA
- Haz preguntas cortas de negocio para guiar al usuario en la toma de decisiones o el enfoque del análisis (ej. "¿Desea que analicemos la tendencia del costo marginal de este año o prefiere comparar los precios de energía por región?").
- Si el usuario hizo una pregunta de datos con respuesta directa, NO le hagas preguntas de opción ni conversacionales previas: ve y consulta el dato con `query_data` primero.
- NUNCA hagas preguntas sobre aspectos técnicos de bases de datos, nombres de columnas o confirmaciones previas de ejecución de herramientas del MCP.
- Fomenta el diálogo de forma natural y servicial.

8. PROFUNDIDAD TÉCNICA BAJO DEMANDA
- Mantén toda la información técnica disponible. Si el usuario te pide explícitamente detalles como nombres técnicos de tablas, tipos de datos, llaves o estructuras SQL, proporciónaselos con total exactitud y rigor técnico.

81: 9. PROCESO INTERNO DE DESCUBRIMIENTO DE DATOS (PARA TU USO INTERNO COMO LLM):
82: - Si el usuario solicita explorar el catálogo, ver qué tablas hay, buscar datasets, o importar bases de datos, DEBES llamar inmediatamente a la herramienta `get_catalogo_datos` para listar las opciones reales disponibles y presentarlas interactivamente.
83: - Si el usuario te solicita datos, tendencias, gráficos o análisis específicos, y no conoces la tabla o ID, DEBES llamar primero a la herramienta `get_catalogo_datos` para identificar el dataset correspondiente en el catálogo.
84: - Inmediatamente después de obtener la lista del catálogo, debes analizarla, seleccionar la tabla idónea (ej: `CMO_TX_CENTRAL_GEN` para centrales o empresas eléctricas, `VW_EESS_UBICACION_GEO` para estaciones de servicio, etc.), llamar a `get_detalle_catalogo_datos` para ver sus columnas, y luego ejecutar `query_data` con los filtros correspondientes (ej: `filters: {"NO_DEPARTAMENTO": "HUANUCO"}`).
85: - Todo este flujo de llamadas a herramientas (`get_catalogo_datos` -> `get_detalle_catalogo_datos` -> `query_data`) debe ser ejecutado en forma continua y encadenada en un solo turno, sin detenerse a preguntarle nada al usuario, hasta obtener los datos y poder responderle con la respuesta final.
86: - Queda prohibido inventar o alucinar nombres de tablas, esquemas, columnas o IDs de catálogo. Búscalos siempre mediante las herramientas.
87: 
88: 10. AUTONOMÍA EJECUTIVA ABSOLUTA (PROHIBIDO PREGUNTAR DETALLES TÉCNICOS O PEDIR PERMISOS):
89: - NO le preguntes al usuario si desea que consultes la tabla o si debes ejecutar la herramienta. Procede a realizar la cadena de consultas del catálogo y la base de datos de forma autónoma e inmediata.
90: - NO le pidas al usuario nombres de columnas, tipos de datos o parámetros de base de datos. Obtén esta información consultando los detalles de la tabla de forma silenciosa.
91: - El usuario es un gerente/director de negocio y no conoce el modelo de base de datos, por lo que tú debes resolver toda la capa técnica de forma autónoma e interna y entregarle el dato final consultado.
"""

# Configuración de URLs y credenciales
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
import difflib

def normalize_text(text):
    """
    Normaliza el texto quitando puntuación y palabras de cortesía o relleno comunes.
    """
    if not text:
        return ""
    text = text.lower().strip()
    
    # Quitar signos de puntuación comunes
    punctuation = [".", ",", "?", "¿", "!", "¡", "(", ")", "-", "_"]
    for char in punctuation:
        text = text.replace(char, "")
        
    # Limpiar espacios múltiples
    words = text.split()
    
    # Palabras de relleno a omitir (stopwords básicas de cortesía)
    fillers = {"por", "favor", "porfavor", "gracias", "hola", "buenos", "dias", "tardes", "noches", "estimado", "asistente", "copiloto"}
    filtered_words = [w for w in words if w not in fillers]
    
    return " ".join(filtered_words)

def find_fuzzy_match(query, cache, threshold=0.85):
    """
    Busca una coincidencia difusa en el caché de la sesión usando difflib.
    Devuelve la respuesta guardada si supera el umbral de similitud, de lo contrario None.
    """
    norm_query = normalize_text(query)
    if not norm_query:
        return None
        
    for cached_query, data in cache.items():
        norm_cached = normalize_text(cached_query)
        # Comparar similitud de secuencias
        similarity = difflib.SequenceMatcher(None, norm_query, norm_cached).ratio()
        if similarity >= threshold:
            return data
            
    return None

# ----------------- Funciones Auxiliares de Registro y Cuotas -----------------

def log_usage(gerente, model, query, prompt_tokens=0, completion_tokens=0):
    """
    Registra el uso del agente en el archivo log_uso.txt
    """
    try:
        log_path = os.path.join(current_dir, "log_uso.txt")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(
                f"[{timestamp}] Gerente: {gerente} | "
                f"Modelo: {model} | "
                f"Prompt Tokens: {prompt_tokens} | "
                f"Completion Tokens: {completion_tokens} | "
                f"Consulta: {query}\n"
            )
    except Exception as e:
        print(f"Error escribiendo en log_uso.txt: {e}")

def is_rate_limited():
    """
    Controla el consumo justo (máximo 50 preguntas en 10 minutos por sesión).
    Utiliza una ventana deslizante basada en marcas de tiempo en cl.user_session.
    """
    now = time.time()
    timestamps = cl.user_session.get("message_timestamps", [])
    
    # Filtrar marcas de tiempo mayores a 10 minutos (600 segundos)
    timestamps = [t for t in timestamps if now - t < 600]
    cl.user_session.set("message_timestamps", timestamps)
    
    # Validar límite de 50 mensajes
    if len(timestamps) >= 50:
        return True
        
    # Registrar mensaje actual
    timestamps.append(now)
    cl.user_session.set("message_timestamps", timestamps)
    return False

# ----------------- Obtención y Formateo de Herramientas -----------------

def fetch_tools_from_server(base_url):
    """
    Obtiene la lista de herramientas del servidor Osinergmin
    utilizando el canal oficial SSE de MCP.
    """
    from semantic_registry import run_async_in_thread, CustomSseMcpClient
    
    async def get_tools_async():
        sse_url = base_url if base_url.endswith("/sse") else f"{base_url}/sse"
        client = CustomSseMcpClient(sse_url)
        try:
            await client.connect()
            await client.initialize()
            tools = await client.list_tools()
            return tools
        finally:
            await client.close()
            
    try:
        raw_tools = run_async_in_thread(get_tools_async())
        openai_tools = []
        
        for tool in raw_tools:
            name = tool.get("name")
            desc = tool.get("description", "")
            schema = tool.get("inputSchema", {})
            
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": desc,
                    "parameters": {
                        "type": schema.get("type", "object"),
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", [])
                    }
                }
            })
        return openai_tools
    except Exception as e:
        raise RuntimeError(f"Fallo crítico de conexión al servidor MCP real vía SSE en {base_url}: {str(e)}")

# ----------------- Ejecución Local de Herramientas -----------------

def run_local_tool(base_url, name, args):
    """
    Ejecuta la herramienta correspondiente llamando al canal estándar SSE (MCP oficial).
    """
    print(f"[BACKEND] Ejecutando herramienta {name!r} vía SSE...")
    try:
        from semantic_registry import run_async_in_thread, run_tool_via_sse, normalize_tool_result
        raw_res = run_async_in_thread(run_tool_via_sse(base_url, name, args))
        result = normalize_tool_result(raw_res)
        print(f"[BACKEND] Herramienta {name!r} ejecutada con éxito vía SSE.")
        return result
    except Exception as sse_err:
        print(f"[BACKEND ERROR] Fallo al ejecutar {name!r} vía SSE: {sse_err}")
        raise RuntimeError(f"Fallo de conexión al ejecutar la herramienta MCP {name!r} vía SSE: {sse_err}")

# ----------------- Enrutador de Resiliencia del LLM -----------------

async def stream_llm_response(messages, tools=None):
    """
    Envía la solicitud al proveedor (Google AI Studio o OpenRouter) con resiliencia y reintentos.
    Si el modelo principal falla, intenta secuencialmente con los de respaldo.
    """
    # Recargar variables de entorno dinámicamente para capturar cambios en .env (como la API key o GEMINI_MODEL) sin reiniciar el servidor
    load_dotenv(dotenv_path, override=True)
    
    # Clonar y adaptar mensajes dinámicamente con contexto de datos e filtros activos
    injected_messages = list(messages)
    
    # 0. Limpiar y aplanar el historial de turnos pasados finalizados
    # Eliminamos las llamadas a herramientas y volcados de datos anteriores para evitar
    # errores de compatibilidad (como INVALID_ARGUMENT 400 en Gemini) y optimizar tokens.
    cleaned_messages = []
    if len(injected_messages) > 0:
        cleaned_messages.append(injected_messages[0]) # System prompt
        chat_history = injected_messages[1:]
        
        # Encontrar el índice del último mensaje del usuario (inicio del turno actual)
        last_user_idx = -1
        for i in range(len(chat_history) - 1, -1, -1):
            if chat_history[i].get("role") == "user":
                last_user_idx = i
                break
                
        if last_user_idx != -1:
            past_history = chat_history[:last_user_idx]
            current_turn = chat_history[last_user_idx:]
            
            cleaned_past = []
            for msg in past_history:
                role = msg.get("role")
                content = msg.get("content")
                if role == "user":
                    cleaned_past.append({"role": "user", "content": content})
                elif role == "assistant" and content:
                    cleaned_past.append({"role": "assistant", "content": content})
            
            cleaned_messages.extend(cleaned_past)
            cleaned_messages.extend(current_turn)
        else:
            cleaned_messages.extend(chat_history)
            
    injected_messages = cleaned_messages
    
    # 1. Inyectar Filtros Activos de la Sesión
    filtros_activos = cl.user_session.get("filtros_activos")
    if filtros_activos and len(injected_messages) > 0:
        try:
            ubicacion = filtros_activos.get("ubicacion", "Todas")
            periodo = filtros_activos.get("periodo", "Todos")
            categoria = filtros_activos.get("categoria", [])
            if isinstance(categoria, list):
                categoria_str = ", ".join(categoria)
            else:
                categoria_str = str(categoria)
                
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
            
            # Construir contexto de filtros activos
            filtros_context = (
                f"\n\nFILTROS ACTIVOS SELECCIONADOS POR EL USUARIO EN EL SIDEBAR:\n"
                f"- Geografía/Ubicación: {ubicacion}\n"
                f"- Periodo: {periodo}\n"
                f"- Matriz Energética (Categorías): {categoria_str or 'Todas'}\n"
                f"- Datasets/Tablas Activos e Importados: {datasets_str}\n"
                f"\n🔴 INSTRUCCIONES PARA LA CONSULTA DE DATOS Y RENDERIZADO EN LA INTERFAZ:\n"
                f"1. Si el usuario solicita datos, tendencias, números o ver qué datos tienes disponibles, y no conoces qué tablas existen, DEBES llamar primero a la herramienta `get_catalogo_datos`.\n"
                f"2. Una vez identificada la tabla adecuada en la lista devuelta (ej. 'CMO_TX_CENTRAL_GEN', 'VW_EESS_UBICACION_GEO', 'CMO_TD_BLOOMBERGDATA', etc.), DEBES llamar a la herramienta `get_detalle_catalogo_datos` pasando su `id_catalogo` para conocer sus columnas reales, tipos de datos y descripciones.\n"
                f"3. Con los nombres de columnas físicos obtenidos, ejecuta la consulta utilizando la herramienta `query_data` especificando el esquema ('ES_DATGOB_CV' por defecto), la tabla física, su `id_catalogo`, y un diccionario de `filters` clave-valor (ej: `filters: {{\"DEPARTAMENTO\": \"MOQUEGUA\"}}`).\n"
                f"4. Todo este descubrimiento y consulta debe realizarse de forma 100% autónoma en el primer turno encadenando las herramientas necesarias antes de responder al usuario final.\n"
                f"5. Después de obtener los datos y presentar tu respuesta en texto libre al usuario, DEBES incluir obligatoriamente al final de tu mensaje el bloque de código Markdown marcado con la etiqueta `json-osam`.\n"
                f"Este bloque JSON es el que lee la interfaz de usuario de React para poder activar la visualización interactiva de pestañas 'Tabla' y 'Gráfico' juntas. El formato del bloque DEBE ser exactamente este:\n"
                f"```json-osam\n"
                f"{{\n"
                f"  \"report\": {{\n"
                f"    \"columns\": [\n"
                f"      {{\"id\": \"FE_FECHA\", \"name\": \"Fecha\", \"type\": \"DATE\"}},\n"
                f"      {{\"id\": \"CO_IDENTIFIER\", \"name\": \"Identificador\", \"type\": \"VARCHAR2\"}},\n"
                f"      {{\"id\": \"NU_PX_LAST\", \"name\": \"Último Valor\", \"type\": \"NUMBER\"}}\n"
                f"    ],\n"
                f"    \"data\": [\n"
                f"      {{\"FE_FECHA\": \"2026-04-16\", \"CO_IDENTIFIER\": \"SI1 COMDTY\", \"NU_PX_LAST\": 78.71}}\n"
                f"    ],\n"
                f"    \"presentation\": {{\n"
                f"      \"chart\": {{\n"
                f"        \"type\": \"line\",\n"
                f"        \"x\": \"FE_FECHA\",\n"
                f"        \"y\": \"NU_PX_LAST\"\n"
                f"      }},\n"
                f"      \"default_view\": \"table\"\n"
                f"    }}\n"
                f"  }},\n"
                f"  \"analysis\": {{\n"
                f"    \"insights\": [\n"
                f"      {{\"type\": \"trend\", \"text\": \"Escribe aquí una conclusión relevante sobre los datos...\"}}\n"
                f"    ]\n"
                f"  }}\n"
                f"}}\n"
                f"```\n"
                f"Asegúrate de reemplazar 'columns', 'data', 'x', e 'y' con las columnas reales que te devolvieron las herramientas. NUNCA inventes columnas ni datos."
            )
            system_msg = dict(injected_messages[0])
            system_msg["content"] = system_msg["content"] + filtros_context
            injected_messages[0] = system_msg
        except Exception as fe:
            print(f"Error inyectando filtros activos en prompt: {fe}")

    # 2. Inyectar Contexto de Datos de la Sesión
    last_result = cl.user_session.get("last_tool_result")
    if last_result and isinstance(last_result, list) and len(last_result) > 0 and len(injected_messages) > 0:
        try:
            df = pd.DataFrame(last_result)
            cols_info = ", ".join(f"{col} ({dtype})" for col, dtype in df.dtypes.items())
            num_cols = list(df.select_dtypes('number').columns)
            
            data_context = (
                f"\n\nDATOS DISPONIBLES EN SESIÓN:\n"
                f"- Filas recuperadas: {len(df)}\n"
                f"- Columnas y tipos: {cols_info}\n"
                f"- Columnas numéricas aptas para Y: {num_cols}\n"
                f"Si el usuario pide un gráfico, tendencia o comparación visual, invoca la herramienta 'crear_grafico' "
                f"usando estas columnas exactas."
            )
            
            system_msg = dict(injected_messages[0])
            system_msg["content"] = system_msg["content"] + data_context
            injected_messages[0] = system_msg
        except Exception as e:
            print(f"Error inyectando contexto de datos en prompt: {e}")

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    llm_key = (os.getenv("LLM_API_KEY") or LLM_API_KEY or "").strip()
    
    # Priorizar estrictamente GEMINI_API_KEY para conectar con Google AI Studio directamente
    if gemini_key:
        api_key = gemini_key
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        env_models = os.getenv("GEMINI_MODEL")
        if env_models:
            # Extraer lista completa de modelos configurados
            model_list = [m.strip() for m in env_models.split(",") if m.strip()]
        else:
            model_list = ["gemini-2.5-flash"]
        provider_name = "Google AI Studio (Gemini)"
    elif llm_key and llm_key.startswith("sk-or-"):
        api_key = llm_key
        base_url = "https://openrouter.ai/api/v1"
        model_list = ["google/gemini-2.5-flash"]
        provider_name = "OpenRouter"
    else:
        # Fallback si no hay claves válidas configuradas
        api_key = llm_key or gemini_key
        base_url = "https://openrouter.ai/api/v1"
        model_list = ["google/gemini-2.5-flash"]
        provider_name = "OpenRouter"

    # max_retries=0 desactiva los reintentos automáticos internos de la librería openai
    client = openai.AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        max_retries=0
    )
    
    last_exception = None
    
    # Bucle principal de rotación de modelos
    for model in model_list:
        print(f"[BACKEND] Intentando conectar con modelo {model!r} a través de {provider_name}...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Backoff exponencial progresivo ante reintentos
                    backoff_delay = attempt * 3
                    print(f"[BACKEND WARNING] Esperando {backoff_delay}s antes del reintento {attempt+1}/{max_retries}...")
                    await asyncio.sleep(backoff_delay)
                    
                kwargs = {
                    "model": model,
                    "messages": injected_messages,
                    "stream": True,
                    "stream_options": {"include_usage": True}
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["parallel_tool_calls"] = False
                    
                try:
                    stream = await client.chat.completions.create(**kwargs)
                except Exception as inner_e:
                    print(f"[BACKEND DEBUG] Falló completions para {model}. Error: {inner_e}")
                    if "stream_options" in kwargs:
                        del kwargs["stream_options"]
                        try:
                            stream = await client.chat.completions.create(**kwargs)
                        except Exception as inner_e2:
                            print(f"[BACKEND DEBUG] Reintento sin stream_options también falló para {model}: {inner_e2}")
                            raise inner_e2
                    else:
                        raise inner_e
                        
                # Si llegamos aquí, la llamada fue exitosa
                return stream, model
                
            except Exception as e:
                last_exception = e
                # Verificar si es un error transitorio de red, cuota o sobrecarga (429, 503, 500)
                is_transient = any(code in str(e) for code in ["429", "503", "500"]) or "rate" in str(e).lower() or "overloaded" in str(e).lower() or "unavailable" in str(e).lower()
                
                if is_transient and attempt < max_retries - 1:
                    print(f"[BACKEND WARNING] Error transitorio detectado en {model}: {e}. Reintentando...")
                    continue
                else:
                    print(f"[BACKEND WARNING] Fallo definitivo para el modelo {model}: {e}.")
                    # Rompe el bucle de reintentos actual y pasa al siguiente modelo de respaldo
                    break
                    
    # Si todos los modelos de la lista fallaron
    raise RuntimeError(f"Todos los modelos de la lista fallaron. Último error: {last_exception}")

# ----------------- Generador Automático de Gráficos -----------------

import plotly.graph_objects as go
import plotly.express as px

def try_generate_chart(data, query):
    """
    Analiza los datos y la consulta del usuario para generar un gráfico.
    Busca columnas para el eje X (fechas/periodos) y el eje Y (numéricos/valores).
    Devuelve la ruta absoluta del archivo generado si tiene éxito, de lo contrario None.
    """
    try:
        # Validar tipo de datos
        if not isinstance(data, list) or len(data) == 0:
            return None
            
        # Convertir a DataFrame de pandas
        df = pd.DataFrame(data)
        
        # Eliminar columnas que no aportan valor visual
        cols_to_drop = [c for c in df.columns if any(p in c.lower() for p in ["id_", "co_", "ip_", "usuario", "estado"])]
        plot_df_cols = [c for c in df.columns if c not in cols_to_drop]
        
        # 1. Identificar eje X (Temporal/Categorías)
        x_col = None
        date_keywords = ["fecha", "periodo", "anio", "mes", "dia", "date", "fe_", "nu_anio", "period", "fec"]
        
        for col in plot_df_cols:
            col_lower = col.lower()
            if any(kw in col_lower for kw in date_keywords):
                x_col = col
                break
                
        if not x_col:
            # Si no hay columnas con nombres de fecha, ver si hay alguna de tipo datetime o numérica de año
            for col in plot_df_cols:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    x_col = col
                    break
        
        # 2. Identificar eje Y (Valores Numéricos)
        y_cols = []
        for col in plot_df_cols:
            if col == x_col:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                y_cols.append(col)
                
        # Si no hay numéricas por tipo, intentar convertir
        if not y_cols:
            numeric_keywords = ["precio", "demanda", "cantidad", "cmo", "inventario", "mo_", "nu_", "valor", "monto", "ejecutada", "total"]
            for col in plot_df_cols:
                if col == x_col:
                    continue
                if any(kw in col.lower() for kw in numeric_keywords):
                    try:
                        df[col] = pd.to_numeric(df[col])
                        y_cols.append(col)
                    except:
                        pass
                        
        if not x_col or not y_cols:
            return None
            
        y_col = y_cols[0]
        
        # Limpiar nulos para graficar
        plot_df = df[[x_col, y_col]].dropna()
        if len(plot_df) == 0:
            return None
            
        # Ordenar por el eje X si aplica
        try:
            plot_df = plot_df.sort_values(by=x_col)
        except:
            pass
            
        # Generar el gráfico con Plotly
        fig = go.Figure()
        
        # Estilos modernos y elegantes
        fig.add_trace(go.Scatter(
            x=plot_df[x_col].astype(str), 
            y=plot_df[y_col], 
            mode='lines+markers',
            name=y_col,
            line=dict(color='#0D6EFD', width=2),
            marker=dict(size=8)
        ))
        
        # Títulos limpios
        title_x = str(x_col).replace('_', ' ').title()
        title_y = str(y_col).replace('_', ' ').title()
        
        fig.update_layout(
            title=f"Evolución / Tendencia de {title_y} por {title_x}",
            xaxis_title=title_x,
            yaxis_title=title_y,
            template="plotly_white",
            margin=dict(l=40, r=40, t=60, b=40),
            hovermode="x unified"
        )
        
        # Crear directorio temporal si no existe
        temp_dir = os.path.join(current_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        chart_path = os.path.join(temp_dir, "last_trend_chart.png")
        # Para mantener compatibilidad con cl.Image, guardamos como imagen estática como fallback,
        # pero es mejor devolver la figura directamente si el caller lo soporta.
        fig.write_image(chart_path, scale=2)
        
        return chart_path
    except Exception as e:
        print(f"Error generando gráfico automático: {e}")
        return None

def try_generate_chart_json(data, query):
    """
    Analiza los datos y la consulta del usuario para generar los metadatos de un gráfico interactivo.
    Identifica columnas X (temporal/categoría) e Y (valores numéricos) y devuelve un diccionario serializable a JSON.
    """
    try:
        if not isinstance(data, list) or len(data) == 0:
            return None
            
        df = pd.DataFrame(data)
        
        # Eliminar columnas de control irrelevantes en la graficación
        cols_to_drop = [c for c in df.columns if any(p in c.lower() for p in ["id_", "co_", "ip_", "usuario", "estado"])]
        plot_df_cols = [c for c in df.columns if c not in cols_to_drop]
        
        # 1. Identificar eje X (Temporal/Categorías)
        x_col = None
        date_keywords = ["fecha", "periodo", "anio", "mes", "dia", "date", "fe_", "nu_anio", "period", "fec", "central", "empresa", "nombre", "tipo"]
        
        for col in plot_df_cols:
            col_lower = col.lower()
            if any(kw in col_lower for kw in date_keywords):
                x_col = col
                break
                
        if not x_col and len(plot_df_cols) > 0:
            x_col = plot_df_cols[0]
            
        # 2. Identificar eje Y (Valores Numéricos)
        y_cols = []
        for col in plot_df_cols:
            if col == x_col:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                y_cols.append(col)
                
        # Si no hay numéricas por tipo, intentar convertir bajo palabras clave
        if not y_cols:
            numeric_keywords = ["precio", "demanda", "cantidad", "cmo", "inventario", "mo_", "nu_", "valor", "monto", "ejecutada", "total", "potencia", "mw", "kw"]
            for col in plot_df_cols:
                if col == x_col:
                    continue
                if any(kw in col.lower() for kw in numeric_keywords):
                    try:
                        df[col] = pd.to_numeric(df[col])
                        y_cols.append(col)
                    except:
                        pass
                        
        if not x_col or not y_cols:
            return None
            
        y_col = y_cols[0]
        
        # Limpiar nulos para graficar
        plot_df = df[[x_col, y_col]].dropna()
        if len(plot_df) == 0:
            return None
            
        # Ordenar por el eje X si aplica
        try:
            plot_df = plot_df.sort_values(by=x_col)
        except:
            pass
            
        # Limitar a top 25 registros para que el gráfico sea legible en pantalla
        if len(plot_df) > 25:
            plot_df = plot_df.head(25)
            
        # Formatear datos a JSON estructurado
        chart_data = {
            "tipo": "lineas" if any(k in x_col.lower() for k in ["fecha", "periodo", "anio", "mes", "dia", "date"]) else "barras",
            "titulo": f"Evolución / Tendencia de {str(y_col).replace('_', ' ').title()} por {str(x_col).replace('_', ' ').title()}",
            "columna_x": x_col,
            "columna_y": y_col,
            "datos": plot_df.to_dict(orient="records")
        }
        return chart_data
    except Exception as e:
        print(f"Error analizando datos para JSON Chart: {e}")
        return None

async def run_local_chart_tool(args):
    """
    Ejecuta la creación local de gráficos basada en la última consulta de datos de la sesión.
    Muestra el gráfico directamente en el chat utilizando cl.Pyplot.
    """
    try:
        last_result = cl.user_session.get("last_tool_result")
        if not last_result or not isinstance(last_result, list) or len(last_result) == 0:
            return False, "No hay datos de consulta activos en esta sesión para graficar. Asegúrese de consultar datos primero antes de pedir un gráfico."
            
        df = pd.DataFrame(last_result)
        
        tipo = args.get("tipo_grafico", "lineas")
        x_col = args.get("columna_x")
        y_col = args.get("columna_y")
        titulo = args.get("titulo") or f"Tendencia de {y_col} por {x_col}"
        
        if x_col not in df.columns or y_col not in df.columns:
            available_cols = ", ".join(df.columns)
            return False, f"La columna '{x_col}' o '{y_col}' no existe en el conjunto de datos. Columnas disponibles: {available_cols}"
            
        # Intentar convertir eje Y a numérico
        try:
            df[y_col] = pd.to_numeric(df[y_col])
        except Exception as e:
            return False, f"La columna Y ({y_col}) no se pudo convertir a formato numérico para graficar: {str(e)}"
            
        plot_df = df[[x_col, y_col]].dropna()
        if len(plot_df) == 0:
            return False, "El conjunto de datos seleccionado no contiene filas válidas (sin valores nulos) para graficar."
            
        # Ordenar por eje X si aplica
        try:
            plot_df = plot_df.sort_values(by=x_col)
        except:
            pass
            
        # Crear la figura
        fig, ax = plt.subplots(figsize=(10, 5))
        
        if tipo == "barras":
            ax.bar(plot_df[x_col].astype(str), plot_df[y_col], color='#0D6EFD', alpha=0.85, edgecolor='black')
        elif tipo == "dispersion":
            ax.scatter(plot_df[x_col].astype(str), plot_df[y_col], color='#DC3545', s=50, alpha=0.85)
        elif tipo == "pastel":
            # Limitar a top 10 para no saturar
            pie_data = plot_df.head(10)
            ax.pie(pie_data[y_col], labels=pie_data[x_col].astype(str), autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
            ax.axis('equal')
        else: # lineas
            ax.plot(plot_df[x_col].astype(str), plot_df[y_col], marker='o', linewidth=2, color='#0D6EFD', label=y_col)
            
        ax.set_title(titulo, fontsize=13, fontweight='bold', pad=15)
        if tipo != "pastel":
            ax.set_xlabel(str(x_col).replace('_', ' ').title(), fontsize=10, labelpad=8)
            ax.set_ylabel(str(y_col).replace('_', ' ').title(), fontsize=10, labelpad=8)
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, linestyle='--', alpha=0.5)
            if tipo == "lineas":
                ax.legend()
                
        plt.tight_layout()
        
        # Generar JSON estructurado para el frontend React
        chart_json = {
            "tipo": tipo,
            "titulo": titulo,
            "columna_x": x_col,
            "columna_y": y_col,
            "datos": plot_df.to_dict(orient="records")
        }
        chart_block = f"\n\n```json-chart\n{json.dumps(chart_json, ensure_ascii=False, indent=2)}\n```"

        # Enviar elemento inline cl.Pyplot
        pyplot_element = cl.Pyplot(figure=fig, name="grafico", display="inline")
        await cl.Message(
            content=f"📊 **Gráfico generado:** {titulo}{chart_block}",
            elements=[pyplot_element],
            author="Sistema"
        ).send()
        
        plt.close(fig)
        cl.user_session.set("chart_generated_in_turn", True)
        return True, f"Gráfico de tipo '{tipo}' generado con éxito para {y_col} vs {x_col}."
    except Exception as e:
        return False, f"Error al crear el gráfico: {str(e)}"

# ----------------- Autenticación de Usuarios (Login) -----------------

# Diccionario de roles y credenciales válidas para el prototipo (Simulando gobernanza corporativa)
DICCIONARIO_ROLES = {
    "gerente.energia@osinergmin.gob.pe": "Gerente de Energía",
    "analista.mcp@osinergmin.gob.pe": "Analista de Datos MCP",
    "supervisor.intranet@osinergmin.gob.pe": "Supervisor Corporativo",
    "admin.openenergy@osinergmin.gob.pe": "Administrador de Sistemas"
}

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """
    Función de autenticación temporal corporativa.
    Valida credenciales simulando la integración OIDC/Microsoft AD.
    """
    clean_username = username.strip().lower()
    
    # 1. Comprobar si el correo está registrado en la base de gobernanza
    rol_asignado = DICCIONARIO_ROLES.get(clean_username)
    if not rol_asignado:
        print(f"[AUTH ERROR] Intento de login fallido para '{clean_username}'. Usuario no autorizado en la base de gobernanza.")
        return None
        
    # 2. Comprobar contraseña corporativa demo
    if password != "Osi2026!":
        print(f"[AUTH ERROR] Contraseña incorrecta para el usuario '{clean_username}'.")
        return None

    # Formatear el display name a partir del correo
    display_name = clean_username.split("@")[0].replace(".", " ").title()

    # Devolvemos el usuario autenticado con su rol asignado en la metadata
    print(f"[AUTH SUCCESS] Usuario '{clean_username}' autenticado como '{rol_asignado}'.")
    return cl.User(
        identifier=clean_username, 
        username=clean_username, 
        display_name=display_name,
        metadata={"rol": rol_asignado}
    )

# ----------------- Eventos de Chainlit -----------------

@cl.on_chat_start
async def start():
    print("\n[BACKEND] --- ON CHAT START TRIGGERED ---")
    # Obtener el nombre del gerente desde la sesión autenticada de forma robusta
    user = cl.user_session.get("user")
    gerente_name = "Gerente"
    if user:
        gerente_name = getattr(user, "username", None) or getattr(user, "identifier", "Gerente")
        
    cl.user_session.set("gerente", gerente_name)
    cl.user_session.set("message_timestamps", [])
    cl.user_session.set("faq_cache", {})

    # Cargar y almacenar herramientas del servidor en la sesión (Caché de MCP al arrancar)
    with cl.Step(name="Inicializando herramientas MCP", type="system") as step:
        try:
            openai_tools = fetch_tools_from_server(MCP_SERVER_URL)
        except Exception as e:
            print(f"[BACKEND ERROR] No se pudieron obtener las herramientas del servidor MCP: {e}")
            openai_tools = []
        
        # Definir la herramienta local de creación de gráficos
        local_chart_tool = {
            "type": "function",
            "function": {
                "name": "crear_grafico",
                "description": "Genera y muestra un gráfico (de líneas, barras, dispersión o pastel) en el chat a partir de los últimos datos de la consulta. Úsela si el usuario le pide explícitamente graficar, ver tendencias, curvas o comparaciones visuales.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tipo_grafico": {
                            "type": "string",
                            "enum": ["lineas", "barras", "dispersion", "pastel"],
                            "description": "El tipo de gráfico a generar (lineas, barras, dispersion, pastel)."
                        },
                        "columna_x": {
                            "type": "string",
                            "description": "El nombre exacto de la columna del eje X (generalmente fecha, periodo, año o categorías)."
                        },
                        "columna_y": {
                            "type": "string",
                            "description": "El nombre exacto de la columna del eje Y (valores numéricos como precio, demanda, etc.)."
                        },
                        "titulo": {
                            "type": "string",
                            "description": "Título descriptivo para el gráfico."
                        }
                    },
                    "required": ["tipo_grafico", "columna_x", "columna_y"]
                }
            }
        }
        
        if openai_tools is None:
            openai_tools = []
        openai_tools.append(local_chart_tool)
        cl.user_session.set("openai_tools", openai_tools)
        
        if len(openai_tools) > 1:
            tools_list_desc = "\n".join([f"- **{t['function']['name']}**: {t['function']['description']}" for t in openai_tools])
            step.output = f"Se cargaron {len(openai_tools)} herramientas:\n{tools_list_desc}"
        else:
            step.output = "⚠️ Advertencia: No se pudieron precargar las herramientas del servidor. Verifica la URL en .env"

    # Cargar catálogo de datos gobernados en caché de sesión al arrancar a través de get_semantic_catalog
    try:
        catalog_dict = get_semantic_catalog()
        catalogo = [
            {
                "table_name": k,
                "description": v.get("description", ""),
                "NO_TABLA": k,
                "DE_TABLA": v.get("description", ""),
                "id_catalogo": int(v.get("id_catalogo") or 0)
            }
            for k, v in catalog_dict.get("tables", {}).items()
        ]
        cl.user_session.set("catalogo_completo", catalogo)
        print(f"[BACKEND] Catálogo de datos cargado en sesión ({len(catalogo)} elementos desde Registro Semántico).")
    except Exception as ce:
        print(f"[BACKEND ERROR] No se pudo precargar el catálogo en sesión: {ce}")

    # Construir el System Prompt adaptado dinámicamente según el rol del usuario
    personalized_system_prompt = SYSTEM_PROMPT
    if gerente_name == "gerente_comercial":
        personalized_system_prompt += (
            "\n\nCONTEXTO ESPECÍFICO DEL USUARIO:\n"
            "- El usuario actual es el GERENTE COMERCIAL de Osinergmin. Su foco de interés principal son "
            "los precios, tarifas, costos, contratos y la demanda comercial de energía y combustibles.\n"
            "- Prioriza y destaca la perspectiva comercial, análisis de tarifas e indicadores de mercado en tus respuestas."
        )
    elif gerente_name == "gerente_operaciones":
        personalized_system_prompt += (
            "\n\nCONTEXTO ESPECÍFICO DEL USUARIO:\n"
            "- El usuario actual es el GERENTE DE OPERACIONES de Osinergmin. Su foco de interés principal es "
            "la infraestructura (centrales, líneas, subestaciones), capacidad física, inventarios y disponibilidad de productos.\n"
            "- Prioriza y destaca la perspectiva de continuidad operativa, distribución e infraestructura física en tus respuestas."
        )
    elif gerente_name == "admin":
        personalized_system_prompt += (
            "\n\nCONTEXTO ESPECÍFICO DEL USUARIO:\n"
            "- El usuario actual es el ADMINISTRADOR. Tiene un perfil de supervisión general y técnico.\n"
            "- Puedes responder con detalles técnicos y nombres de tablas reales con mayor soltura, pero manteniendo la estructura ejecutiva y limpia."
        )

    # Inicializar historial de conversación con el System Prompt adaptado
    cl.user_session.set("history", [
        {"role": "system", "content": personalized_system_prompt}
    ])
    
    # Configuración de Filtros (Refinar Resultados [RF-07])
    await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="ubicacion",
                label="Ubicación",
                values=["Sede Nacional", "Amazonas", "Áncash", "Apurímac", "Arequipa", "Ayacucho", "Cajamarca", "Callao", "Cusco", "Huancavelica", "Huánuco", "Ica", "Junín", "La Libertad", "Lambayeque", "Lima", "Loreto", "Madre de Dios", "Moquegua", "Pasco", "Piura", "Puno", "San Martín", "Tacna", "Tumbes", "Ucayali"],
                initial_index=0, # Sede Nacional
            ),
            cl.input_widget.Select(
                id="periodo",
                label="Periodo",
                values=["Todos", "AÑO: 2024", "AÑO: 2023", "AÑO: 2022", "AÑO: 2021"],
                initial_index=2, # AÑO: 2023
            ),
            cl.input_widget.Tags(
                id="categoria",
                label="Categoría",
                initial=["Solar"],
            ),
            cl.input_widget.Tags(
                id="entidad",
                label="Entidad",
                initial=["MINEM"],
            ),
            cl.input_widget.Tags(
                id="variable",
                label="Variable",
                initial=["Generación (MWh)"],
            )
        ]
    ).send()

    # Mensaje estético de bienvenida
    await cl.Message(
        content=f"💼 Bienvenido **{gerente_name}**, soy su asistente ejecutivo de inteligencia de datos en Osinergmin. "
                "Estoy listo para asistirte con tus consultas en lenguaje natural sobre nuestros datos gobernados.\n\n"
                "⚙️ *Puedes usar el botón de ajustes (Settings) para refinar tus resultados de búsqueda por ubicación, periodo y más.*",
        author="Sistema"
    ).send()

@cl.on_settings_update
async def setup_agent(settings):
    # Obtener filtros antiguos para comparación
    prev_settings = cl.user_session.get("filtros_activos") or {}
    cl.user_session.set("filtros_activos", settings)
    
    # Detectar cambios en los datasets activos
    prev_datasets = prev_settings.get("datasets_activos", [])
    curr_datasets = settings.get("datasets_activos", [])
    
    prev_titles = [d.get("table_name") if isinstance(d, dict) else str(d) for d in prev_datasets]
    curr_titles = [d.get("table_name") if isinstance(d, dict) else str(d) for d in curr_datasets]
    
    if curr_titles != prev_titles:
        # Encontrar cuál se agregó
        added = [d for d in curr_datasets if (d.get("table_name") if isinstance(d, dict) else str(d)) not in prev_titles]
        if added:
            added_item = added[0]
            table_name = added_item.get("table_name") if isinstance(added_item, dict) else str(added_item)
            await cl.Message(
                content=f"📥 **Dataset importado y activo:** `{table_name}`\nEl asistente ahora tiene este dataset como contexto prioritario.",
                author="Sistema"
            ).send()
            return

    # Comprobar si hubo cambios en los otros filtros para evitar spam redundante
    keys = ["ubicacion", "periodo", "categoria", "entidad"]
    has_filter_changes = any(settings.get(k) != prev_settings.get(k) for k in keys if k in settings or k in prev_settings)
    
    if has_filter_changes:
        ubicacion = settings.get("ubicacion")
        periodo = settings.get("periodo")
        categoria = ", ".join(settings.get("categoria", [])) if isinstance(settings.get("categoria"), list) else settings.get("categoria", "")
        entidad = ", ".join(settings.get("entidad", [])) if isinstance(settings.get("entidad"), list) else settings.get("entidad", "")
        
        mensaje_filtros = f"✅ **Filtros Actualizados:**\n- Ubicación: {ubicacion}\n- Periodo: {periodo}"
        if categoria:
            mensaje_filtros += f"\n- Categoría: {categoria}"
        if entidad:
            mensaje_filtros += f"\n- Entidad: {entidad}"
            
        await cl.Message(
            content=mensaje_filtros,
            author="Sistema"
        ).send()

@cl.on_message
async def main(message: cl.Message):
    print(f"\n[BACKEND] --- ON MESSAGE TRIGGERED --- Content: {message.content!r}")
    print(f"[LLM INTERACTION] === NEW CHAT TURN ===")
    print(f"[LLM INTERACTION] --- Raw User Query: {message.content!r}")
    
    clean_query = message.content.strip().lower()
    
    # Guardar mensaje del usuario en sesión para inferencia de gráficos
    cl.user_session.set("last_user_message", message.content)
        
    # Mantener el resultado de herramientas de turnos anteriores para permitir graficar datos persistentes
    cl.user_session.set("chart_generated_in_turn", False)
    catalogo_consultado_en_este_turno = False
    
    # Recuperar variables de la sesión
    history = cl.user_session.get("history")
    openai_tools = cl.user_session.get("openai_tools")
    gerente = cl.user_session.get("gerente", "Gerente")
    print(f"[BACKEND] Gerente: {gerente!r}, History length: {len(history) if history else 0}, Tools count: {len(openai_tools) if openai_tools else 0}")
    
    # 1. Control de Consumo Justo
    if is_rate_limited():
        print("[BACKEND] Rate limited!")
        await cl.Message(
            content="⚠️ **Control de Consumo Justo:** He alcanzado mi límite de cuota para esta sesión (máximo 50 consultas en 10 minutos). Por favor, espere unos momentos antes de realizar otra consulta.",
            author="Sistema"
        ).send()
        return

    # 2. Caché de Preguntas Frecuentes (FAQ) deshabilitada para evitar colisiones al cambiar filtros

    # Guardar mensaje del usuario
    history.append({"role": "user", "content": message.content})
    print("[BACKEND] User message appended. Starting LLM loop...")
    
    # Variables de control de tokens del stream actual
    prompt_tokens = 0
    completion_tokens = 0
    active_model = "Desconocido"
    
    # Bucle de interacción con el LLM (por si solicita múltiples llamadas a herramientas)
    while True:
        # Obtener respuesta del LLM con el enrutador de resiliencia
        try:
            print(f"[LLM INTERACTION] --- Preparing messages. History length: {len(history) if history else 0}")
            print("[BACKEND] Calling stream_llm_response...")
            stream, active_model = await stream_llm_response(history, openai_tools)
            print(f"[BACKEND] stream_llm_response returned successfully. Active model: {active_model}")
            print(f"[LLM INTERACTION] --- Connection to LLM provider active. Model: {active_model}")
        except Exception as e:
            print(f"[BACKEND] stream_llm_response failed: {e}")
            await cl.Message(
                content=f"❌ **Error crítico de comunicación con el LLM:** {str(e)}\n"
                        "Por favor verifica tus claves de API (`LLM_API_KEY` o `GEMINI_API_KEY`) en el archivo `.env`.",
                author="Sistema"
            ).send()
            break
            
        full_text = ""
        tool_calls_chunks = {}
        msg = None
        
        # Procesar streaming de la respuesta
        print("[BACKEND] Iterating over stream chunks...")
        chunk_count = 0
        async for chunk in stream:
            chunk_count += 1
            # Capturar estadísticas de uso del token si el chunk final las incluye
            if getattr(chunk, "usage", None) is not None:
                prompt_tokens = chunk.usage.prompt_tokens
                completion_tokens = chunk.usage.completion_tokens
                
            if not chunk.choices:
                continue
                
            delta = chunk.choices[0].delta
            
            # Si el modelo envía texto, hacemos stream en pantalla
            if delta.content is not None:
                if msg is None:
                    print(f"[BACKEND] Creating cl.Message for stream (Author: Agente ({active_model}))...")
                    msg = cl.Message(content="", author=f"Agente ({active_model})")
                    await msg.send()
                full_text += delta.content
                await msg.stream_token(delta.content)
                
            # Si el modelo envía llamadas a herramientas, acumulamos los chunks
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx is None:
                        idx = 0
                    if idx not in tool_calls_chunks:
                        tool_calls_chunks[idx] = {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        }
                    if tc.id:
                        tool_calls_chunks[idx]["id"] = tc.id
                    if tc.function and tc.function.name:
                        tool_calls_chunks[idx]["function"]["name"] += tc.function.name
                    if tc.function and tc.function.arguments:
                        tool_calls_chunks[idx]["function"]["arguments"] += tc.function.arguments
                        
                    # Capturar extra_content / thought_signature de Gemini 3.x
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
        
        print(f"[BACKEND] Stream finished. Total chunks: {chunk_count}, msg created: {msg is not None}, tool calls count: {len(tool_calls_chunks)}")

        # Finalizar el streaming del mensaje si se envió texto
        if msg:
            await msg.update()
            
        # Si se identificaron llamadas a herramientas
        if tool_calls_chunks:
            tool_calls_list = [val for val in tool_calls_chunks.values()]
            
            # Registrar la intención del asistente en el historial
            history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls_list
            })
            
            # Ejecutar cada herramienta
            for tc in tool_calls_list:
                name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                
                try:
                    args = json.loads(raw_args) if raw_args else {}
                except Exception as je:
                    args = {"error": f"Invalid JSON arguments: {str(je)}", "raw": raw_args}
                    
                print(f"[LLM INTERACTION] --- Assistant requested execution of tool: {name!r}")
                print(f"[LLM INTERACTION] --- Tool arguments: {json.dumps(args, ensure_ascii=False)}")
                print(f"[BACKEND] Executing tool: {name!r} with args: {args}")
                if name == "crear_grafico":
                    async with cl.Step(name="Creando gráfico interactivo", type="tool") as step:
                        step.input = args
                        success, message_text = await run_local_chart_tool(args)
                        print(f"[BACKEND] Chart tool returned: success={success}, msg={message_text}")
                        if success:
                            step.output = "Gráfico generado y mostrado con éxito en el chat."
                            result = {"status": "success", "message": message_text}
                        else:
                            step.output = f"Error generando gráfico: {message_text}"
                            result = {"status": "error", "message": message_text}
                else:
                    # Crear un paso de ejecución en la UI de Chainlit para feedback al usuario
                    async with cl.Step(name=f"Ejecutando: {name}", type="tool") as step:
                        step.input = args
                        
                        try:
                            # Llamar al servidor de Osinergmin
                            result = run_local_tool(MCP_SERVER_URL, name, args)
                            if name == "get_catalogo_datos":
                                catalogo_consultado_en_este_turno = True
                            print(f"[BACKEND] Tool {name!r} returned output of length: {len(str(result))} (sample: {str(result)[:200]}...)")
                            
                            # Si es consulta de datos, construir compatibilidad con OSAM v1 para renderizar el componente dual (tabla/grafico) de la intranet
                            if name in ["query_data", "get_unidades", "get_unidades_por_ubigeo", "get_precios_combustible"] and isinstance(result, list) and len(result) > 0:
                                try:
                                    df = pd.DataFrame(result)
                                    osam_columns = []
                                    for col in df.columns:
                                        col_type = "NUMBER" if pd.api.types.is_numeric_dtype(df[col]) else "VARCHAR2"
                                        col_friendly = col.replace("NO_", "").replace("CO_", "").replace("DE_", "").replace("NU_", "").replace("FE_", "").replace("_", " ").title()
                                        osam_columns.append({
                                            "id": col,
                                            "name": col_friendly,
                                            "type": col_type
                                        })
                                    
                                    x_col = df.columns[0]
                                    y_col = df.columns[-1]
                                    for col in df.columns:
                                        if any(k in col.lower() for k in ["fecha", "date", "periodo", "anio"]):
                                            x_col = col
                                            break
                                    for col in df.columns:
                                        if col != x_col and pd.api.types.is_numeric_dtype(df[col]):
                                            y_col = col
                                            break
                                            
                                    chart_type = "line" if any(k in x_col.lower() for k in ["fecha", "date", "periodo", "anio"]) else "bar"
                                    
                                    report_payload = {
                                        "status": "success",
                                        "report": {
                                            "columns": osam_columns,
                                            "data": result,
                                            "presentation": {
                                                "chart": {
                                                    "type": chart_type,
                                                    "x": x_col,
                                                    "y": y_col
                                                },
                                                "default_view": "table"
                                            },
                                            "provenance": {
                                                "query_hash": f"mcp_query_{name}"
                                            }
                                        }
                                    }
                                    cl.user_session.set("last_osam_payload", report_payload)
                                    print(f"[BACKEND] Guardado payload de compatibilidad OSAM para {name}")
                                except Exception as payload_err:
                                    print(f"[BACKEND WARNING] No se pudo generar payload de compatibilidad OSAM: {payload_err}")
                            
                            # Mostrar resultados en la UI
                            if isinstance(result, list):
                                step.output = f"Se recuperaron {len(result)} registros.\n\n" + json.dumps(result[:3], indent=2) + "\n\n*(mostrando primeros 3 registros)*"
                            else:
                                step.output = json.dumps(result, indent=2)
                        except Exception as e:
                            print(f"[BACKEND ERROR] Error al ejecutar la herramienta real {name!r}: {e}")
                            
                            # Manejo de fallos con degradación segura de metadatos
                            if name == "get_catalogo_datos":
                                catalogo_consultado_en_este_turno = True
                                result = cl.user_session.get("catalogo_completo") or []
                                step.output = f"⚠️ Nota: El servidor MCP en vivo no responde (Timeout). Utilizando catálogo de respaldo local.\n\n" + json.dumps(result[:3], indent=2) + "\n\n*(mostrando primeros 3 registros)*"
                            elif name == "get_detalle_catalogo_datos":
                                # Buscar los metadatos de las columnas en la caché semántica local
                                target_id = args.get("id_catalogo") or 0
                                table_name_arg = args.get("table_name", "").upper()
                                
                                # Intentar buscar por ID de catálogo o por nombre
                                catalog_dict = get_semantic_catalog()
                                found_cols = []
                                found_table = ""
                                
                                for t_name, t_data in catalog_dict.get("tables", {}).items():
                                    t_id = t_data.get("id_catalogo") or t_data.get("ID_CATALOGO_DATO")
                                    if (target_id and t_id and int(t_id) == int(target_id)) or (table_name_arg and t_name == table_name_arg):
                                        found_cols = t_data.get("columns", [])
                                        found_table = t_name
                                        break
                                        
                                if found_cols:
                                    result = {
                                        "table_name": found_table,
                                        "columns": [
                                            {
                                                "name": col["name"],
                                                "type": col.get("type", "VARCHAR2"),
                                                "description": col.get("description", ""),
                                                "show": True
                                            }
                                            for col in found_cols
                                        ]
                                    }
                                    step.output = f"⚠️ Nota: El servidor MCP en vivo no responde (Timeout). Utilizando columnas de respaldo local para {found_table}.\n\n" + json.dumps(result, indent=2)
                                else:
                                    result = {"error": f"No se pudieron obtener columnas para el catálogo {target_id or table_name_arg}."}
                                    step.output = f"❌ Error: {e}\nNo hay columnas en la caché local para esta tabla."
                            else:
                                # Si falla get_unidades u otra de datos en vivo, devolvemos un mensaje de error limpio al LLM
                                result = {"error": f"La herramienta {name} no pudo completarse debido a un fallo de red o timeout en el servidor MCP."}
                                step.output = f"❌ Error de Conexión: {e}"
                        
                # Registrar el resultado de la herramienta en el historial del chat
                history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": name,
                    "content": json.dumps(result)
                })
                if name != "crear_grafico":
                    cl.user_session.set("last_tool_result", result)
                if name == "get_catalogo_datos" and isinstance(result, list):
                    cl.user_session.set("catalogo_completo", result)
                
            # Continuar en el bucle para que el LLM reciba los resultados de la herramienta
            continue
        else:
            # Si no hubo llamadas a herramientas, guardamos la respuesta de texto y terminamos
            history.append({
                "role": "assistant",
                "content": full_text
            })
            cl.user_session.set("history", history)
            
            # --- VALIDACIÓN Y LOGS DE COMPONENTES GENERADOS EN EL TEXTO ---
            print(f"[LLM INTERACTION] --- Final Assistant text response saved in session history.")
            
            # Buscar json-osam block
            if "```json-osam" in full_text:
                print(f"[COMPONENT GENERATION] --- Found code block: 'json-osam' in message content.")
                try:
                    # Extraer JSON
                    start_pos = full_text.find("```json-osam") + 12
                    end_pos = full_text.find("```", start_pos)
                    if end_pos != -1:
                        json_str = full_text[start_pos:end_pos].strip()
                        parsed_osam = json.loads(json_str)
                        print(f"[COMPONENT GENERATION] --- Parsed json-osam block successfully:")
                        
                        report_data = parsed_osam.get("report") or {}
                        analysis_data = parsed_osam.get("analysis") or {}
                        
                        # --- AUTO-REPARACIÓN DE PRESENTACIÓN Y CASING ---
                        saved_payload = cl.user_session.get("last_osam_payload") or {}
                        saved_report = saved_payload.get("report") or {}
                        saved_presentation = saved_report.get("presentation")
                        
                        if saved_presentation:
                            curr_pres = report_data.get("presentation") or {}
                            curr_chart = curr_pres.get("chart") or {}
                            
                            # Si falta o está desactivado
                            if not curr_chart or curr_chart.get("type", "none") == "none":
                                report_data["presentation"] = saved_presentation
                                print("[COMPONENT GENERATION] --- Auto-repair: Re-injected presentation from session payload.")
                            else:
                                # Alinear casing de los campos x e y en el chart con los nombres reales en columns
                                col_ids_upper = {col["id"].upper(): col["id"] for col in report_data.get("columns", [])}
                                
                                x_field = curr_chart.get("x")
                                if x_field and x_field.upper() in col_ids_upper:
                                    curr_chart["x"] = col_ids_upper[x_field.upper()]
                                    
                                y_field = curr_chart.get("y")
                                if y_field and y_field.upper() in col_ids_upper:
                                    curr_chart["y"] = col_ids_upper[y_field.upper()]
                                    
                                curr_pres["chart"] = curr_chart
                                report_data["presentation"] = curr_pres
                                
                            parsed_osam["report"] = report_data
                            
                            # Re-serializar y actualizar la respuesta
                            new_json_str = json.dumps(parsed_osam, ensure_ascii=False, indent=2)
                            new_full_text = full_text[:start_pos] + "\n" + new_json_str + "\n" + full_text[end_pos:]
                            full_text = new_full_text
                            
                            # Actualizar el mensaje de Chainlit
                            if msg:
                                msg.content = new_full_text
                                await msg.update()
                                print("[COMPONENT GENERATION] --- Auto-repair: Updated client message with repaired presentation schema.")
                        
                        # Recargar report_data del objeto parseado (posiblemente reparado)
                        report_data = parsed_osam.get("report") or {}
                        
                        print(f"  - Report status: Present (Data records: {len(report_data.get('data', []))})")
                        print(f"  - Columns count: {len(report_data.get('columns', []))}")
                        
                        chart_info = report_data.get("presentation", {}).get("chart", {})
                        print(f"  - Chart status: {chart_info.get('type', 'none')} (X: {chart_info.get('x')}, Y: {chart_info.get('y')})")
                        
                        insights_list = analysis_data.get("insights", [])
                        print(f"  - AI Insights count: {len(insights_list)}")
                        for idx, ins in enumerate(insights_list):
                            print(f"    Insight {idx+1}: [{ins.get('type')}] {ins.get('text')}")
                except Exception as parse_err:
                    print(f"[COMPONENT ERROR] --- Failed to parse 'json-osam' block: {parse_err}")
            else:
                print(f"[COMPONENT WARNING] --- Message does NOT contain json-osam block. Only plain text rendered.")
            
            if "```json-chart" in full_text:
                print(f"[COMPONENT GENERATION] --- Found code block: 'json-chart' (matplotlib fallback) in message content.")
                try:
                    start_pos = full_text.find("```json-chart") + 13
                    end_pos = full_text.find("```", start_pos)
                    if end_pos != -1:
                        json_str = full_text[start_pos:end_pos].strip()
                        parsed_chart = json.loads(json_str)
                        print(f"[COMPONENT GENERATION] --- Parsed json-chart block successfully: Type: {parsed_chart.get('type')}")
                except Exception as parse_err:
                    print(f"[COMPONENT ERROR] --- Failed to parse 'json-chart' block: {parse_err}")
            
            # Guardar en caché omitido (caché deshabilitada)
            
            # Registrar en log_uso.txt
            log_usage(gerente, active_model, message.content, prompt_tokens, completion_tokens)
            
            # --- DETECCIÓN Y GENERACIÓN AUTOMÁTICA DE GRÁFICOS (FALLBACK) ---
            chart_keywords = ["grafic", "tendencia", "curva", "evolucion", "plot", "gráfico", "grafique", "evolución"]
            last_result = cl.user_session.get("last_tool_result")
            chart_already_generated = cl.user_session.get("chart_generated_in_turn", False)
            
            # Extraer lista de registros de forma robusta
            data_list = None
            if isinstance(last_result, list):
                data_list = last_result
            elif isinstance(last_result, dict):
                data_list = last_result.get("report", {}).get("data")
                
            if not chart_already_generated and any(kw in clean_query for kw in chart_keywords) and isinstance(data_list, list) and len(data_list) > 0:
                chart_path = try_generate_chart(data_list, message.content)
                chart_json = try_generate_chart_json(data_list, message.content)
                
                chart_block = ""
                if chart_json:
                    chart_block = f"\n\n```json-chart\n{json.dumps(chart_json, ensure_ascii=False, indent=2)}\n```"
                
                if chart_block:
                    if chart_path:
                        # Enviar el gráfico generado como elemento inline en Chainlit junto al bloque interactivo
                        image_element = cl.Image(path=chart_path, name="tendencia", display="inline")
                        if msg:
                            msg.elements = [image_element]
                            msg.content += chart_block
                            await msg.update()
                        else:
                            await cl.Message(
                                content="Aquí tiene el gráfico de la tendencia basado en los datos recuperados:" + chart_block,
                                elements=[image_element],
                                author=f"Agente ({active_model})"
                            ).send()
                    else:
                        # Si falló la exportación de imagen estática (ej: falta kaleido), enviamos solo el bloque interactivo
                        if msg:
                            msg.content += chart_block
                            await msg.update()
                        else:
                            await cl.Message(
                                content="Aquí tiene el gráfico de la tendencia basado en los datos recuperados:" + chart_block,
                                author=f"Agente ({active_model})"
                            ).send()
                        
            # 1. Obtener la lista completa de tablas del catálogo que tengamos en sesión
            catalogo_completo = cl.user_session.get("catalogo_completo")
            if not isinstance(catalogo_completo, list) or len(catalogo_completo) == 0:
                try:
                    catalog_dict = get_semantic_catalog()
                    catalogo_completo = [
                        {
                            "table_name": k,
                            "description": v.get("description", ""),
                            "NO_TABLA": k,
                            "DE_TABLA": v.get("description", ""),
                            "id_catalogo": int(v.get("id_catalogo") or 0)
                        }
                        for k, v in catalog_dict.get("tables", {}).items()
                    ]
                    cl.user_session.set("catalogo_completo", catalogo_completo)
                    print(f"[BACKEND] Catálogo cargado en sesión ({len(catalogo_completo)} elementos desde Registro Semántico) para escaneo.")
                except Exception as ex:
                    print(f"[BACKEND WARNING] Error al cargar catálogo de escaneo: {ex}")
                    catalogo_completo = []
                
            # 2. Buscar menciones de tablas en el texto final de la respuesta del asistente (full_text)
            import re
            content_text = full_text or ""
            
            # Extraer posibles palabras en mayúsculas y minúsculas (de longitud >= 4)
            palabras_raw = re.findall(r'\b[a-zA-Z0-9_]{4,}\b', content_text)
            palabras = list(dict.fromkeys([p.upper() for p in palabras_raw]))
            
            # Extraer números de 4 dígitos (posibles IDs de catálogo)
            numeros = re.findall(r'\b\d{4}\b', content_text)
            numeros = list(dict.fromkeys(numeros))
            
            datasets_list = []
            tablas_agregadas = set()
            
            # A) Buscar por coincidencia de ID_CATALOGO_DATO
            for num in numeros:
                try:
                    num_int = int(num)
                    for item in catalogo_completo:
                        id_catalogo = item.get("ID_CATALOGO_DATO")
                        if id_catalogo is not None:
                            try:
                                if int(id_catalogo) == num_int:
                                    name_in_item = item.get("NO_TABLA") or item.get("table_name") or item.get("name") or ""
                                    if name_in_item and name_in_item.upper() not in tablas_agregadas:
                                        table_name = name_in_item
                                        description = item.get("DE_TABLA") or item.get("description") or item.get("desc") or "Tabla de datos de Osinergmin."
                                        datasets_list.append({
                                            "title": table_name,
                                            "description": description,
                                            "format": "SQL Table",
                                            "license": "Osinergmin",
                                            "organization": "Gobernanza de Datos",
                                            "schema": item.get("NO_ESQUEMA_ORIGEN") or item.get("schema") or "ES_DATGOB_CV",
                                            "id_catalogo": int(item.get("ID_CATALOGO_DATO") or item.get("id_catalogo") or num_int)
                                        })
                                        tablas_agregadas.add(name_in_item.upper())
                                        break
                            except ValueError:
                                pass
                except ValueError:
                    pass
            
            # B) Buscar coincidencia exacta con tablas del catálogo real (por nombre)
            for palabra in palabras:
                for item in catalogo_completo:
                    name_in_item = item.get("NO_TABLA") or item.get("table_name") or item.get("name") or ""
                    if name_in_item and name_in_item.upper() == palabra.upper() and name_in_item.upper() not in tablas_agregadas:
                        table_name = name_in_item
                        description = item.get("DE_TABLA") or item.get("description") or item.get("desc") or "Tabla de datos de Osinergmin."
                        datasets_list.append({
                            "title": table_name,
                            "description": description,
                            "format": "SQL Table",
                            "license": "Osinergmin",
                            "organization": "Gobernanza de Datos",
                            "schema": item.get("NO_ESQUEMA_ORIGEN") or item.get("schema") or "ES_DATGOB_CV",
                            "id_catalogo": int(item.get("ID_CATALOGO_DATO") or item.get("id_catalogo") or 0)
                        })
                        tablas_agregadas.add(name_in_item.upper())
                        break
                        
            # 3. Inyectar el bloque de datasets si encontramos elementos
            if datasets_list:
                datasets_block = f"\n\n```json-datasets\n{json.dumps(datasets_list, ensure_ascii=False, indent=2)}\n```"
                if msg:
                    msg.content += datasets_block
                    await msg.update()
                else:
                    await cl.Message(
                        content="Aquí están los conjuntos de datos gobernados encontrados en el catálogo:" + datasets_block,
                        author=f"Agente ({active_model})"
                    ).send()
            break
