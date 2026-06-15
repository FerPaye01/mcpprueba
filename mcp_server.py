# mcp_server.py
import os
from dotenv import load_dotenv
load_dotenv()
import sys
import logging
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Reconfigure stdout to use UTF-8 to prevent encoding issues on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp-osinergmin-server")

# Inicializar FastMCP dinámicamente con puerto de entorno
mcp_port = int(os.getenv("PORT", "8001"))
mcp_host = os.getenv("HOST", "0.0.0.0")
mcp = FastMCP(name="Osinergmin-MCP-Server", host=mcp_host, port=mcp_port)

# --- CONEXIÓN A BASE DE DATO ORACLE (100% ACTIVA REQUERIDA) ---
oracle_conn = None
DYNAMIC_CATALOG_CACHE = []

try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    logger.critical("La librería 'oracledb' no está instalada. Ejecute 'pip install oracledb'.")
    sys.exit("Error: 'oracledb' es obligatorio para el modo 100% activo.")

def get_oracle_connection():
    """Establece conexión estricta con Oracle DB utilizando variables de entorno."""
    global oracle_conn
    if not ORACLE_AVAILABLE:
        raise RuntimeError("La librería 'oracledb' no está instalada. Conexión imposible.")
        
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")
    
    if not all([user, password, dsn]):
        raise RuntimeError("Faltan variables de entorno esenciales para Oracle (ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN).")
        
    try:
        if oracle_conn is None:
            oracle_conn = oracledb.connect(user=user, password=password, dsn=dsn)
            logger.info("Conexión establecida con éxito a la base de datos Oracle.")
        return oracle_conn
    except Exception as e:
        logger.error(f"Fallo crítico conectando a Oracle DB: {e}")
        raise RuntimeError(f"Error de conexión a Oracle: {e}")

# Intentar verificar la conexión inicial al arrancar
try:
    get_oracle_connection()
except Exception as init_err:
    logger.warning(f"Advertencia de inicio: No se pudo conectar a Oracle al arrancar ({init_err}). Se reintentará en la primera consulta de herramienta.")

# --- HERRAMIENTAS MCP (CON FIRMAS EXACTAS - OBLIGATORIO CONEXIÓN ACTIVA) ---

@mcp.tool()
def get_unidades(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """
    unidades operativas o estaciones de servicio de hidrocarburos líquidos (20 max)
    """
    logger.info(f"Herramienta get_unidades invocada: limit={limit}, offset={offset}")
    lim = min(limit, 20)
    
    conn = get_oracle_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM ES_DATGOB_CV.VW_EESS_UBICACION_GEO OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        cursor.execute(query, {"offset": offset, "limit": lim})
        columns = [col[0] for col in cursor.description]
        records = []
        for row in cursor.fetchall():
            records.append(dict(zip(columns, row)))
        cursor.close()
        return records
    except Exception as e:
        logger.error(f"Error consultando get_unidades en Oracle: {e}")
        raise RuntimeError(f"Error consultando get_unidades en la base de datos Oracle: {e}")

@mcp.tool()
def get_unidades_por_ubigeo(ubigeo: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    unidades operativas o estaciones de servicio de hidrocarburos líquidos por departamento, provincia o distrito (20 max)
    """
    logger.info(f"Herramienta get_unidades_por_ubigeo invocada: ubigeo={ubigeo}, limit={limit}")
    lim = min(limit, 20)
    
    conn = get_oracle_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM ES_DATGOB_CV.VW_EESS_UBICACION_GEO WHERE UBIGEO LIKE :ubigeo FETCH FIRST :limit ROWS ONLY"
        cursor.execute(query, {"ubigeo": f"{ubigeo}%", "limit": lim})
        columns = [col[0] for col in cursor.description]
        records = []
        for row in cursor.fetchall():
            records.append(dict(zip(columns, row)))
        cursor.close()
        return records
    except Exception as e:
        logger.error(f"Error consultando get_unidades_por_ubigeo en Oracle: {e}")
        raise RuntimeError(f"Error consultando get_unidades_por_ubigeo en la base de datos Oracle: {e}")

@mcp.tool()
def get_precios_combustible(ubigeo: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Precios de unidades operativas o estaciones de servicio de hidrocarburos líquidos por ubigeo (15 max)
    """
    logger.info(f"Herramienta get_precios_combustible invocada: ubigeo={ubigeo}, limit={limit}")
    lim = min(limit, 15)
    
    conn = get_oracle_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM ES_DATGOB_CV.VW_PRECIOS_COMB WHERE UBIGEO LIKE :ubigeo FETCH FIRST :limit ROWS ONLY"
        cursor.execute(query, {"ubigeo": f"{ubigeo}%", "limit": lim})
        columns = [col[0] for col in cursor.description]
        records = []
        for row in cursor.fetchall():
            records.append(dict(zip(columns, row)))
        cursor.close()
        return records
    except Exception as e:
        logger.error(f"Error consultando get_precios_combustible en Oracle: {e}")
        raise RuntimeError(f"Error consultando get_precios_combustible en la base de datos Oracle: {e}")

@mcp.tool()
def get_catalogo_datos(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Muestra todos los datasets (tablas y vistas) disponibles en el catálogo de datos gobernados de Osinergmin.
    """
    logger.info(f"Herramienta get_catalogo_datos invocada: limit={limit}")
    
    conn = get_oracle_connection()
    try:
        cursor = conn.cursor()
        schema = os.getenv("ORACLE_USER", "ES_DATGOB_CV").upper()
        target_schema = "ES_DATGOB_CV"
        
        query = """
            SELECT 
                t.table_name, 
                c.comments 
            FROM 
                (SELECT table_name FROM all_tables WHERE owner = :schema
                 UNION 
                 SELECT view_name FROM all_views WHERE owner = :schema) t
            LEFT JOIN 
                all_tab_comments c ON t.table_name = c.table_name AND c.owner = :schema
            ORDER BY 
                t.table_name
        """
        cursor.execute(query, {"schema": target_schema})
        rows = cursor.fetchall()
        
        # Si no hay tablas bajo ES_DATGOB_CV, probar con el esquema conectado actual
        if not rows:
            cursor.execute(query, {"schema": schema})
            rows = cursor.fetchall()
            target_schema = schema
            
        cursor.close()
        
        if not rows:
            raise RuntimeError(f"No se encontraron tablas ni vistas accesibles en el esquema {target_schema}.")
            
        dynamic_catalog = []
        for idx, (table_name, comments) in enumerate(rows, 1):
            desc = comments or f"Tabla de datos gobernados {table_name} en el esquema {target_schema}."
            dynamic_catalog.append({
                "id_catalogo": idx,
                "ID_CATALOGO_DATO": idx,
                "schema": target_schema,
                "NO_ESQUEMA_ORIGEN": target_schema,
                "table_name": table_name,
                "NO_TABLA": table_name,
                "description": desc,
                "DE_TABLA": desc
            })
        # Cachear en memoria
        global DYNAMIC_CATALOG_CACHE
        DYNAMIC_CATALOG_CACHE = dynamic_catalog
        return dynamic_catalog[:limit]
    except Exception as e:
        logger.error(f"Error cargando catálogo desde Oracle: {e}")
        raise RuntimeError(f"Error al obtener el catálogo de datos de Oracle: {e}")

@mcp.tool()
def get_detalle_catalogo_datos(id_catalogo: int) -> Dict[str, Any]:
    """
    Obtiene las columnas de un catálogo de datos por su ID.
    """
    logger.info(f"Herramienta get_detalle_catalogo_datos invocada: id_catalogo={id_catalogo}")
    
    global DYNAMIC_CATALOG_CACHE
    target_table = None
    target_schema = "ES_DATGOB_CV"
    
    if DYNAMIC_CATALOG_CACHE:
        for item in DYNAMIC_CATALOG_CACHE:
            if item["id_catalogo"] == id_catalogo:
                target_table = item["table_name"]
                target_schema = item["schema"]
                break
                
    if not target_table:
        # Si la caché está vacía, intentar repoblarla primero
        try:
            get_catalogo_datos(limit=500)
            if DYNAMIC_CATALOG_CACHE:
                for item in DYNAMIC_CATALOG_CACHE:
                    if item["id_catalogo"] == id_catalogo:
                        target_table = item["table_name"]
                        target_schema = item["schema"]
                        break
        except Exception:
            pass
            
    if not target_table:
        raise RuntimeError(f"ID de catálogo {id_catalogo} no encontrado. Ejecute get_catalogo_datos primero.")
        
    conn = get_oracle_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                col.column_name, 
                col.data_type, 
                comm.comments 
            FROM 
                all_tab_columns col
            LEFT JOIN 
                all_col_comments comm ON col.owner = comm.owner AND col.table_name = comm.table_name AND col.column_name = comm.column_name
            WHERE 
                col.owner = :schema AND col.table_name = :table_name
            ORDER BY 
                col.column_id
        """
        cursor.execute(query, {"schema": target_schema, "table_name": target_table})
        rows = cursor.fetchall()
        cursor.close()
        
        if not rows:
            raise RuntimeError(f"No se encontraron columnas para la tabla o vista {target_table}.")
            
        columns = []
        for col_name, col_type, comments in rows:
            columns.append({
                "name": col_name,
                "type": col_type,
                "description": comments or f"Columna {col_name} de tipo {col_type}.",
                "show": True
            })
        return {
            "table_name": target_table,
            "columns": columns
        }
    except Exception as e:
        logger.error(f"Error consultando columnas de {target_table} en Oracle: {e}")
        raise RuntimeError(f"Error consultando columnas de {target_table} en Oracle: {e}")

@mcp.tool()
def query_data(schema: str, table: str, id_catalogo: int, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Consulta datos gobernados almacenados en el catálogo de datos de Osinergmin.
    """
    logger.info(f"Herramienta query_data invocada: schema={schema}, table={table}, id_catalogo={id_catalogo}, limit={limit}, filters={filters}")
    
    table_upper = table.upper()
    lim = min(limit, 50)
    
    conn = get_oracle_connection()
    try:
        # Primero, validar que la tabla existe en Oracle y obtener las columnas autorizadas para validar filtros
        # Evitamos usar ':table' ya que TABLE es una palabra reservada en Oracle y causa ORA-01745
        cursor = conn.cursor()
        query_cols = "SELECT column_name FROM all_tab_columns WHERE owner = :schema AND table_name = :table_name"
        cursor.execute(query_cols, {"schema": schema.upper(), "table_name": table_upper})
        cols = [r[0].upper() for r in cursor.fetchall()]
        
        if not cols:
            cursor.close()
            raise RuntimeError(f"La tabla {schema}.{table_upper} no existe o no es accesible.")
            
        # Construir consulta dinámica segura
        query = f"SELECT * FROM {schema.upper()}.{table_upper}"
        where_clauses = []
        params = {}
        if filters:
            # Usamos marcadores de posición genéricos (p1, p2...) para evitar colisiones ORA-01745 con nombres de columnas reservados
            for idx, (k, v) in enumerate(filters.items(), 1):
                if k.upper() in cols:
                    param_name = f"p{idx}"
                    where_clauses.append(f"{k.upper()} = :{param_name}")
                    params[param_name] = v
                    
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += f" FETCH FIRST {lim} ROWS ONLY"
        
        logger.info(f"Ejecutando SQL en Oracle: {query} con parámetros {params}")
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        records = []
        for row in cursor.fetchall():
            # Convertir fechas a strings para compatibilidad JSON
            row_dict = {}
            for col, val in zip(columns, row):
                import datetime
                if isinstance(val, (datetime.date, datetime.datetime)):
                    row_dict[col] = val.strftime('%Y-%m-%d')
                else:
                    row_dict[col] = val
            records.append(row_dict)
            
        cursor.close()
        return records
    except Exception as e:
        logger.error(f"Error consultando en Oracle DB: {e}")
        raise RuntimeError(f"Fallo al ejecutar la consulta en Oracle: {e}")

# --- INICIALIZACIÓN DE TRANSPORTE SSE ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    logger.info(f"Iniciando MCP Server 100% ACTIVO en modo SSE en el puerto {port}...")
    mcp.run(transport="sse")
