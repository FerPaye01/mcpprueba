# verificar_mcp.py
import sys
import os
import json

PROJECT_DIR = r"C:\Users\opaye\Proyectos\MCPdinamicoPrueba"
sys.path.append(PROJECT_DIR)
sys.path.append(os.path.join(PROJECT_DIR, "agente-mcp"))

from semantic_registry import get_semantic_catalog

try:
    print("Obteniendo catálogo semántico real desde el MCP...")
    catalog = get_semantic_catalog(force_refresh=True)
    print("¡Conexión exitosa!")
    print("Tablas encontradas:", list(catalog["tables"].keys()))
    for t_name, t_data in catalog["tables"].items():
        print(f"\nTabla: {t_name} - {t_data['description']}")
        print("Columnas:")
        for col in t_data["columns"]:
            print(f"  - {col['name']} ({col['type']}): {col['description']}")
except Exception as e:
    print("Error conectando al MCP real:", e)
