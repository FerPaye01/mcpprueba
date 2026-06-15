# agente-mcp/semantic_registry.py
import os
import requests
import json
import asyncio
import httpx
import threading
import queue
import sys
from dotenv import load_dotenv

# Asegurar soporte de asyncio loop en Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Cargar variables de entorno
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(parent_dir, ".env"), override=True)

# Obtener URL del catálogo MCP
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

# Caché en memoria del catálogo
_cached_catalog = None


# ----------------- Cliente MCP SSE Personalizado (Defensivo y Resiliente) -----------------

class CustomSseMcpClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.sse_url = f"{base_url}/sse" if not base_url.endswith("/sse") else base_url
        if self.base_url.endswith("/sse"):
            self.base_url = self.base_url[:-4]
        self.post_url = None
        self.client = httpx.AsyncClient(timeout=30.0)
        self.pending_responses = {}
        self.request_id = 0
        self.read_task = None
        self.connected_event = asyncio.Event()

    async def connect(self):
        self.read_task = asyncio.create_task(self._read_stream())
        try:
            await asyncio.wait_for(self.connected_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            raise RuntimeError("Timeout esperando el endpoint en el stream SSE.")

    async def _read_stream(self):
        try:
            async with self.client.stream("GET", self.sse_url) as response:
                current_event = None
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_content = line[5:].strip()
                        if current_event == "endpoint":
                            if data_content.startswith("http"):
                                self.post_url = data_content
                            else:
                                self.post_url = f"{self.base_url}{data_content}"
                            self.connected_event.set()
                        elif current_event == "message":
                            await self._handle_message(data_content)
                        current_event = None
        except Exception:
            self.connected_event.set()

    async def _handle_message(self, raw_msg):
        try:
            msg = json.loads(raw_msg)
            msg_id = msg.get("id")
            if msg_id is not None:
                future = self.pending_responses.pop(msg_id, None)
                if future and not future.done():
                    future.set_result(msg)
        except Exception:
            pass

    async def send_request(self, method, params):
        self.request_id += 1
        rid = self.request_id
        payload = {
            "jsonrpc": "2.0",
            "id": rid,
            "method": method,
            "params": params
        }
        future = asyncio.get_running_loop().create_future()
        self.pending_responses[rid] = future
        r = await self.client.post(self.post_url, json=payload)
        if r.status_code not in [200, 202]:
            self.pending_responses.pop(rid, None)
            raise RuntimeError(f"Fallo en POST a {self.post_url}: HTTP {r.status_code} - {r.text}")
        response = await future
        return response

    async def initialize(self):
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "CustomSseMcpClient", "version": "1.0"}
        }
        return await self.send_request("initialize", params)

    async def list_tools(self):
        res = await self.send_request("tools/list", {})
        return res.get("result", {}).get("tools", [])

    async def call_tool(self, name, arguments):
        params = {"name": name, "arguments": arguments}
        res = await self.send_request("tools/call", params)
        if "error" in res:
            raise RuntimeError(res["error"].get("message", "Error desconocido llamando a la herramienta"))
        return res.get("result", {})

    async def close(self):
        if self.read_task:
            self.read_task.cancel()
        await self.client.aclose()


# ----------------- Funciones Auxiliares para Sincronía y Formateo -----------------

def run_async_in_thread(coro):
    """
    Ejecuta una coroutine de asyncio en un hilo separado para poder llamarla
    síncronamente desde cualquier contexto sin interferir con loops existentes.
    """
    q = queue.Queue()
    def worker():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(coro)
            loop.close()
            q.put((True, res))
        except Exception as e:
            q.put((False, e))
            
    t = threading.Thread(target=worker)
    t.start()
    t.join()
    
    success, val = q.get()
    if success:
        return val
    else:
        raise val


def normalize_tool_result(result):
    """
    Desempaqueta el resultado de tools/call de MCP si viene envuelto en content text.
    Maneja tanto listas completas serializadas como múltiples elementos de contenido.
    """
    if isinstance(result, dict) and "content" in result:
        content_list = result["content"]
        if isinstance(content_list, list) and len(content_list) > 0:
            parsed_items = []
            for item in content_list:
                if isinstance(item, dict) and "text" in item:
                    text_val = item["text"]
                    try:
                        parsed_val = json.loads(text_val)
                        if isinstance(parsed_val, list):
                            parsed_items.extend(parsed_val)
                        else:
                            parsed_items.append(parsed_val)
                    except Exception:
                        parsed_items.append(text_val)
            
            if parsed_items:
                if len(parsed_items) > 1:
                    return parsed_items
                return parsed_items[0]
    return result


async def run_tool_via_sse(base_url, tool_name, arguments):
    sse_url = base_url if base_url.endswith("/sse") else f"{base_url}/sse"
    client = CustomSseMcpClient(sse_url)
    try:
        await client.connect()
        await client.initialize()
        return await client.call_tool(tool_name, arguments)
    finally:
        await client.close()


async def fetch_catalog_via_sse(base_url):
    sse_url = base_url if base_url.endswith("/sse") else f"{base_url}/sse"
    client = CustomSseMcpClient(sse_url)
    try:
        await client.connect()
        await client.initialize()
        
        tables_list = await client.call_tool("get_catalogo_datos", {})
        tables_list = normalize_tool_result(tables_list)
        
        if not isinstance(tables_list, list):
            raise RuntimeError("El formato de respuesta de get_catalogo_datos no es una lista válida.")
            
        catalog = {"tables": {}}
        for table_info in tables_list:
            table_name = table_info.get("table_name") or table_info.get("NO_TABLA")
            description = table_info.get("description") or table_info.get("DE_TABLA") or f"Tabla {table_name}"
            
            if not table_name:
                continue
                
            table_name = table_name.upper()
            try:
                id_catalogo = table_info.get("id_catalogo") or table_info.get("ID_CATALOGO_DATO")
                payload = {}
                if id_catalogo is not None:
                    payload = {"id_catalogo": int(id_catalogo)}
                else:
                    payload = {"table_name": table_name}
                    
                details = await client.call_tool("get_detalle_catalogo_datos", payload)
                details = normalize_tool_result(details)
            except Exception as ex:
                print(f"[SEMANTIC REGISTRY WARNING] Error consultando columnas de {table_name}: {ex}")
                continue
                
            columns_raw = details.get("columns", []) if isinstance(details, dict) else []
            columns_mapped = []
            
            for col in columns_raw:
                col_name = col.get("name") or col.get("NO_COLUMNA")
                col_type = col.get("type") or col.get("TI_DATO", "VARCHAR2").upper()
                col_desc = col.get("description") or col.get("DE_COLUMNA") or f"Columna {col_name}"
                show = col.get("show") or col.get("BO_MOSTRAR")
                if show is None:
                    show = True
                else:
                    show = str(show).upper() in ["TRUE", "1", "Y", "SI"]
                    
                if not col_name:
                    continue
                    
                if show:
                    columns_mapped.append({
                        "name": col_name.upper(),
                        "type": col_type,
                        "description": col_desc
                    })
                    
            schema = table_info.get("schema") or table_info.get("NO_ESQUEMA_ORIGEN") or "ES_DATGOB_CV"
            catalog["tables"][table_name] = {
                "id_catalogo": id_catalogo,
                "schema": schema,
                "description": description,
                "columns": columns_mapped
            }
        return catalog
    finally:
        await client.close()


def build_catalog_from_mcp():
    """
    Retorna la lista de tablas y columnas físicas con sus descripciones
    utilizando únicamente el canal estándar SSE (MCP oficial).
    """
    if not MCP_SERVER_URL:
        raise RuntimeError("La variable de entorno MCP_SERVER_URL no está configurada.")

    print(f"[SEMANTIC REGISTRY] Intentando cargar metadatos físicos vía SSE desde {MCP_SERVER_URL}...")
    try:
        catalog = run_async_in_thread(fetch_catalog_via_sse(MCP_SERVER_URL))
        print("[SEMANTIC REGISTRY] Catálogo físico obtenido exitosamente desde SSE.")
        return catalog
    except Exception as sse_err:
        print(f"[SEMANTIC REGISTRY WARNING] Fallo al conectar vía SSE: {sse_err}")
        raise RuntimeError(f"Fallo de conexión al servidor MCP a través del canal oficial SSE: {sse_err}")

def get_semantic_catalog(force_refresh=False):
    """
    Retorna el Catálogo Físico de Datos con sus descripciones.
    Usa caché para evitar llamadas de red redundantes.
    Requiere obligatoriamente que el servidor MCP esté activo.
    """
    global _cached_catalog
    if _cached_catalog is not None and not force_refresh:
        return _cached_catalog
        
    try:
        _cached_catalog = build_catalog_from_mcp()
        print("[SEMANTIC REGISTRY] Catálogo físico obtenido exitosamente desde el servidor MCP real.")
    except Exception as e:
        print(f"[SEMANTIC REGISTRY ERROR] Fallo crítico al conectar al servidor MCP: {e}")
        raise e
        
    return _cached_catalog
