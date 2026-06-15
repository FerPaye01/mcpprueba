# mcp_server.py
import os
from dotenv import load_dotenv
load_dotenv()
import sys
import json
import logging
import datetime
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import duckdb

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

# --- CONEXIÓN A BASE DE DATO ORACLE / DUCKDB FALLBACK ---
oracle_conn = None
duck_conn = None

# Intentar importar oracledb para la base de datos Oracle
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    logger.warning("La librería 'oracledb' no está instalada. Ejecute 'pip install oracledb' para soporte de Oracle.")

def init_duckdb_mock():
    """Inicializa la base de datos local en memoria DuckDB con datos de respaldo."""
    global duck_conn
    logger.info("Inicializando base de datos local DuckDB con datos mock...")
    duck_conn = duckdb.connect(database=':memory:')
    
    # 1. Tabla Centrales
    duck_conn.execute("""
        CREATE OR REPLACE TABLE CMO_TX_CENTRAL_GEN (
            NO_CENTRAL VARCHAR,
            DEPARTAMENTO VARCHAR,
            POTENCIA_MW DOUBLE,
            TECNOLOGIA VARCHAR,
            ESTADO VARCHAR
        )
    """)
    duck_conn.execute("""
        INSERT INTO CMO_TX_CENTRAL_GEN VALUES
        ('Central Solar Rubí', 'MOQUEGUA', 180.0, 'Solar', 'En Servicio'),
        ('Central Solar Intipampa', 'MOQUEGUA', 44.0, 'Solar', 'En Servicio'),
        ('Central Térmica Cerro Verde', 'AREQUIPA', 180.0, 'Térmica', 'En Servicio'),
        ('Central Hidroeléctrica Mantaro', 'HUANCAVELICA', 798.0, 'Hidráulica', 'En Servicio'),
        ('Central Hidroeléctrica Huinco', 'LIMA', 240.0, 'Hidráulica', 'En Servicio'),
        ('Central Hidroeléctrica Platanal', 'LIMA', 220.0, 'Hidráulica', 'En Servicio'),
        ('Central Eólica Wayra I', 'ICA', 132.0, 'Eólica', 'En Servicio'),
        ('Central Eólica Tres Hermanas', 'ICA', 97.0, 'Eólica', 'En Servicio'),
        ('Central Solar Tacna Solar', 'TACNA', 20.0, 'Solar', 'En Servicio')
    """)

    # 2. Tabla Estaciones de Servicio (EESS)
    duck_conn.execute("""
        CREATE OR REPLACE TABLE VW_EESS_UBICACION_GEO (
            NO_ESTACION VARCHAR,
            DEPARTAMENTO VARCHAR,
            PROVINCIA VARCHAR,
            DISTRITO VARCHAR,
            LATITUD DOUBLE,
            LONGITUD DOUBLE
        )
    """)
    duck_conn.execute("""
        INSERT INTO VW_EESS_UBICACION_GEO VALUES
        ('GRIFO PRIMAX EL PINO', 'LIMA', 'LIMA', 'SAN LUIS', -12.0721, -76.9934),
        ('GRIFO REPSOL CHARCANI', 'AREQUIPA', 'AREQUIPA', 'CAYMA', -16.3812, -71.5511),
        ('GRIFO PETROPERU ILO', 'MOQUEGUA', 'ILO', 'ILO', -17.6432, -71.3411),
        ('GRIFO COSTI TUPAC AMARU', 'LIMA', 'LIMA', 'COMAS', -11.9324, -77.0612)
    """)

    # 3. Tabla Demanda Diaria
    duck_conn.execute("""
        CREATE OR REPLACE TABLE DEMANDA_DIARIA_ELEC (
            FECHA VARCHAR,
            DEMANDA_MAX_MW DOUBLE,
            GENERACION_GWH DOUBLE
        )
    """)
    base_date = datetime.date(2024, 1, 1)
    for i in range(30):
        date_str = (base_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        weekday = (base_date + datetime.timedelta(days=i)).weekday()
        factor = 1.05 if weekday < 5 else 0.95
        mw = round(7100.0 * factor + (i * 12.0) % 250 - 100, 1)
        gwh = round(mw * 24 / 1000 * 0.9, 2)
        duck_conn.execute(f"INSERT INTO DEMANDA_DIARIA_ELEC VALUES ('{date_str}', {mw}, {gwh})")
    
    logger.info("Base de datos local DuckDB inicializada con éxito.")

def get_oracle_connection():
    """Intenta establecer conexión con Oracle DB utilizando variables de entorno."""
    global oracle_conn
    if not ORACLE_AVAILABLE:
        return None
        
    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")  # ej. "host:port/service_name"
    
    if not all([user, password, dsn]):
        logger.info("Faltan variables de entorno para Oracle (ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN). Usando DuckDB.")
        return None
        
    try:
        # Habilitar modo thin de oracledb
        oracle_conn = oracledb.connect(user=user, password=password, dsn=dsn)
        logger.info("Conexión establecida con éxito a la base de datos Oracle.")
        return oracle_conn
    except Exception as e:
        logger.error(f"Error conectando a Oracle DB: {e}. Reintentando con DuckDB local.")
        return None

# Inicializar conexiones
init_duckdb_mock()
get_oracle_connection()

# --- CATÁLOGO DE TABLAS Y ESTRUCTURAS (METADATOS SEMÁNTICOS) ---
CATALOGO_METADATA = [
    {
        "id_catalogo": 1,
        "ID_CATALOGO_DATO": 1,
        "schema": "ES_DATGOB_CV",
        "NO_ESQUEMA_ORIGEN": "ES_DATGOB_CV",
        "table_name": "CMO_TX_CENTRAL_GEN",
        "NO_TABLA": "CMO_TX_CENTRAL_GEN",
        "description": "Catálogo de centrales eléctricas activas, su ubicación, tecnología y potencia instalada.",
        "DE_TABLA": "Catálogo de centrales eléctricas activas, su ubicación, tecnología y potencia instalada."
    },
    {
        "id_catalogo": 2,
        "ID_CATALOGO_DATO": 2,
        "schema": "ES_DATGOB_CV",
        "NO_ESQUEMA_ORIGEN": "ES_DATGOB_CV",
        "table_name": "VW_EESS_UBICACION_GEO",
        "NO_TABLA": "VW_EESS_UBICACION_GEO",
        "description": "Estaciones de servicio y grifos autorizados con su ubicación geográfica y coordenadas.",
        "DE_TABLA": "Estaciones de servicio y grifos autorizados con su ubicación geográfica y coordenadas."
    },
    {
        "id_catalogo": 3,
        "ID_CATALOGO_DATO": 3,
        "schema": "ES_DATGOB_CV",
        "NO_ESQUEMA_ORIGEN": "ES_DATGOB_CV",
        "table_name": "DEMANDA_DIARIA_ELEC",
        "NO_TABLA": "DEMANDA_DIARIA_ELEC",
        "description": "Historial de demanda máxima y generación diaria de electricidad a nivel del SEIN.",
        "DE_TABLA": "Historial de demanda máxima y generación diaria de electricidad a nivel del SEIN."
    }
]

COLUMNAS_METADATA = {
    "CMO_TX_CENTRAL_GEN": [
        {"name": "NO_CENTRAL", "type": "VARCHAR", "description": "Nombre identificativo de la central de generación eléctrica.", "show": True},
        {"name": "DEPARTAMENTO", "type": "VARCHAR", "description": "Ubicación a nivel regional de la central eléctrica.", "show": True},
        {"name": "POTENCIA_MW", "type": "NUMBER", "description": "Potencia total instalada de la central eléctrica en megawatts.", "show": True},
        {"name": "TECNOLOGIA", "type": "VARCHAR", "description": "Matriz energética o tipo de tecnología de la central (Solar, Eólica, Hidráulica, Térmica).", "show": True},
        {"name": "ESTADO", "type": "VARCHAR", "description": "Estado de servicio de la central (En Servicio, Mantenimiento, Fuera de Servicio).", "show": True}
    ],
    "VW_EESS_UBICACION_GEO": [
        {"name": "NO_ESTACION", "type": "VARCHAR", "description": "Razón social o nombre comercial del grifo.", "show": True},
        {"name": "DEPARTAMENTO", "type": "VARCHAR", "description": "Departamento político del establecimiento.", "show": True},
        {"name": "PROVINCIA", "type": "VARCHAR", "description": "Provincia de ubicación del establecimiento.", "show": True},
        {"name": "DISTRITO", "type": "VARCHAR", "description": "Distrito político del establecimiento.", "show": True},
        {"name": "LATITUD", "type": "NUMBER", "description": "Coordenada de latitud geográfica del grifo.", "show": True},
        {"name": "LONGITUD", "type": "NUMBER", "description": "Coordenada de longitud geográfica del grifo.", "show": True}
    ],
    "DEMANDA_DIARIA_ELEC": [
        {"name": "FECHA", "type": "DATE", "description": "Fecha del día en que se registran las métricas.", "show": True},
        {"name": "DEMANDA_MAX_MW", "type": "NUMBER", "description": "Demanda pico registrada en el Sistema Eléctrico Interconectado Nacional.", "show": True},
        {"name": "GENERACION_GWH", "type": "NUMBER", "description": "Total de energía generada en el SEIN expresada en gigavatios-hora.", "show": True}
    ]
}

# --- HERRAMIENTAS MCP (MCP TOOLS) ---

@mcp.tool()
def get_catalogo_datos(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de tablas registradas en el catálogo de datos gobernados de Osinergmin.
    
    Args:
        limit: Límite opcional de tablas a retornar.
    """
    logger.info("Herramienta get_catalogo_datos invocada.")
    # Si tenemos conexión a Oracle activa, podríamos consultar una tabla física de catálogo si existiera.
    # Como fallback o diseño por defecto, usamos el catálogo semántico estructurado.
    res = CATALOGO_METADATA
    if limit:
        res = res[:limit]
    return res

@mcp.tool()
def get_detalle_catalogo_datos(id_catalogo: Optional[int] = None, table_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene la estructura de columnas y metadatos detallados de una tabla del catálogo.
    
    Args:
        id_catalogo: ID numérico del catálogo de la tabla.
        table_name: Nombre físico de la tabla (usar si id_catalogo no se conoce).
    """
    logger.info(f"Herramienta get_detalle_catalogo_datos invocada. id_catalogo={id_catalogo}, table_name={table_name}")
    
    target_table = None
    if id_catalogo is not None:
        for item in CATALOGO_METADATA:
            if item["id_catalogo"] == id_catalogo:
                target_table = item["table_name"]
                break
    elif table_name:
        target_table = table_name.upper()
        
    if not target_table or target_table not in COLUMNAS_METADATA:
        return {"error": f"Tabla o catálogo especificado no encontrado: id={id_catalogo}, table={table_name}"}
        
    return {
        "table_name": target_table,
        "columns": COLUMNAS_METADATA[target_table]
    }

@mcp.tool()
def query_data(table_name: str, schema_name: str = "ES_DATGOB_CV", limit: int = 100, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Consulta registros de una tabla específica del catálogo, aplicando filtros básicos y un límite.
    
    Args:
        table_name: Nombre físico de la tabla a consultar.
        schema_name: Nombre del esquema de base de datos.
        limit: Número máximo de registros a retornar.
        filters: Diccionario de filtros clave-valor (ej: {"DEPARTAMENTO": "AREQUIPA"}).
    """
    logger.info(f"Herramienta query_data invocada. table_name={table_name}, limit={limit}, filters={filters}")
    
    table_upper = table_name.upper()
    if table_upper not in COLUMNAS_METADATA:
        return [{"error": f"La tabla {table_name} no pertenece al catálogo gobernado."}]
        
    # Intentar ejecutar en Oracle si está conectado
    conn = get_oracle_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Construir consulta SQL segura
            query = f"SELECT * FROM {schema_name}.{table_upper}"
            where_clauses = []
            params = {}
            if filters:
                for k, v in filters.items():
                    # Validar que la columna exista
                    if any(col["name"] == k.upper() for col in COLUMNAS_METADATA[table_upper]):
                        where_clauses.append(f"{k.upper()} = :{k}")
                        params[k] = v
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Limitar registros (sintaxis Oracle 12c+)
            query += f" FETCH FIRST {limit} ROWS ONLY"
            
            logger.info(f"Ejecutando SQL en Oracle: {query} con parámetros {params}")
            cursor.execute(query, params)
            
            # Formatear salida como lista de diccionarios
            columns = [col[0] for col in cursor.description]
            records = []
            for row in cursor.fetchall():
                records.append(dict(zip(columns, row)))
            cursor.close()
            return records
        except Exception as e:
            logger.error(f"Error consultando en Oracle DB: {e}. Cayendo a DuckDB de respaldo.")
            # Continuar abajo con DuckDB

    # Consultar en DuckDB local (mock)
    try:
        query = f"SELECT * FROM {table_upper}"
        where_clauses = []
        if filters:
            for k, v in filters.items():
                if any(col["name"] == k.upper() for col in COLUMNAS_METADATA[table_upper]):
                    # Sanitización simple de comillas simples
                    val_clean = str(v).replace("'", "''")
                    where_clauses.append(f"{k.upper()} = '{val_clean}'")
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += f" LIMIT {limit}"
        
        logger.info(f"Ejecutando SQL en DuckDB local: {query}")
        df = duck_conn.execute(query).fetchdf()
        
        # Convertir timestamps a strings legibles
        records = df.to_dict(orient="records")
        for r in records:
            for k, v in r.items():
                if isinstance(v, (datetime.date, datetime.datetime)):
                    r[k] = v.strftime('%Y-%m-%d')
                elif pandas_isna(v):
                    r[k] = None
        return records
    except Exception as e:
        logger.error(f"Error consultando en DuckDB local: {e}")
        return [{"error": f"Fallo al ejecutar la consulta: {str(e)}"}]

def pandas_isna(val):
    """Auxiliar para evitar importar pandas completo si no es necesario."""
    try:
        import pandas as pd
        return pd.isna(val)
    except ImportError:
        return val is None

@mcp.tool()
def get_unidades(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene unidades operativas o estaciones de servicio georreferenciadas (grifos).
    
    Args:
        limit: Límite de grifos a listar.
    """
    logger.info(f"Herramienta get_unidades invocada. limit={limit}")
    return query_data(table_name="VW_EESS_UBICACION_GEO", limit=limit)

# --- EJEMPLOS DE HERRAMIENTAS ADICIONALES (Calculator & Weather) ---

@mcp.tool()
def calculator(a: int, b: int) -> int:
    """Suma dos números enteros."""
    logger.info(f"Herramienta calculator invocada: a={a}, b={b}")
    return a + b

@mcp.tool()
def get_weather(city: str, unit: str = "celsius") -> str:
    """Obtiene el clima actual de una ciudad."""
    logger.info(f"Herramienta get_weather invocada: city={city}, unit={unit}")
    return f"Clima en {city}: 22 grados {unit.title()}"

# --- INICIALIZACIÓN DE TRANSPORTE SSE ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    logger.info(f"Iniciando MCP Server en modo SSE (Server-Sent Events) en el puerto {port}...")
    
    # FastMCP gestiona internamente la aplicación Starlette/FastAPI
    # Para cambiar el puerto de FastMCP sse en modo standalone, se utiliza la variable de entorno PORT o se le puede pasar a run.
    mcp.run(transport="sse")
