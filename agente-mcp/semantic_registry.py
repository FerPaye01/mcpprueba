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
    """
    if isinstance(result, dict) and "content" in result:
        content_list = result["content"]
        if isinstance(content_list, list) and len(content_list) > 0:
            first_item = content_list[0]
            if isinstance(first_item, dict) and "text" in first_item:
                text_val = first_item["text"]
                try:
                    return json.loads(text_val)
                except Exception:
                    return text_val
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
                    
            catalog["tables"][table_name] = {
                "description": description,
                "columns": columns_mapped
            }
        return catalog
    finally:
        await client.close()


def build_catalog_from_mcp():
    """
    Retorna la lista de tablas y columnas físicas con sus descripciones
    intentando primero vía canal SSE (MCP oficial) y cayendo a HTTP REST en caso de fallos.
    """
    if not MCP_SERVER_URL:
        raise RuntimeError("La variable de entorno MCP_SERVER_URL no está configurada.")

    print(f"[SEMANTIC REGISTRY] Intentando cargar metadatos físicos vía SSE desde {MCP_SERVER_URL}...")
    sse_error_msg = None
    try:
        catalog = run_async_in_thread(fetch_catalog_via_sse(MCP_SERVER_URL))
        print("[SEMANTIC REGISTRY] Catálogo físico obtenido exitosamente desde SSE.")
        return catalog
    except Exception as sse_err:
        sse_error_msg = str(sse_err)
        print(f"[SEMANTIC REGISTRY WARNING] Fallo al conectar vía SSE: {sse_err}")
        print("[SEMANTIC REGISTRY] Reintentando obtener metadatos vía endpoints HTTP REST directos...")

    # Si llegamos aquí, el intento SSE falló. Intentamos vía HTTP REST
    url_tables = f"{MCP_SERVER_URL}/tools/get_catalogo_datos"
    rest_error_msg = None
    try:
        r = requests.post(url_tables, json={}, timeout=10)
        if r.status_code != 200:
            raise RuntimeError(f"El servidor MCP retornó código {r.status_code} al leer tablas.")
        tables_list = r.json()

        if not isinstance(tables_list, list):
            raise RuntimeError("El formato de respuesta de get_catalogo_datos no es una lista válida.")

        catalog = {"tables": {}}

        # 2. Para cada tabla, obtener sus columnas con sus descripciones (DE_COLUMNA)
        for table_info in tables_list:
            table_name = table_info.get("table_name") or table_info.get("NO_TABLA")
            description = table_info.get("description") or table_info.get("DE_TABLA") or f"Tabla {table_name}"
            
            if not table_name:
                continue

            table_name = table_name.upper()
            
            url_columns = f"{MCP_SERVER_URL}/tools/get_detalle_catalogo_datos"
            try:
                id_catalogo = table_info.get("id_catalogo") or table_info.get("ID_CATALOGO_DATO")
                payload = {}
                if id_catalogo is not None:
                    payload = {"id_catalogo": int(id_catalogo)}
                else:
                    payload = {"table_name": table_name}
                    
                r_col = requests.post(url_columns, json=payload, timeout=10)
                if r_col.status_code != 200:
                    print(f"[SEMANTIC REGISTRY WARNING] No se pudo obtener columnas para {table_name} (payload: {payload}).")
                    continue
                details = r_col.json()
            except Exception as ex:
                print(f"[SEMANTIC REGISTRY WARNING] Error consultando columnas de {table_name}: {ex}")
                continue

            columns_raw = details.get("columns", [])
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

            catalog["tables"][table_name] = {
                "description": description,
                "columns": columns_mapped
            }

        print("[SEMANTIC REGISTRY] Catálogo físico obtenido exitosamente desde endpoints HTTP REST directos.")
        return catalog

    except Exception as rest_err:
        rest_error_msg = str(rest_err)
        print(f"[SEMANTIC REGISTRY WARNING] Fallo al conectar vía HTTP REST: {rest_err}")

    # Si ambos fallaron, lanzamos un error que combine ambos mensajes detallados
    raise RuntimeError(
        f"Fallo de conexión múltiple al servidor MCP:\n"
        f"  - Canal SSE: {sse_error_msg}\n"
        f"  - Canal HTTP REST: {rest_error_msg}"
    )

def get_semantic_catalog(force_refresh=False):
    """
    Retorna el Catálogo Físico de Datos con sus descripciones.
    Usa caché para evitar llamadas de red redundantes.
    Si el servidor MCP físico está offline, carga el archivo local semantic_catalog.json
    como respaldo seguro para mantener el prototipo 100% operativo.
    """
    global _cached_catalog
    if _cached_catalog is not None and not force_refresh:
        return _cached_catalog
        
    try:
        _cached_catalog = build_catalog_from_mcp()
        print("[SEMANTIC REGISTRY] Catálogo físico obtenido exitosamente desde el servidor MCP real.")
    except Exception as e:
        print(f"[SEMANTIC REGISTRY WARNING] Fallo al conectar al servidor MCP: {e}")
        print("[SEMANTIC REGISTRY] Intentando cargar catálogo local de respaldo (semantic_catalog.json)...")
        try:
            catalog_path = os.path.join(current_dir, "semantic_catalog.json")
            if os.path.exists(catalog_path):
                with open(catalog_path, "r", encoding="utf-8") as f:
                    raw_cached = json.load(f)
                
                # Adaptar formato de semantic_catalog.json al formato esperado por la aplicación y el gateway
                adapted_catalog = {}
                for t_name, t_data in raw_cached.get("tables", {}).items():
                    columns_mapped = []
                    
                    # Cargar medidas
                    for m_name, m_data in t_data.get("measures", {}).items():
                        col_physical_name = m_name.upper()
                        formula = m_data.get("formula", "")
                        import re
                        match = re.search(r'\((.*?)\)', formula)
                        if match:
                            col_physical_name = match.group(1).upper()
                            
                        columns_mapped.append({
                            "name": col_physical_name,
                            "type": "NUMBER",
                            "description": m_data.get("description", "")
                        })
                    
                    # Cargar dimensiones
                    for d_name, d_data in t_data.get("dimensions", {}).items():
                        columns_mapped.append({
                            "name": d_name.upper(),
                            "type": d_data.get("type", "nominal"),
                            "description": d_data.get("description", "")
                        })
                        
                    # Eliminar duplicados por nombre de columna
                    unique_cols = {}
                    for col in columns_mapped:
                        unique_cols[col["name"]] = col
                        
                    adapted_catalog[t_name.upper()] = {
                        "description": t_data.get("description", f"Tabla {t_name}"),
                        "columns": list(unique_cols.values()),
                        "id_catalogo": int(t_data.get("id_catalogo") or t_data.get("ID_CATALOGO_DATO") or 0)
                    }
                
                # Formatear contenedor final
                _cached_catalog = {"tables": adapted_catalog}
                print(f"[SEMANTIC REGISTRY] Catálogo de respaldo local cargado exitosamente ({len(_cached_catalog['tables'])} tablas).")
            else:
                print("[SEMANTIC REGISTRY ERROR] No se encontró el archivo de respaldo semantic_catalog.json.")
                raise e
        except Exception as file_err:
            print(f"[SEMANTIC REGISTRY ERROR] Error crítico leyendo el catálogo local de respaldo: {file_err}")
            raise e
            
    return _cached_catalog
