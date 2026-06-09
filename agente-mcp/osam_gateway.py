# agente-mcp/osam_gateway.py
import duckdb
import pandas as pd
import datetime
import hashlib
from semantic_registry import get_semantic_catalog

# Inicializar conexión local en memoria de DuckDB
con = duckdb.connect(database=':memory:')

# Inicializar tablas con datos mock reales en DuckDB para el motor local
def init_db():
    # 1. Tabla Centrales
    con.execute("""
        CREATE OR REPLACE TABLE CMO_TX_CENTRAL_GEN (
            NO_CENTRAL VARCHAR,
            DEPARTAMENTO VARCHAR,
            POTENCIA_MW DOUBLE,
            TECNOLOGIA VARCHAR,
            ESTADO VARCHAR
        )
    """)
    con.execute("""
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
    con.execute("""
        CREATE OR REPLACE TABLE VW_EESS_UBICACION_GEO (
            NO_ESTACION VARCHAR,
            DEPARTAMENTO VARCHAR,
            PROVINCIA VARCHAR,
            DISTRITO VARCHAR,
            LATITUD DOUBLE,
            LONGITUD DOUBLE
        )
    """)
    con.execute("""
        INSERT INTO VW_EESS_UBICACION_GEO VALUES
        ('GRIFO PRIMAX EL PINO', 'LIMA', 'LIMA', 'SAN LUIS', -12.0721, -76.9934),
        ('GRIFO REPSOL CHARCANI', 'AREQUIPA', 'AREQUIPA', 'CAYMA', -16.3812, -71.5511),
        ('GRIFO PETROPERU ILO', 'MOQUEGUA', 'ILO', 'ILO', -17.6432, -71.3411),
        ('GRIFO COSTI TUPAC AMARU', 'LIMA', 'LIMA', 'COMAS', -11.9324, -77.0612)
    """)

    # 3. Tabla Demanda Diaria
    con.execute("""
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
        con.execute(f"INSERT INTO DEMANDA_DIARIA_ELEC VALUES ('{date_str}', {mw}, {gwh})")

# Inicializar base de datos local en memoria
init_db()

def translate_to_sql(table_name, fields, dimensions, filters, user_geography):
    """
    Traduce una consulta lógica OSAM v2 (especificando campos y sus agregaciones)
    a una sentencia SQL de DuckDB, validando tipos e inyectando RLS de geografía.
    """
    catalog = get_semantic_catalog()["tables"].get(table_name)
    if not catalog:
        raise ValueError(f"Tabla '{table_name}' no registrada en el catálogo de base de datos.")

    # Mapear nombres de columnas existentes para validación insensible a mayúsculas
    valid_columns = {col["name"].upper(): col for col in catalog.get("columns", [])}
    
    select_clauses = []
    selected_cols = set()
    
    # 1. Procesar campos solicitados con su agregación dinámica
    for field_spec in fields:
        field_name = field_spec["name"].upper()
        agg_func = field_spec.get("aggregation", "NONE").upper()
        
        if field_name not in valid_columns:
            raise ValueError(f"Columna '{field_name}' no existe en la tabla '{table_name}'.")
            
        alias = field_name.upper()
        if agg_func in ["SUM", "AVG", "MAX", "MIN", "COUNT"]:
            select_clauses.append(f"{agg_func}({field_name}) AS {alias}")
            selected_cols.add(alias)
        else:
            if alias not in selected_cols:
                select_clauses.append(f"{field_name} AS {alias}")
                selected_cols.add(alias)

    # 2. Procesar dimensiones (columnas de agrupación)
    for dim in dimensions:
        dim_upper = dim.upper()
        if dim_upper not in valid_columns:
            raise ValueError(f"Dimensión '{dim}' no existe en la tabla '{table_name}'.")
        alias = dim_upper
        if alias not in selected_cols:
            select_clauses.append(f"{dim_upper} AS {alias}")
            selected_cols.add(alias)

    select_str = ", ".join(select_clauses)
    
    # 3. Procesar filtros lógicos
    where_clauses = []
    for filt in filters:
        field = filt["field"].upper()
        op = filt["operator"]
        val = filt["value"]
        
        if field not in valid_columns:
            continue  # Omitir filtros sobre columnas inexistentes
            
        if op == "equals":
            where_clauses.append(f"{field} = '{val}'")
        elif op == "in":
            vals_str = ", ".join(f"'{v}'" for v in val)
            where_clauses.append(f"{field} IN ({vals_str})")
        elif op == "greater_than":
            where_clauses.append(f"{field} > '{val}'")
        elif op == "less_than":
            where_clauses.append(f"{field} < '{val}'")

    # 4. Inyectar Row-Level Security (RLS)
    # Si la tabla física posee la columna DEPARTAMENTO, filtramos por la geografía del usuario
    if user_geography and user_geography.lower() not in ["sede nacional", "todas", "todos"]:
        if "DEPARTAMENTO" in valid_columns:
            where_clauses.append(f"DEPARTAMENTO = '{user_geography.upper()}'")

    where_str = ""
    if where_clauses:
        where_str = " WHERE " + " AND ".join(where_clauses)

    # 5. Agrupaciones (Group By) si se solicitaron dimensiones
    group_str = ""
    if dimensions:
        group_fields = [d.upper() for d in dimensions]
        group_str = " GROUP BY " + ", ".join(group_fields)

    sql = f"SELECT {select_str} FROM {table_name}{where_str}{group_str}"
    return sql

def execute_osam_query(query_dict, user_role="Analista", user_geography="Sede Nacional"):
    """
    Procesa la consulta lógica OSAM v2, traduce a SQL, ejecuta en DuckDB
    y retorna la estructura del bloque 'report' de OSAM v1.
    """
    fields = query_dict.get("fields", [])
    dimensions = query_dict.get("dimensions", [])
    filters = query_dict.get("filters", [])
    
    # Inferencia de tabla destino en base a la pertenencia de las columnas
    catalog = get_semantic_catalog()
    target_table = None
    
    all_requested_cols = [f["name"].upper() for f in fields] + [d.upper() for d in dimensions]
    
    for t_name, t_spec in catalog.get("tables", {}).items():
        if not isinstance(t_spec, dict) or "columns" not in t_spec:
            continue
        valid_cols = [c["name"].upper() for c in t_spec.get("columns", [])]
        if all(col in valid_cols for col in all_requested_cols):
            target_table = t_name
            break
            
    if not target_table:
        return {
            "status": "error",
            "message": "No se encontró una tabla única que contenga todas las dimensiones y campos especificados."
        }
        
    try:
        # Traducir a SQL e inyectar RLS
        sql = translate_to_sql(target_table, fields, dimensions, filters, user_geography)
        print(f"[OSAM GATEWAY] SQL Generado con RLS: {sql}")
        
        # Ejecutar consulta en DuckDB
        df = con.execute(sql).fetchdf()
        
        # Estructurar columns metadata
        columns_meta = []
        table_catalog = catalog.get("tables", {}).get(target_table, {})
        valid_columns_dict = {col["name"].upper(): col for col in table_catalog.get("columns", [])}
        
        for col in df.columns:
            col_upper = col.upper()
            spec = valid_columns_dict.get(col_upper)
            
            if spec:
                col_type = spec["type"].upper()
                is_num = col_type in ["NUMBER", "DOUBLE", "INTEGER", "FLOAT", "DECIMAL"]
                columns_meta.append({
                    "id": col,
                    "label": spec["description"] if len(spec["description"]) < 30 else spec["name"].replace("_", " ").title(),
                    "type": "quantitative" if is_num else ("temporal" if "FECHA" in col_upper or "DATE" in col_type else "nominal"),
                    "format": "number:2" if is_num else "text"
                })
            else:
                # Si es un campo de agregación o derivado, asumimos tipo cuantitativo
                columns_meta.append({
                    "id": col,
                    "label": col.replace("_", " ").title(),
                    "type": "quantitative",
                    "format": "number:2"
                })
                
        # Estructurar metadata de proveniencia
        query_hash = hashlib.sha256(sql.encode('utf-8')).hexdigest()
        provenance = {
            "source_tables": [target_table],
            "source_systems": ["SEIN_DIARIO" if "DEMANDA" in target_table else "ESTADO_ORGANICO"],
            "filters_applied": [f"user_geography = {user_geography}"] + [f"{f['field']} {f['operator']} {f['value']}" for f in filters],
            "query_hash": f"sha256:{query_hash}",
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        # Formatear registros
        data_records = df.to_dict(orient="records")
        for record in data_records:
            for k, v in record.items():
                if isinstance(v, pd.Timestamp):
                    record[k] = v.strftime('%Y-%m-%d')
                elif pd.isna(v):
                    record[k] = None
                    
        return {
            "status": "success",
            "report": {
                "query": query_dict,
                "columns": columns_meta,
                "data": data_records,
                "provenance": provenance
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al ejecutar la consulta analítica: {str(e)}"
        }
