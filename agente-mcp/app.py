import os
from dotenv import load_dotenv

# Cargar .env de forma robusta desde la raíz del proyecto (directorio padre) antes de importar Chainlit
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
dotenv_path = os.path.join(parent_dir, ".env")
load_dotenv(dotenv_path, override=True)

import requests
import json
import time
import chainlit as cl
import openai
import pandas as pd
from datetime import datetime

# Configuración del Prompt del Sistema institucional
SYSTEM_PROMPT = """
Eres un Asistente Ejecutivo de Inteligencia de Datos en Osinergmin. 
Tu objetivo es proporcionar análisis precisos basándote en herramientas MCP.
- Eres técnico pero claro.
- Si no tienes datos suficientes, indica la fuente faltante.
- Si una consulta requiere acceso a datos sensibles, prioriza la seguridad.
- Tu estilo es: Profesional, analítico y directo.
"""

# Configuración de URLs y credenciales
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

# Caché global en memoria para preguntas frecuentes (FAQ)
FAQ_CACHE = {}

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
    y las mapea al formato de tools (funciones) que espera la API de OpenAI/OpenRouter.
    """
    url = f"{base_url}/tools/list"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            raw_tools = r.json()
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
        else:
            print(f"Error al listar herramientas: Código {r.status_code}")
            return []
    except Exception as e:
        print(f"Error conectando al servidor para listar herramientas: {e}")
        return []

# ----------------- Ejecución Local de Herramientas -----------------

def run_local_tool(base_url, name, args):
    """
    Ejecuta la herramienta correspondiente llamando a los endpoints REST del backend
    y adaptando los esquemas si es necesario.
    """
    url = f"{base_url}/tools/{name}"
    
    # Adaptar parámetros para query_data (de MCP a REST)
    if name == "query_data":
        if "schema" in args:
            args["schema_name"] = args.pop("schema")
        if "table" in args:
            args["table_name"] = args.pop("table")
            
    try:
        # get_unidades y list se llaman vía GET, los demás vía POST
        if name in ["get_unidades", "list"]:
            r = requests.get(url, params=args, timeout=20)
        else:
            r = requests.post(url, json=args, timeout=20)
            
        if r.status_code == 200:
            return r.json()
        else:
            return {"error": f"Error del servidor (código {r.status_code})", "detail": r.text}
    except Exception as e:
        return {"error": "Error de conexión con el servidor", "detail": str(e)}

# ----------------- Enrutador de Resiliencia del LLM -----------------

async def stream_llm_response(messages, tools=None):
    """
    Envía la solicitud a OpenRouter con una lista ordenada de modelos.
    Si el modelo principal falla, intenta secuencialmente con los modelos de respaldo.
    Intenta solicitar el conteo exacto de tokens si el modelo lo permite.
    """
    models = [
        "meta-llama/llama-3.3-70b-instruct",
        "google/gemini-2.5-flash",
        "anthropic/claude-3-haiku",
        "openai/gpt-4o-mini"
    ]
    
    api_key = os.getenv("LLM_API_KEY") or LLM_API_KEY
    client = openai.AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    
    for idx, model in enumerate(models):
        try:
            if idx > 0:
                await cl.Message(
                    content=f"⚠️ *El modelo anterior no respondió.* Intentando conectar con modelo de respaldo: `{model}`...",
                    author="Sistema"
                ).send()
                
            kwargs = {
                "model": model,
                "messages": messages,
                "stream": True,
                "stream_options": {"include_usage": True}
            }
            if tools:
                kwargs["tools"] = tools
                
            try:
                stream = await client.chat.completions.create(**kwargs)
            except Exception as inner_e:
                # Si el modelo/proveedor no soporta stream_options, reintentar sin eso
                if "stream_options" in kwargs:
                    del kwargs["stream_options"]
                    stream = await client.chat.completions.create(**kwargs)
                else:
                    raise inner_e
                    
            return stream, model
        except Exception as e:
            print(f"Fallo con modelo {model}: {e}")
            if idx == len(models) - 1:
                raise e

# ----------------- Autenticación de Usuarios (Login) -----------------

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """
    Función de autenticación para los gerentes de Osinergmin.
    Define las credenciales autorizadas de prueba para la demo.
    """
    valid_users = {
        "admin": "admin2026",
        "gerente_comercial": "comercial2026",
        "gerente_operaciones": "operaciones2026"
    }
    
    if username in valid_users and valid_users[username] == password:
        return cl.User(identifier=username, username=username)
    return None

# ----------------- Eventos de Chainlit -----------------

@cl.on_chat_start
async def start():
    # Obtener el nombre del gerente desde la sesión autenticada de forma robusta
    user = cl.user_session.get("user")
    gerente_name = "Gerente"
    if user:
        gerente_name = getattr(user, "username", None) or getattr(user, "identifier", "Gerente")
        
    cl.user_session.set("gerente", gerente_name)
    cl.user_session.set("message_timestamps", [])

    # Cargar y almacenar herramientas del servidor en la sesión (Caché de MCP al arrancar)
    with cl.Step(name="Inicializando herramientas MCP", type="system") as step:
        step.input = "Consultando catálogo de Osinergmin..."
        openai_tools = fetch_tools_from_server(MCP_SERVER_URL)
        cl.user_session.set("openai_tools", openai_tools)
        
        if openai_tools:
            tools_list_desc = "\n".join([f"- **{t['function']['name']}**: {t['function']['description']}" for t in openai_tools])
            step.output = f"Se cargaron {len(openai_tools)} herramientas:\n{tools_list_desc}"
        else:
            step.output = "⚠️ Advertencia: No se pudieron precargar las herramientas del servidor. Verifica la URL en .env"

    # Inicializar historial de conversación con el System Prompt
    cl.user_session.set("history", [
        {"role": "system", "content": SYSTEM_PROMPT}
    ])
    
    # Mensaje estético de bienvenida
    await cl.Message(
        content=f"💼 Bienvenido **{gerente_name}**, soy su asistente ejecutivo de inteligencia de datos en Osinergmin. "
                "Estoy listo para asistirte con tus consultas en lenguaje natural sobre nuestros datos gobernados.",
        author="Sistema"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    # Recuperar variables de la sesión
    history = cl.user_session.get("history")
    openai_tools = cl.user_session.get("openai_tools")
    gerente = cl.user_session.get("gerente", "Gerente")
    
    # 1. Control de Consumo Justo
    if is_rate_limited():
        await cl.Message(
            content="⚠️ **Control de Consumo Justo:** He alcanzado mi límite de cuota para esta sesión (máximo 50 consultas en 10 minutos). Por favor, espere unos momentos antes de realizar otra consulta.",
            author="Sistema"
        ).send()
        return

    # 2. Caché de Preguntas Frecuentes (FAQ)
    clean_query = message.content.strip().lower()
    if clean_query in FAQ_CACHE:
        cached_ans = FAQ_CACHE[clean_query]
        await cl.Message(
            content=f"ℹ️ **[Caché FAQ]** Respuesta recuperada de consultas frecuentes:\n\n{cached_ans}",
            author=f"Agente ({gerente})"
        ).send()
        
        # Loguear en log_uso.txt indicando uso de caché
        log_usage(gerente, "Caché FAQ", message.content, 0, 0)
        
        # Añadir al historial para consistencia
        history.append({"role": "user", "content": message.content})
        history.append({"role": "assistant", "content": cached_ans})
        cl.user_session.set("history", history)
        return

    # Guardar mensaje del usuario
    history.append({"role": "user", "content": message.content})
    
    # Variables de control de tokens del stream actual
    prompt_tokens = 0
    completion_tokens = 0
    active_model = "Desconocido"
    
    # Bucle de interacción con el LLM (por si solicita múltiples llamadas a herramientas)
    while True:
        # Obtener respuesta del LLM con el enrutador de resiliencia
        try:
            stream, active_model = await stream_llm_response(history, openai_tools)
        except Exception as e:
            await cl.Message(
                content=f"❌ **Error crítico de comunicación con OpenRouter:** {str(e)}\n"
                        "Por favor verifica tu `LLM_API_KEY` en el archivo `.env`.",
                author="Sistema"
            ).send()
            break
            
        full_text = ""
        tool_calls_chunks = {}
        msg = None
        
        # Procesar streaming de la respuesta
        async for chunk in stream:
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
                    msg = cl.Message(content="", author=f"Agente ({active_model})")
                    await msg.send()
                full_text += delta.content
                await msg.stream_token(delta.content)
                
            # Si el modelo envía llamadas a herramientas, acumulamos los chunks
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
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
                    
                # Crear un paso de ejecución en la UI de Chainlit para feedback al usuario
                async with cl.Step(name=f"Ejecutando: {name}", type="tool") as step:
                    step.input = args
                    
                    # Llamar localmente al servidor de Osinergmin
                    result = run_local_tool(MCP_SERVER_URL, name, args)
                    
                    # Mostrar resultados en la UI
                    if isinstance(result, list):
                        step.output = f"Se recuperaron {len(result)} registros.\n\n" + json.dumps(result[:3], indent=2) + "\n\n*(mostrando primeros 3 registros)*"
                    else:
                        step.output = json.dumps(result, indent=2)
                        
                # Registrar el resultado de la herramienta en el historial del chat
                history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": name,
                    "content": json.dumps(result)
                })
                
            # Continuar en el bucle para que el LLM reciba los resultados de la herramienta
            continue
        else:
            # Si no hubo llamadas a herramientas, guardamos la respuesta de texto y terminamos
            history.append({
                "role": "assistant",
                "content": full_text
            })
            cl.user_session.set("history", history)
            
            # Guardar en el caché global de preguntas frecuentes
            FAQ_CACHE[clean_query] = full_text
            
            # Registrar en log_uso.txt
            log_usage(gerente, active_model, message.content, prompt_tokens, completion_tokens)
            break
