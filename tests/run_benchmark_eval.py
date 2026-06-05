# run_benchmark_eval.py
import os
import sys
import json
import asyncio
import time
from dotenv import load_dotenv
import openai

# 1. Cargar variables de entorno y paths
PROJECT_DIR = r"C:\Users\opaye\Proyectos\MCPdinamicoPrueba"
sys.path.append(PROJECT_DIR)
sys.path.append(os.path.join(PROJECT_DIR, "agente-mcp"))

load_dotenv(os.path.join(PROJECT_DIR, ".env"), override=True)

# 2. Definición del Ground Truth del Benchmark (50 Casos de Negocio reales)
BENCHMARK_CASES = [
    # --- Grupo A: CMO_TX_CENTRAL_GEN (18 casos) ---
    {
        "id": 1,
        "question": "¿Cuál es la potencia total instalada de todas las centrales?",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "SUM"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 2,
        "question": "¿Cuántas centrales de generación eléctrica tenemos registradas?",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "NO_CENTRAL", "aggregation": "COUNT"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 3,
        "question": "Lista de todas las centrales solares activas en Moquegua.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "NO_CENTRAL", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "TECNOLOGIA", "operator": "equals", "value": "Solar"},
                {"field": "DEPARTAMENTO", "operator": "equals", "value": "MOQUEGUA"},
                {"field": "ESTADO", "operator": "equals", "value": "En Servicio"}
            ]
        }
    },
    {
        "id": 4,
        "question": "Muestra la potencia instalada promedio por tecnología de generación.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "AVG"}],
            "dimensions": ["TECNOLOGIA"],
            "filters": []
        }
    },
    {
        "id": 5,
        "question": "¿Cuál es la central eólica con mayor capacidad de generación?",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "MAX"}, {"name": "NO_CENTRAL", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "TECNOLOGIA", "operator": "equals", "value": "Eólica"}
            ]
        }
    },
    {
        "id": 6,
        "question": "Compara la potencia máxima instalada entre centrales hidráulicas y térmicas.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "MAX"}],
            "dimensions": ["TECNOLOGIA"],
            "filters": [
                {"field": "TECNOLOGIA", "operator": "in", "value": ["Hidráulica", "Térmica"]}
            ]
        }
    },
    {
        "id": 7,
        "question": "¿Cuántas centrales en mantenimiento hay por departamento?",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "NO_CENTRAL", "aggregation": "COUNT"}],
            "dimensions": ["DEPARTAMENTO"],
            "filters": [
                {"field": "ESTADO", "operator": "equals", "value": "Mantenimiento"}
            ]
        }
    },
    {
        "id": 8,
        "question": "Lista el nombre y estado de las centrales en el departamento de Tacna.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "NO_CENTRAL", "aggregation": "NONE"}, {"name": "ESTADO", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "DEPARTAMENTO", "operator": "equals", "value": "TACNA"}
            ]
        }
    },
    {
        "id": 9,
        "question": "Suma de la potencia de centrales hidroeléctricas en Lima y Huancavelica.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "SUM"}],
            "dimensions": [],
            "filters": [
                {"field": "TECNOLOGIA", "operator": "equals", "value": "Hidráulica"},
                {"field": "DEPARTAMENTO", "operator": "in", "value": ["LIMA", "HUANCAVELICA"]}
            ]
        }
    },
    {
        "id": 10,
        "question": "¿Qué tecnologías operan en el departamento de Ica y cuánta potencia suman?",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "SUM"}],
            "dimensions": ["TECNOLOGIA"],
            "filters": [
                {"field": "DEPARTAMENTO", "operator": "equals", "value": "ICA"}
            ]
        }
    },
    {
        "id": 11,
        "question": "Muestra las centrales que no estén en servicio actualmente.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "NO_CENTRAL", "aggregation": "NONE"}, {"name": "ESTADO", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "ESTADO", "operator": "equals", "value": "Mantenimiento"} # o no en servicio
            ]
        }
    },
    {
        "id": 12,
        "question": "Promedio de potencia instalada de centrales térmicas.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "AVG"}],
            "dimensions": [],
            "filters": [
                {"field": "TECNOLOGIA", "operator": "equals", "value": "Térmica"}
            ]
        }
    },
    {
        "id": 13,
        "question": "Potencia mínima registrada para una central solar.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "MIN"}],
            "dimensions": [],
            "filters": [
                {"field": "TECNOLOGIA", "operator": "equals", "value": "Solar"}
            ]
        }
    },
    {
        "id": 14,
        "question": "Cuántas centrales solares hay en el departamento de Arequipa.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "NO_CENTRAL", "aggregation": "COUNT"}],
            "dimensions": [],
            "filters": [
                {"field": "TECNOLOGIA", "operator": "equals", "value": "Solar"},
                {"field": "DEPARTAMENTO", "operator": "equals", "value": "AREQUIPA"}
            ]
        }
    },
    {
        "id": 15,
        "question": "Muestra la potencia total de centrales por departamento.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "POTENCIA_MW", "aggregation": "SUM"}],
            "dimensions": ["DEPARTAMENTO"],
            "filters": []
        }
    },
    {
        "id": 16,
        "question": "Nombres de centrales hidroeléctricas con potencia mayor a 100 MW.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "NO_CENTRAL", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "TECNOLOGIA", "operator": "equals", "value": "Hidráulica"},
                {"field": "POTENCIA_MW", "operator": "greater_than", "value": "100"}
            ]
        }
    },
    {
        "id": 17,
        "question": "Lista de tecnologías de generación registradas en el sistema.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "TECNOLOGIA", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 18,
        "question": "Conteo de centrales activas por tecnología.",
        "expected": {
            "table": "CMO_TX_CENTRAL_GEN",
            "fields": [{"name": "NO_CENTRAL", "aggregation": "COUNT"}],
            "dimensions": ["TECNOLOGIA"],
            "filters": [
                {"field": "ESTADO", "operator": "equals", "value": "En Servicio"}
            ]
        }
    },

    # --- Grupo B: VW_EESS_UBICACION_GEO (16 casos) ---
    {
        "id": 19,
        "question": "¿Cuántas estaciones de servicio hay en total a nivel nacional?",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "COUNT"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 20,
        "question": "Grifos autorizados en la provincia de Ilo.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "PROVINCIA", "operator": "equals", "value": "ILO"}
            ]
        }
    },
    {
        "id": 21,
        "question": "Cantidad de estaciones de servicio agrupadas por departamento.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "COUNT"}],
            "dimensions": ["DEPARTAMENTO"],
            "filters": []
        }
    },
    {
        "id": 22,
        "question": "Muestra las coordenadas latitud y longitud del Grifo Repsol Charcani.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "LATITUD", "aggregation": "NONE"}, {"name": "LONGITUD", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "NO_ESTACION", "operator": "equals", "value": "GRIFO REPSOL CHARCANI"}
            ]
        }
    },
    {
        "id": 23,
        "question": "¿Cuántos establecimientos registrados hay en el distrito de San Luis, Lima?",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "COUNT"}],
            "dimensions": [],
            "filters": [
                {"field": "DISTRITO", "operator": "equals", "value": "SAN LUIS"},
                {"field": "PROVINCIA", "operator": "equals", "value": "LIMA"}
            ]
        }
    },
    {
        "id": 24,
        "question": "Lista de grifos en Arequipa y Moquegua.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "DEPARTAMENTO", "operator": "in", "value": ["AREQUIPA", "MOQUEGUA"]}
            ]
        }
    },
    {
        "id": 25,
        "question": "Conteo de grifos por provincia en el departamento de Lima.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "COUNT"}],
            "dimensions": ["PROVINCIA"],
            "filters": [
                {"field": "DEPARTAMENTO", "operator": "equals", "value": "LIMA"}
            ]
        }
    },
    {
        "id": 26,
        "question": "Dame la ubicación georreferenciada de las estaciones en Cayma.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "NONE"}, {"name": "LATITUD", "aggregation": "NONE"}, {"name": "LONGITUD", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "DISTRITO", "operator": "equals", "value": "CAYMA"}
            ]
        }
    },
    {
        "id": 27,
        "question": "¿Hay grifos registrados en Comas?",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "COUNT"}],
            "dimensions": [],
            "filters": [
                {"field": "DISTRITO", "operator": "equals", "value": "COMAS"}
            ]
        }
    },
    {
        "id": 28,
        "question": "Estaciones de servicio ordenadas por distrito en Moquegua.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "NONE"}],
            "dimensions": ["DISTRITO"],
            "filters": [
                {"field": "DEPARTAMENTO", "operator": "equals", "value": "MOQUEGUA"}
            ]
        }
    },
    {
        "id": 29,
        "question": "Estaciones de servicio de la provincia de Arequipa.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "PROVINCIA", "operator": "equals", "value": "AREQUIPA"}
            ]
        }
    },
    {
        "id": 30,
        "question": "Distritos con grifos en la provincia de Ilo.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "DISTRITO", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "PROVINCIA", "operator": "equals", "value": "ILO"}
            ]
        }
    },
    {
        "id": 31,
        "question": "Cantidad de grifos en Moquegua.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "COUNT"}],
            "dimensions": [],
            "filters": [
                {"field": "DEPARTAMENTO", "operator": "equals", "value": "MOQUEGUA"}
            ]
        }
    },
    {
        "id": 32,
        "question": "Coordenadas del Grifo Primax El Pino.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "LATITUD", "aggregation": "NONE"}, {"name": "LONGITUD", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "NO_ESTACION", "operator": "equals", "value": "GRIFO PRIMAX EL PINO"}
            ]
        }
    },
    {
        "id": 33,
        "question": "Lista de grifos en el distrito de San Luis.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "DISTRITO", "operator": "equals", "value": "SAN LUIS"}
            ]
        }
    },
    {
        "id": 34,
        "question": "Conteo de establecimientos por departamento.",
        "expected": {
            "table": "VW_EESS_UBICACION_GEO",
            "fields": [{"name": "NO_ESTACION", "aggregation": "COUNT"}],
            "dimensions": ["DEPARTAMENTO"],
            "filters": []
        }
    },

    # --- Grupo C: DEMANDA_DIARIA_ELEC (16 casos) ---
    {
        "id": 35,
        "question": "¿Cuál fue la demanda máxima histórica registrada en el sistema?",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "DEMANDA_MAX_MW", "aggregation": "MAX"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 36,
        "question": "Suma de la generación de energía total en GWh del periodo disponible.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "GENERACION_GWH", "aggregation": "SUM"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 37,
        "question": "Promedio diario de la demanda de electricidad registrada.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "DEMANDA_MAX_MW", "aggregation": "AVG"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 38,
        "question": "Muestra la generación en GWh diaria y la demanda máxima para cada fecha.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "GENERACION_GWH", "aggregation": "NONE"}, {"name": "DEMANDA_MAX_MW", "aggregation": "NONE"}],
            "dimensions": ["FECHA"],
            "filters": []
        }
    },
    {
        "id": 39,
        "question": "¿Cuál fue el promedio de generación en gigavatios-hora a partir del 25 de enero de 2024?",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "GENERACION_GWH", "aggregation": "AVG"}],
            "dimensions": [],
            "filters": [
                {"field": "FECHA", "operator": "greater_than", "value": "2024-01-25"}
            ]
        }
    },
    {
        "id": 40,
        "question": "Demanda máxima diaria en el SEIN antes del 15 de enero de 2024.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "DEMANDA_MAX_MW", "aggregation": "NONE"}],
            "dimensions": ["FECHA"],
            "filters": [
                {"field": "FECHA", "operator": "less_than", "value": "2024-01-15"}
            ]
        }
    },
    {
        "id": 41,
        "question": "Encuentra el día con la generación eléctrica más baja.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "GENERACION_GWH", "aggregation": "MIN"}, {"name": "FECHA", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 42,
        "question": "¿Cómo se comportó la demanda máxima entre el 10 y el 20 de enero de 2024?",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "DEMANDA_MAX_MW", "aggregation": "NONE"}],
            "dimensions": ["FECHA"],
            "filters": [
                {"field": "FECHA", "operator": "greater_than", "value": "2024-01-10"},
                {"field": "FECHA", "operator": "less_than", "value": "2024-01-20"}
            ]
        }
    },
    {
        "id": 43,
        "question": "Suma de energía generada acumulada por día.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "GENERACION_GWH", "aggregation": "SUM"}],
            "dimensions": ["FECHA"],
            "filters": []
        }
    },
    {
        "id": 44,
        "question": "Demanda máxima promedio registrada después del 20 de enero de 2024.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "DEMANDA_MAX_MW", "aggregation": "AVG"}],
            "dimensions": [],
            "filters": [
                {"field": "FECHA", "operator": "greater_than", "value": "2024-01-20"}
            ]
        }
    },
    {
        "id": 45,
        "question": "Generación diaria promedio durante todo el periodo.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "GENERACION_GWH", "aggregation": "AVG"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 46,
        "question": "Muestra la demanda máxima para el 15 de enero de 2024.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "DEMANDA_MAX_MW", "aggregation": "NONE"}],
            "dimensions": [],
            "filters": [
                {"field": "FECHA", "operator": "equals", "value": "2024-01-15"}
            ]
        }
    },
    {
        "id": 47,
        "question": "Generación acumulada antes del 5 de enero de 2024.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "GENERACION_GWH", "aggregation": "SUM"}],
            "dimensions": [],
            "filters": [
                {"field": "FECHA", "operator": "less_than", "value": "2024-01-05"}
            ]
        }
    },
    {
        "id": 48,
        "question": "Lista de las demandas diarias registradas.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "DEMANDA_MAX_MW", "aggregation": "NONE"}],
            "dimensions": ["FECHA"],
            "filters": []
        }
    },
    {
        "id": 49,
        "question": "Máxima generación de energía diaria registrada.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "GENERACION_GWH", "aggregation": "MAX"}],
            "dimensions": [],
            "filters": []
        }
    },
    {
        "id": 50,
        "question": "Demanda máxima promedio de energía entre el 5 y el 15 de enero.",
        "expected": {
            "table": "DEMANDA_DIARIA_ELEC",
            "fields": [{"name": "DEMANDA_MAX_MW", "aggregation": "AVG"}],
            "dimensions": [],
            "filters": [
                {"field": "FECHA", "operator": "greater_than", "value": "2024-01-05"},
                {"field": "FECHA", "operator": "less_than", "value": "2024-01-15"}
            ]
        }
    }
]

# 3. Metadatos del catálogo Oracle (Físicos y comentarios emulados del MCP)
CATALOG_METADATA = {
    "tables": {
        "CMO_TX_CENTRAL_GEN": {
            "description": "Centrales de generación eléctrica registradas en el sistema SEIN (térmica, hidráulica, solar, eólica).",
            "columns": [
                {"name": "NO_CENTRAL", "type": "VARCHAR2", "description": "Nombre oficial de la central de generación eléctrica."},
                {"name": "DEPARTAMENTO", "type": "VARCHAR2", "description": "Nombre de la región o departamento político donde está ubicada físicamente la central (ej: LIMA, MOQUEGUA, TACNA, ICA, AREQUIPA)."},
                {"name": "POTENCIA_MW", "type": "NUMBER", "description": "Capacidad o potencia nominal instalada de la central de generación en Megavatios (MW)."},
                {"name": "TECNOLOGIA", "type": "VARCHAR2", "description": "Tipo de tecnología de generación de energía (ej: Hidráulica, Térmica, Solar, Eólica, Biomasa)."},
                {"name": "ESTADO", "type": "VARCHAR2", "description": "Estado de operatividad operativa actual de la central (ej: En Servicio, Mantenimiento, Fuera de Servicio)."}
            ]
        },
        "VW_EESS_UBICACION_GEO": {
            "description": "Estaciones de servicio y grifos de combustibles líquidos y GLP georreferenciados a nivel nacional.",
            "columns": [
                {"name": "NO_ESTACION", "type": "VARCHAR2", "description": "Nombre comercial de la estación de servicio o grifo (ej: GRIFO PRIMAX, REPSOL)."},
                {"name": "DEPARTAMENTO", "type": "VARCHAR2", "description": "Departamento político geográfico del grifo (ej: LIMA, AREQUIPA, MOQUEGUA)."},
                {"name": "PROVINCIA", "type": "VARCHAR2", "description": "Provincia geográfica política del establecimiento (ej: LIMA, AREQUIPA, ILO)."},
                {"name": "DISTRITO", "type": "VARCHAR2", "description": "Distrito político geográfico de la estación de servicio (ej: SAN LUIS, CAYMA, ILO, COMAS)."},
                {"name": "LATITUD", "type": "NUMBER", "description": "Coordenada geográfica de latitud para mapeo cartográfico."},
                {"name": "LONGITUD", "type": "NUMBER", "description": "Coordenada geográfica de longitud para mapeo cartográfico."}
            ]
        },
        "DEMANDA_DIARIA_ELEC": {
            "description": "Estadísticas e indicadores diarios de la demanda de electricidad y generación en el Sistema Eléctrico Interconectado Nacional (SEIN).",
            "columns": [
                {"name": "FECHA", "type": "DATE", "description": "Fecha del registro diario en formato estándar ISO YYYY-MM-DD."},
                {"name": "DEMANDA_MAX_MW", "type": "NUMBER", "description": "Pico máximo de potencia demandada en Megavatios (MW) durante ese día en el SEIN."},
                {"name": "GENERACION_GWH", "type": "NUMBER", "description": "Energía total generada diaria acumulada expresada en Gigavatios-hora (GWh)."}
            ]
        }
    }
}

# 4. Prompt del Sistema para las Pruebas (Igual al de app.py pero refinado para retornar sólo JSON en Tool Call)
TEST_SYSTEM_PROMPT = """
Eres el motor de traducción semántica y generación de consultas OSAM v2 de Osinergmin.
Tu única tarea es analizar la pregunta en lenguaje natural del usuario y traducirla a una consulta estructurada llamando a la herramienta `query_data_osam`.

Tienes acceso al siguiente Catálogo Físico de Datos de Oracle (basado en comentarios reales DE_TABLA y DE_COLUMNA):
{catalog_serialized}

REGLAS DE TRADUCCIÓN:
1. Identifica la tabla correcta basándote en las descripciones.
2. Identifica los campos y sus agregaciones correctas (SUM, AVG, MAX, MIN, COUNT o NONE si es listado descriptivo) basándote en la intención del usuario.
3. Si el usuario pide agrupar o ver tendencias por alguna categoría/fecha, ponla en `dimensions`.
4. Si el usuario pide un departamento, distrito, tecnología, rango de fechas u otro, tradúcelo a filtros en `filters` usando el operador correcto ("equals", "in", "greater_than", "less_than").
   Formatos de fecha: Siempre en formato YYYY-MM-DD.
   Operadores:
   - equals: igualdad exacta.
   - in: para múltiples valores (ej: ['AREQUIPA', 'MOQUEGUA']).
   - greater_than: para mayor que (ej: potencia > 100).
   - less_than: para menor que (ej: fecha < '2024-01-15').

Debes invocar la herramienta `query_data_osam` de forma obligatoria.
"""

def serialize_catalog(catalog):
    lines = []
    for tab_name, tab_spec in catalog["tables"].items():
        lines.append(f"Tabla: {tab_name} - Desc: {tab_spec['description']}")
        lines.append("Columnas:")
        for col in tab_spec["columns"]:
            lines.append(f"  - {col['name']} ({col['type']}): {col['description']}")
        lines.append("")
    return "\n".join(lines)

def build_openai_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "query_data_osam",
                "description": "Ejecuta consultas analíticas gobernadas en la base de datos a partir de una intención semántica estructurada (OSAM Query).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "object",
                            "properties": {
                                "fields": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "aggregation": {"type": "string", "enum": ["SUM", "AVG", "MAX", "MIN", "COUNT", "NONE"]}
                                        },
                                        "required": ["name", "aggregation"]
                                    }
                                },
                                "dimensions": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "filters": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "field": {"type": "string"},
                                            "operator": {"type": "string", "enum": ["equals", "in", "greater_than", "less_than"]},
                                            "value": {"type": "string"}
                                        },
                                        "required": ["field", "operator", "value"]
                                    }
                                }
                            },
                            "required": ["fields"]
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]

# 5. Lógica del Validador / Evaluador
def evaluate_query(actual, expected):
    score_table = 0.0
    score_columns = 0.0
    score_aggregation = 0.0
    score_geo_filters = 1.0 # Por defecto 1.0, penaliza si hay fallas
    score_temp_filters = 1.0 # Por defecto 1.0, penaliza si hay fallas

    # Inferencia de tabla en el actual:
    # Como la herramienta del LLM no pasa el nombre de la tabla directamente, sino que el Gateway
    # la infiere por las columnas solicitadas, nosotros la inferimos usando la metadata del catálogo
    actual_fields = [f["name"].upper() for f in actual.get("fields", [])]
    actual_dims = [d.upper() for d in actual.get("dimensions", [])]
    all_actual_cols = actual_fields + actual_dims
    
    inferred_table = None
    for t_name, t_spec in CATALOG_METADATA["tables"].items():
        valid_cols = [c["name"].upper() for c in t_spec["columns"]]
        if all(col in valid_cols for col in all_actual_cols):
            inferred_table = t_name
            break

    # 1. Selección de Tabla (25%)
    expected_table = expected["table"].upper()
    if inferred_table == expected_table:
        score_table = 1.0

    # 2. Selección de Columnas (25%) & Agregación (20%)
    expected_fields_dict = {f["name"].upper(): f["aggregation"].upper() for f in expected["fields"]}
    actual_fields_dict = {f["name"].upper(): f.get("aggregation", "NONE").upper() for f in actual.get("fields", [])}
    
    matched_cols = 0
    matched_aggs = 0
    total_cols = len(expected_fields_dict)

    for col_name, agg in expected_fields_dict.items():
        if col_name in actual_fields_dict:
            matched_cols += 1
            if actual_fields_dict[col_name] == agg:
                matched_aggs += 1

    if total_cols > 0:
        score_columns = matched_cols / total_cols
        score_aggregation = matched_aggs / total_cols

    # 3. Filtros Geográficos & Temporales
    expected_filters = expected.get("filters", [])
    actual_filters = actual.get("filters", [])

    # Clasificar filtros esperados en geo vs temporales vs otros
    geo_cols = ["DEPARTAMENTO", "PROVINCIA", "DISTRITO"]
    temp_cols = ["FECHA"]

    expected_geo = [f for f in expected_filters if f["field"].upper() in geo_cols]
    expected_temp = [f for f in expected_filters if f["field"].upper() in temp_cols]
    expected_others = [f for f in expected_filters if f["field"].upper() not in geo_cols and f["field"].upper() not in temp_cols]

    actual_geo = [f for f in actual_filters if f["field"].upper() in geo_cols]
    actual_temp = [f for f in actual_filters if f["field"].upper() in temp_cols]
    actual_others = [f for f in actual_filters if f["field"].upper() not in geo_cols and f["field"].upper() not in temp_cols]

    # Evaluar Geo
    if expected_geo:
        geo_matches = 0
        for eg in expected_geo:
            # Buscar en actual_geo
            for ag in actual_geo:
                if ag["field"].upper() == eg["field"].upper() and ag["operator"] == eg["operator"]:
                    # Comparar valor normalizando mayúsculas/minúsculas y listas
                    v_e = eg["value"]
                    v_a = ag["value"]
                    if isinstance(v_e, list):
                        v_e_norm = sorted([str(x).upper() for x in v_e])
                    else:
                        v_e_norm = str(v_e).upper()
                    
                    if isinstance(v_a, list):
                        v_a_norm = sorted([str(x).upper() for x in v_a])
                    else:
                        v_a_norm = str(v_a).upper()

                    if v_e_norm == v_a_norm:
                        geo_matches += 1
                        break
        score_geo_filters = geo_matches / len(expected_geo) if expected_geo else 1.0
    else:
        # Si no se esperaba geo y el LLM agregó uno incorrecto
        if actual_geo:
            score_geo_filters = 0.0

    # Evaluar Temporal
    if expected_temp:
        temp_matches = 0
        for et in expected_temp:
            for at in actual_temp:
                if at["field"].upper() == et["field"].upper() and at["operator"] == et["operator"]:
                    # Quitar comillas o guiones si es fecha
                    val_e = str(et["value"]).replace("-", "").strip()
                    val_a = str(at["value"]).replace("-", "").strip()
                    if val_e == val_a:
                        temp_matches += 1
                        break
        score_temp_filters = temp_matches / len(expected_temp) if expected_temp else 1.0
    else:
        if actual_temp:
            score_temp_filters = 0.0

    # Puntuación agregada del caso (Pesos: Tabla 25%, Columna 25%, Agregación 20%, Geo 15%, Temp 15%)
    weighted_score = (score_table * 0.25) + (score_columns * 0.25) + (score_aggregation * 0.20) + (score_geo_filters * 0.15) + (score_temp_filters * 0.15)
    
    return {
        "score_table": score_table,
        "score_columns": score_columns,
        "score_aggregation": score_aggregation,
        "score_geo_filters": score_geo_filters,
        "score_temp_filters": score_temp_filters,
        "weighted_score": weighted_score,
        "inferred_table": inferred_table
    }

async def run_benchmark():
    print("=== INICIANDO BENCHMARK CUANTITATIVO DE PRECISIÓN SEMÁNTICA (50 CASOS) ===")
    
    # Determinar qué modelo y proveedor usar según .env
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        model_name = "gemini-2.5-flash"
        print(f"Usando Google AI Studio con {model_name}...")
    else:
        api_key = os.getenv("LLM_API_KEY")
        base_url = "https://openrouter.ai/api/v1"
        model_name = "google/gemini-2.5-flash" # fallback a OpenRouter
        print(f"Usando OpenRouter con {model_name}...")

    if not api_key:
        print("❌ Error crítico: No se encontró API_KEY en el archivo .env.")
        return

    client = openai.AsyncOpenAI(
        base_url=base_url,
        api_key=api_key
    )

    catalog_serialized = serialize_catalog(CATALOG_METADATA)
    system_prompt = TEST_SYSTEM_PROMPT.format(catalog_serialized=catalog_serialized)
    openai_tools = build_openai_tools()

    results_log = []
    total_cases = len(BENCHMARK_CASES)
    passed_cases = 0 # Casos con weighted_score == 1.0

    sum_table = 0.0
    sum_cols = 0.0
    sum_agg = 0.0
    sum_geo = 0.0
    sum_temp = 0.0
    sum_weighted = 0.0

    for idx, case in enumerate(BENCHMARK_CASES):
        print(f"\n[CASO {case['id']}/{total_cases}] Pregunta: {case['question']}")
        
        # Enviar petición al LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": case["question"]}
        ]
        
        actual_query = None
        cot = ""
        error_msg = None
        
        for attempt in range(3): # Reintentar hasta 3 veces ante rate limits (429)
            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice={"type": "function", "function": {"name": "query_data_osam"}},
                    temperature=0.0
                )
                
                # Extraer razonamiento e intent
                choice = response.choices[0]
                cot = getattr(choice.message, "content", "") or ""
                
                # Extraer tool call
                tool_calls = getattr(choice.message, "tool_calls", None)
                if tool_calls:
                    tc = tool_calls[0]
                    raw_args = tc.function.arguments
                    args = json.loads(raw_args)
                    actual_query = args.get("query", {})
                break
            except Exception as e:
                is_rate_limit = "429" in str(e) or "rate" in str(e).lower()
                if is_rate_limit:
                    wait_time = (attempt + 1) * 5
                    print(f"  [429 Rate Limit] Esperando {wait_time}s antes de reintentar...")
                    await asyncio.sleep(wait_time)
                else:
                    error_msg = str(e)
                    print(f"  [ERROR] Falló llamada: {e}")
                    break

        if not actual_query:
            print("  -> ❌ No se generó query estructurada (Error o timeout).")
            eval_res = {
                "score_table": 0.0, "score_columns": 0.0, "score_aggregation": 0.0,
                "score_geo_filters": 0.0, "score_temp_filters": 0.0, "weighted_score": 0.0,
                "inferred_table": None
            }
        else:
            # Evaluar query actual vs esperada
            eval_res = evaluate_query(actual_query, case["expected"])
            print(f"  -> Inferred Table: {eval_res['inferred_table']}")
            print(f"  -> Generated Query: {json.dumps(actual_query)}")
            print(f"  -> Score: {eval_res['weighted_score']:.2f}")

        # Acumular
        sum_table += eval_res["score_table"]
        sum_cols += eval_res["score_columns"]
        sum_agg += eval_res["score_aggregation"]
        sum_geo += eval_res["score_geo_filters"]
        sum_temp += eval_res["score_temp_filters"]
        sum_weighted += eval_res["weighted_score"]
        
        if eval_res["weighted_score"] >= 0.99: # numérico
            passed_cases += 1

        results_log.append({
            "case_id": case["id"],
            "question": case["question"],
            "expected": case["expected"],
            "actual": actual_query,
            "evaluation": eval_res,
            "chain_of_thought": cot,
            "error": error_msg
        })
        
        # Espera suave para mitigar rate limits por minuto en APIs gratuitas
        await asyncio.sleep(1)

    # Calcular métricas globales
    tpt = (sum_table / total_cases) * 100
    tpc = (sum_cols / total_cases) * 100
    tpa = (sum_agg / total_cases) * 100
    tpg = (sum_geo / total_cases) * 100
    tptemp = (sum_temp / total_cases) * 100
    pco = (passed_cases / total_cases) * 100
    promedio_weighted = (sum_weighted / total_cases) * 100

    print("\n" + "="*50)
    print("=== RESULTADOS DEL BENCHMARK ===")
    print(f"Total de Casos Evaluados: {total_cases}")
    print(f"Casos Exitosos (Exactitud 100%): {passed_cases} / {total_cases}")
    print(f"Tasa de Precisión de Tabla (TPT): {tpt:.2f}%")
    print(f"Tasa de Precisión de Columna (TPC): {tpc:.2f}%")
    print(f"Tasa de Precisión de Agregación (TPA): {tpa:.2f}%")
    print(f"Tasa de Precisión Filtros Geo (TPG): {tpg:.2f}%")
    print(f"Tasa de Precisión Filtros Temp (TPTEMP): {tptemp:.2f}%")
    print(f"Precisión de Consulta OSAM (PCO - Casos Perfectos): {pco:.2f}%")
    print(f"Puntuación Promedio Ponderada: {promedio_weighted:.2f}%")
    print("="*50)

    # Guardar reporte JSON y Logs de auditoría
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_used": model_name,
        "metrics": {
            "total_cases": total_cases,
            "perfect_cases": passed_cases,
            "TPT": tpt,
            "TPC": tpc,
            "TPA": tpa,
            "TPG": tpg,
            "TPTEMP": tptemp,
            "PCO": pco,
            "average_score": promedio_weighted
        },
        "results": results_log
    }

    report_path = r"C:\Users\opaye\.gemini\antigravity-cli\brain\f866c370-1183-4d6f-ae27-198526c7a164\scratch\benchmark_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Reporte de evaluación cuantitativa exportado a: {report_path}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
