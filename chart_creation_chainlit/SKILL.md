---
name: chart_creation_chainlit
description: Guía de integración y mejores prácticas para generar y visualizar gráficos (líneas, barras, pastel) en aplicaciones de chat Chainlit utilizando matplotlib.
---

# Skill de Creación de Gráficos en Chainlit

Esta skill proporciona los estándares de desarrollo, esquemas de herramientas y patrones de código para dar a los modelos de lenguaje (LLM) la habilidad de generar gráficos en tiempo real sobre datos de consulta, renderizándolos inline de forma elegante y rápida.

## 🛠️ Arquitectura del Sistema de Gráficos

El flujo de trabajo óptimo para la visualización de datos en Chainlit + LLM (Gemini/OpenRouter) se basa en la separación de datos y presentación:

```mermaid
graph TD
    A[Usuario solicita gráfico / tendencia] --> B[LLM invoca herramienta de datos (ej: query_data)]
    B --> C[Backend guarda datos en cl.user_session]
    C --> D[LLM analiza columnas e invoca tool: crear_grafico]
    D --> E[Backend dibuja la figura usando Matplotlib]
    E --> F[Backend envía cl.Pyplot de forma inline]
```

## 📊 Especificación de la Herramienta (Schema)

La herramienta expuesta al LLM debe tener el siguiente esquema en formato OpenAI/OpenRouter:

```json
{
  "type": "function",
  "function": {
    "name": "crear_grafico",
    "description": "Genera y muestra un gráfico (de líneas, barras, dispersión o pastel) en el chat a partir de los últimos datos de la consulta. Úsala si el usuario pide explícitamente graficar, ver tendencias o comparar datos visualmente.",
    "parameters": {
      "type": "object",
      "properties": {
        "tipo_grafico": {
          "type": "string",
          "enum": ["lineas", "barras", "dispersion", "pastel"],
          "description": "El tipo de gráfico a generar."
        },
        "columna_x": {
          "type": "string",
          "description": "El nombre exacto de la columna para el eje X (e.g. fecha, año, categorías)."
        },
        "columna_y": {
          "type": "string",
          "description": "El nombre exacto de la columna para el eje Y (valores numéricos como precios, demanda, etc.)."
        },
        "titulo": {
          "type": "string",
          "description": "Un título descriptivo y formal para el gráfico."
        }
      },
      "required": ["tipo_grafico", "columna_x", "columna_y"]
    }
  }
}
```

## 💻 Patrón de Código en Python (Chainlit)

### 1. Inicialización de la figura sin GUI
Para evitar conflictos de hilos y bloqueos en el backend del chat, configure Matplotlib en el backend no interactivo `Agg`:

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
```

### 2. Generación del gráfico con cl.Pyplot
Utilice `cl.Pyplot` con `display="inline"` para mostrar el gráfico directamente al usuario final dentro de la misma burbuja de diálogo, reduciendo la fricción:

```python
import chainlit as cl

async def run_local_chart_tool(args, last_result):
    # 1. Cargar datos en Pandas
    df = pd.DataFrame(last_result)
    
    # 2. Dibujar figura
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df[args["columna_x"]], df[args["columna_y"]], marker='o')
    ax.set_title(args.get("titulo", "Gráfico"))
    
    # 3. Enviar a Chainlit
    await cl.Message(
        content=f"📊 Gráfico generado",
        elements=[cl.Pyplot(figure=fig, name="grafico", display="inline")]
    ).send()
    
    plt.close(fig)
```
