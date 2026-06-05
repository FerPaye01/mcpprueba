# agente-mcp/semantic_registry.py
import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
load_dotenv(os.path.join(parent_dir, ".env"), override=True)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

# Caché en memoria del catálogo
_cached_catalog = None

def build_catalog_from_mcp():
    """
    Retorna la lista de tablas y columnas físicas con sus descripciones (DE_COLUMNA)
    directamente del MCP de Osinergmin. 
    
    No infiere fórmulas de negocio ni inventa semántica.
    """
    if not MCP_SERVER_URL:
        raise RuntimeError("La variable de entorno MCP_SERVER_URL no está configurada.")

    print(f"[SEMANTIC REGISTRY] Cargando metadatos físicos y descripciones desde el MCP en {MCP_SERVER_URL}...")
    
    # 1. Obtener la lista de tablas físicas y descripciones (DE_TABLA)
    url_tables = f"{MCP_SERVER_URL}/tools/get_catalogo_datos"
    try:
        r = requests.post(url_tables, json={}, timeout=10)
        if r.status_code != 200:
            raise RuntimeError(f"El servidor MCP retornó código {r.status_code} al leer tablas.")
        tables_list = r.json()
    except Exception as e:
        raise RuntimeError(f"Fallo crítico al conectar con el servidor MCP en {url_tables}: {str(e)}")

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
            r_col = requests.post(url_columns, json={"table_name": table_name}, timeout=10)
            if r_col.status_code != 200:
                print(f"[SEMANTIC REGISTRY WARNING] No se pudo obtener columnas para {table_name}.")
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
                # Normalizar booleano si viene como string o número
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

def get_semantic_catalog(force_refresh=False):
    """
    Retorna el Catálogo Físico de Datos con sus descripciones.
    Usa caché para evitar llamadas de red redundantes.
    """
    global _cached_catalog
    if _cached_catalog is None or force_refresh:
        _cached_catalog = build_catalog_from_mcp()
    return _cached_catalog
