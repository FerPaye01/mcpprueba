import sys
import os

# Agregar la ruta del proyecto a sys.path para poder importar agente_mcp
PROJECT_DIR = r"C:\Users\opaye\Proyectos\MCPdinamicoPrueba"
sys.path.append(PROJECT_DIR)

# Necesario porque agente-mcp usa imports relativos o absolutos dentro de su carpeta
sys.path.append(os.path.join(PROJECT_DIR, "agente-mcp"))

from osam_gateway import execute_osam_query, translate_to_sql

def run_tests():
    print("=== INICIANDO PRUEBAS DE OSAM GATEWAY ===")
    
    # Caso 1: Consulta básica de centrales en Moquegua (Sede Nacional, sin RLS forzado en translate_to_sql)
    print("\n[TEST 1] Consulta de centrales con filtro manual por departamento (Sede Nacional)")
    query_1 = {
        "measures": ["potencia_mw", "total_centrales"],
        "dimensions": ["tecnologia", "departamento"],
        "filters": [
            {"field": "departamento", "operator": "equals", "value": "MOQUEGUA"}
        ]
    }
    res_1 = execute_osam_query(query_1, user_role="Analista", user_geography="Sede Nacional")
    print("Status:", res_1["status"])
    if res_1["status"] == "success":
        print("Registros:", res_1["report"]["data"])
        print("Provenance:", res_1["report"]["provenance"])
    else:
        print("Error:", res_1.get("message"))

    # Caso 2: RLS Activo - Usuario de Moquegua consultando centrales (Debería filtrar automáticamente por MOQUEGUA)
    print("\n[TEST 2] RLS Activo - Usuario de Moquegua consultando todas las centrales")
    query_2 = {
        "measures": ["potencia_mw", "total_centrales"],
        "dimensions": ["tecnologia", "departamento"],
        "filters": []
    }
    res_2 = execute_osam_query(query_2, user_role="Analista", user_geography="Moquegua")
    print("Status:", res_2["status"])
    if res_2["status"] == "success":
        print("Registros:", res_2["report"]["data"])
        for reg in res_2["report"]["data"]:
            assert reg["departamento"] == "MOQUEGUA", f"RLS Falló: se encontró departamento {reg['departamento']}"
        print("[OK] RLS filtro correctamente por MOQUEGUA.")
    else:
        print("Error:", res_2.get("message"))

    # Caso 3: Demanda diaria en el SEIN
    print("\n[TEST 3] Consulta de demanda eléctrica diaria")
    query_3 = {
        "measures": ["demanda_max_mw", "generacion_gwh", "demanda_promedio_mw"],
        "dimensions": ["fecha"],
        "filters": [
            {"field": "fecha", "operator": "greater_than", "value": "2024-01-25"}
        ]
    }
    res_3 = execute_osam_query(query_3, user_role="Analista", user_geography="Sede Nacional")
    print("Status:", res_3["status"])
    if res_3["status"] == "success":
        print(f"Registros recuperados: {len(res_3['report']['data'])}")
        print("Primeros 2 registros:", res_3["report"]["data"][:2])
    else:
        print("Error:", res_3.get("message"))

    # Caso 4: Consulta de estaciones de servicio (EESS)
    print("\n[TEST 4] Consulta de estaciones de servicio (EESS)")
    query_4 = {
        "measures": ["total_estaciones"],
        "dimensions": ["provincia", "distrito"],
        "filters": []
    }
    res_4 = execute_osam_query(query_4, user_role="Analista", user_geography="Sede Nacional")
    print("Status:", res_4["status"])
    if res_4["status"] == "success":
        print("Registros:", res_4["report"]["data"])
    else:
        print("Error:", res_4.get("message"))

    # Caso 5: Consulta de demanda diaria con geografía regional (no debería filtrar por departamento)
    print("\n[TEST 5] Demanda nacional consultada por usuario de Moquegua (No debe aplicar RLS por departamento)")
    query_5 = {
        "measures": ["demanda_max_mw"],
        "dimensions": ["fecha"],
        "filters": [{"field": "fecha", "operator": "greater_than", "value": "2024-01-28"}]
    }
    res_5 = execute_osam_query(query_5, user_role="Analista", user_geography="Moquegua")
    print("Status:", res_5["status"])
    if res_5["status"] == "success":
        print("SQL Generado contiene WHERE DEPARTAMENTO:", "DEPARTAMENTO" in str(res_5["report"]["query"]))
        print("Registros:", res_5["report"]["data"])
    else:
        print("Error:", res_5.get("message"))

    # Caso 6: Filtro de dimensión con operador 'in'
    print("\n[TEST 6] Consulta de centrales con filtro IN")
    query_6 = {
        "measures": ["total_centrales"],
        "dimensions": ["tecnologia"],
        "filters": [
            {"field": "tecnologia", "operator": "in", "value": ["Solar", "Eolica"]}
        ]
    }
    res_6 = execute_osam_query(query_6, user_role="Analista", user_geography="Sede Nacional")
    print("Status:", res_6["status"])
    if res_6["status"] == "success":
        print("Registros:", res_6["report"]["data"])
    else:
        print("Error:", res_6.get("message"))

    # Caso 7: Consulta inválida cruzando tablas (ej: potencia_mw y total_estaciones)
    print("\n[TEST 7] Consulta inválida cruzando métricas de distintas tablas")
    query_7 = {
        "measures": ["potencia_mw", "total_estaciones"],
        "dimensions": ["departamento"],
        "filters": []
    }
    res_7 = execute_osam_query(query_7, user_role="Analista", user_geography="Sede Nacional")
    print("Status:", res_7["status"])
    print("Mensaje de Error Esperado:", res_7.get("message"))

if __name__ == "__main__":
    run_tests()
