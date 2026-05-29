import os
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

9. PROCESO INTERNO DE DESCUBRIMIENTO DE DATOS (PARA TU USO INTERNO COMO LLM):
- Si el usuario te solicita datos, tendencias, gráficos o análisis específicos, y no conoces la tabla o ID, DEBES llamar primero a la herramienta `get_catalogo_datos` para identificar el dataset correspondiente en el catálogo.
- Inmediatamente después de obtener la lista del catálogo, debes analizarla, seleccionar la tabla idónea (ej: `CMO_TX_CENTRAL_GEN` para centrales o empresas eléctricas, `VW_EESS_UBICACION_GEO` para estaciones de servicio, etc.), llamar a `get_detalle_catalogo_datos` para ver sus columnas, y luego ejecutar `query_data` con los filtros correspondientes (ej: `filters: {"NO_DEPARTAMENTO": "HUANUCO"}`).
- Todo este flujo de llamadas a herramientas (`get_catalogo_datos` -> `get_detalle_catalogo_datos` -> `query_data`) debe ser ejecutado en forma continua y encadenada en un solo turno, sin detenerse a preguntarle nada al usuario, hasta obtener los datos y poder responderle con la respuesta final.
- Queda prohibido inventar o alucinar nombres de tablas, esquemas, columnas o IDs de catálogo. Búscalos siempre mediante las herramientas.

10. AUTONOMÍA EJECUTIVA ABSOLUTA (PROHIBIDO PREGUNTAR DETALLES TÉCNICOS O PEDIR PERMISOS):
- NO le preguntes al usuario si desea que consultes la tabla o si debes ejecutar la herramienta. Procede a realizar la cadena de consultas del catálogo y la base de datos de forma autónoma e inmediata.
- NO le pidas al usuario nombres de columnas, tipos de datos o parámetros de base de datos. Obtén esta información consultando los detalles de la tabla de forma silenciosa.
- El usuario es un gerente/director de negocio y no conoce el modelo de base de datos, por lo que tú debes resolver toda la capa técnica de forma autónoma e interna y entregarle el dato final consultado.
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
    Envía la solicitud al proveedor (Google AI Studio o OpenRouter) con resiliencia y reintentos.
    Si el modelo principal falla, intenta secuencialmente con los de respaldo.
    """
    # Recargar variables de entorno dinámicamente para capturar cambios en .env (como la API key o GEMINI_MODEL) sin reiniciar el servidor
    load_dotenv(dotenv_path, override=True)
    
    # Clonar y adaptar mensajes dinámicamente con contexto de datos
    injected_messages = list(messages)
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

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or LLM_API_KEY
    
    # Detección automática del proveedor basado en la clave de API
    if api_key and (api_key.startswith("AIzaSy") or "gemini" in api_key.lower()):
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        
        # Cargar los modelos dinámicamente desde el .env si la variable está definida
        env_models = os.getenv("GEMINI_MODEL")
        if env_models:
            models = [m.strip() for m in env_models.split(",") if m.strip()]
        else:
            models = [
                "gemini-2.5-flash-lite", 
                "gemini-2.5-flash"
            ]
        provider_name = "Google AI Studio (Gemini)"
    else:
        base_url = "https://openrouter.ai/api/v1"
        models = [
            "deepseek/deepseek-v4-flash:free",
            "google/gemma-4-31b-it:free",
            "qwen/qwen3-next-80b-a3b-instruct:free"
        ]
        provider_name = "OpenRouter"

    # max_retries=0 desactiva los reintentos automáticos internos de la librería openai (que son rápidos y empeoran el 429)
    client = openai.AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        max_retries=0
    )
    
    for idx, model in enumerate(models):
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Espera más larga (4 segundos) ante saturación (429) para dejar que se limpie la cuota por segundo/minuto
                    await asyncio.sleep(4)
                    
                kwargs = {
                    "model": model,
                    "messages": injected_messages,
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
                is_rate_limit = "429" in str(e) or "rate" in str(e).lower()
                if is_rate_limit and attempt < max_retries - 1:
                    continue
                
                # Ocultar prints ruidosos a consola, solo reportar el fallo final silencioso
                if idx == len(models) - 1:
                    raise e
                break

# ----------------- Generador Automático de Gráficos -----------------

import matplotlib
matplotlib.use('Agg') # Evitar que matplotlib intente abrir una interfaz GUI
import matplotlib.pyplot as plt

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
            
        # Generar el gráfico
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Estilos modernos y elegantes
        ax.plot(plot_df[x_col].astype(str), plot_df[y_col], marker='o', linewidth=2, color='#0D6EFD', label=y_col)
        
        # Títulos limpios
        title_x = str(x_col).replace('_', ' ').title()
        title_y = str(y_col).replace('_', ' ').title()
        
        ax.set_title(f"Evolución / Tendencia de {title_y} por {title_x}", fontsize=13, fontweight='bold', pad=15)
        ax.set_xlabel(title_x, fontsize=10, labelpad=8)
        ax.set_ylabel(title_y, fontsize=10, labelpad=8)
        
        # Rotar etiquetas del eje X si son largas
        plt.xticks(rotation=45, ha='right')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        plt.tight_layout()
        
        # Crear directorio temporal si no existe
        temp_dir = os.path.join(current_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        chart_path = os.path.join(temp_dir, "last_trend_chart.png")
        plt.savefig(chart_path, dpi=150)
        plt.close(fig)
        
        return chart_path
    except Exception as e:
        print(f"Error generando gráfico automático: {e}")
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
            
        # ---- CONTROL HUMAN-IN-THE-LOOP (HITL) ----
        actions = [
            cl.Action(name="approve_chart", value="yes", label="📊 Sí, generar gráfico", description="Permite renderizar el gráfico en el chat.", payload={}),
            cl.Action(name="cancel_chart", value="no", label="❌ Cancelar", description="Aborta la creación del gráfico.", payload={})
        ]
        
        res = await cl.AskActionMessage(
            content=f"⚠️ **Confirmación Requerida (HITL):** El copiloto solicita generar un gráfico de tipo **{tipo}** para la columna **{y_col}** vs **{x_col}**. ¿Desea proceder?",
            actions=actions,
            timeout=60
        ).send()
        
        if not res or res.get("value") != "yes":
            return False, "Operación cancelada por el usuario. El gráfico no fue generado."
            
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
        
        # Enviar elemento inline cl.Pyplot
        pyplot_element = cl.Pyplot(figure=fig, name="grafico", display="inline")
        await cl.Message(
            content=f"📊 **Gráfico generado:** {titulo}",
            elements=[pyplot_element],
            author="Sistema"
        ).send()
        
        plt.close(fig)
        cl.user_session.set("chart_generated_in_turn", True)
        return True, f"Gráfico de tipo '{tipo}' generado con éxito para {y_col} vs {x_col}."
    except Exception as e:
        return False, f"Error al crear el gráfico: {str(e)}"

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
    cl.user_session.set("faq_cache", {})

    # Cargar y almacenar herramientas del servidor en la sesión (Caché de MCP al arrancar)
    with cl.Step(name="Inicializando herramientas MCP", type="system") as step:
        step.input = "Consultando catálogo de Osinergmin..."
        openai_tools = fetch_tools_from_server(MCP_SERVER_URL)
        
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
                values=["Todas", "Amazonas", "Ancash", "Apurímac", "Arequipa", "Ayacucho", "Cajamarca", "Callao", "Cusco", "Huancavelica", "Huánuco", "Ica", "Junín", "La Libertad", "Lambayeque", "Lima", "Loreto", "Madre de Dios", "Moquegua", "Pasco", "Piura", "Puno", "San Martín", "Tacna", "Tumbes", "Ucayali"],
                initial_index=18, # Moquegua
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
    # Guardamos los filtros en la sesión para poder inyectarlos en el prompt del sistema o pasarlos al backend
    cl.user_session.set("filtros_activos", settings)
    
    ubicacion = settings.get("ubicacion")
    periodo = settings.get("periodo")
    categoria = ", ".join(settings.get("categoria", []))
    entidad = ", ".join(settings.get("entidad", []))
    
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
    # Mantener el resultado de herramientas de turnos anteriores para permitir graficar datos persistentes
    cl.user_session.set("chart_generated_in_turn", False)
    clean_query = message.content.strip().lower()
    
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

    # 2. Caché de Preguntas Frecuentes (FAQ) de la Sesión
    faq_cache = cl.user_session.get("faq_cache", {})
    cached_data = find_fuzzy_match(message.content, faq_cache)
    if cached_data:
        cached_ans = cached_data["response"]
        cached_model = cached_data["model"]
        
        # Enviar directamente al chat para no romper la inmersión (sin prefijos técnicos de caché)
        await cl.Message(
            content=cached_ans,
            author=f"Agente ({cached_model})"
        ).send()
        
        # Loguear en log_uso.txt indicando uso de caché
        log_usage(gerente, f"Caché Sesión ({cached_model})", message.content, 0, 0)
        
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
                content=f"❌ **Error crítico de comunicación con el LLM:** {str(e)}\n"
                        "Por favor verifica tus claves de API (`LLM_API_KEY` o `GEMINI_API_KEY`) en el archivo `.env`.",
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
                    
                if name == "crear_grafico":
                    async with cl.Step(name="Creando gráfico interactivo", type="tool") as step:
                        step.input = args
                        success, message_text = await run_local_chart_tool(args)
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
                if name != "crear_grafico":
                    cl.user_session.set("last_tool_result", result)
                
            # Continuar en el bucle para que el LLM reciba los resultados de la herramienta
            continue
        else:
            # Si no hubo llamadas a herramientas, guardamos la respuesta de texto y terminamos
            history.append({
                "role": "assistant",
                "content": full_text
            })
            cl.user_session.set("history", history)
            
            # Guardar en el caché de la sesión de usuario
            faq_cache = cl.user_session.get("faq_cache", {})
            faq_cache[message.content] = {"response": full_text, "model": active_model}
            cl.user_session.set("faq_cache", faq_cache)
            
            # Registrar en log_uso.txt
            log_usage(gerente, active_model, message.content, prompt_tokens, completion_tokens)
            
            # --- DETECCIÓN Y GENERACIÓN AUTOMÁTICA DE GRÁFICOS (FALLBACK) ---
            chart_keywords = ["grafic", "tendencia", "curva", "evolucion", "plot", "gráfico", "grafique", "evolución"]
            last_result = cl.user_session.get("last_tool_result")
            chart_already_generated = cl.user_session.get("chart_generated_in_turn", False)
            
            if not chart_already_generated and any(kw in clean_query for kw in chart_keywords) and isinstance(last_result, list) and len(last_result) > 0:
                chart_path = try_generate_chart(last_result, message.content)
                if chart_path:
                    # Enviar el gráfico generado como elemento inline en Chainlit
                    image_element = cl.Image(path=chart_path, name="tendencia", display="inline")
                    if msg:
                        msg.elements = [image_element]
                        await msg.update()
                    else:
                        await cl.Message(
                            content="Aquí tiene el gráfico de la tendencia basado en los datos recuperados:",
                            elements=[image_element],
                            author=f"Agente ({active_model})"
                        ).send()
            break
