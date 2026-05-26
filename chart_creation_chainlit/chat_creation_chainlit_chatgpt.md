A robust pattern for data visualization in a [Chainlit](https://docs.chainlit.io?utm_source=chatgpt.com) app is to treat charts as **LLM-callable tools** rather than trying to have the model generate plotting code directly in the conversation. This gives you:

* deterministic chart generation,
* safer execution,
* reusable plotting logic,
* session-aware datasets,
* cleaner UX,
* and compatibility across both [Gemini API](https://ai.google.dev?utm_source=chatgpt.com) and [OpenRouter](https://openrouter.ai?utm_source=chatgpt.com) tool-calling flows.

Chainlit already supports inline rendering for both Matplotlib and Plotly through `cl.Pyplot`, `cl.Plotly`, and `cl.Image`. ([docs.chainlit.io][1])

# Recommended Architecture

```text
User
  ↓
Chainlit UI
  ↓
LLM (Gemini/OpenRouter)
  ↓ tool call
Visualization Tool Layer
  ↓
Dataset Registry / Session State
  ↓
Matplotlib / Plotly Figure
  ↓
cl.Pyplot / cl.Plotly / cl.Image
```

The key design principle:

> The LLM chooses *what* visualization to create, but your backend controls *how* it is created.

---

# Best Practices

## 1. Never Let the LLM Execute Arbitrary Plotting Code

Avoid:

```python
exec(model_generated_python)
```

Instead:

* expose strongly typed plotting tools,
* validate arguments,
* whitelist chart types,
* map semantic requests → deterministic plotting functions.

Good:

```python
{
  "name": "plot_sales_trend",
  "parameters": {
    "metric": "revenue",
    "group_by": "month"
  }
}
```

Bad:

```python
"Run this matplotlib code..."
```

This is especially important with Gemini/OpenRouter tool calling because malformed arguments or hallucinated APIs are common failure modes. Community discussions repeatedly mention inconsistent tool parameter formatting with Gemini-family models. ([Reddit][2])

---

# 2. Use Session-Based Dataset Registries

Store datasets in Chainlit session state:

```python
cl.user_session.set("datasets", {
    "sales_df": sales_df,
    "inventory_df": inventory_df
})
```

Then tools reference datasets symbolically:

```json
{
  "dataset": "sales_df",
  "chart_type": "line"
}
```

Instead of embedding raw tables into prompts.

This:

* reduces token usage,
* improves reliability,
* prevents context overflow,
* avoids leaking unnecessary data.

---

# 3. Keep the LLM Prompt Focused on Visualization Intent

Your system prompt should describe:

* available datasets,
* semantic columns,
* supported chart types,
* chart-selection heuristics.

Example:

```text
Available datasets:
- sales_df: monthly sales metrics
Columns:
  - month
  - revenue
  - units_sold

Available visualization tools:
- create_line_chart
- create_bar_chart
- create_scatter_plot

Use:
- line charts for trends
- bar charts for comparisons
- scatter plots for correlations
```

This works substantially better than dumping dataframe samples into every request.

---

# 4. Use Plotly for Interactive Analytics

Prefer `cl.Plotly` for:

* dashboards,
* zooming,
* hover inspection,
* exploratory analysis.

Chainlit supports direct Plotly figure rendering inline. ([docs.chainlit.io][1])

Example:

```python
import plotly.express as px
import chainlit as cl

async def render_plotly_chart(df):
    fig = px.line(df, x="month", y="revenue")

    await cl.Message(
        content="Revenue trend",
        elements=[
            cl.Plotly(
                name="revenue_chart",
                figure=fig,
                display="inline"
            )
        ]
    ).send()
```

Use Plotly when:

* users may inspect data interactively,
* multiple traces exist,
* dashboard-style UX matters.

---

# 5. Use Matplotlib for Deterministic Static Reports

Prefer `cl.Pyplot` when:

* generating exportable visuals,
* producing stable images,
* handling scientific charts,
* minimizing frontend overhead.

Chainlit supports inline matplotlib rendering through `cl.Pyplot`. ([docs.chainlit.io][3])

Example:

```python
import matplotlib.pyplot as plt
import chainlit as cl

async def render_pyplot(df):
    fig, ax = plt.subplots()

    ax.plot(df["month"], df["revenue"])
    ax.set_title("Revenue Trend")

    await cl.Message(
        content="Static analysis chart",
        elements=[
            cl.Pyplot(
                name="revenue_plot",
                figure=fig,
                display="inline"
            )
        ]
    ).send()
```

---

# 6. Separate “Analysis Tools” from “Rendering Tools”

A common mistake:

```text
tool = create_chart
```

Better:

```text
tool = analyze_dataset
tool = choose_visualization
tool = render_visualization
```

This separation:

* improves composability,
* reduces hallucinations,
* allows multi-step reasoning.

Example pipeline:

```text
1. summarize_dataset()
2. detect_relationships()
3. select_chart_type()
4. render_chart()
```

---

# 7. Define Explicit Visualization Schemas

Use Pydantic or JSON Schema.

Example:

```python
from pydantic import BaseModel
from typing import Literal

class ChartRequest(BaseModel):
    dataset: str
    chart_type: Literal[
        "line",
        "bar",
        "scatter",
        "histogram"
    ]
    x: str
    y: str | None = None
    title: str
```

Then validate tool calls before rendering.

This dramatically reduces Gemini/OpenRouter tool-call instability.

---

# 8. Pass Dataset Metadata, Not Full Dataframes

Instead of:

```python
df.to_csv()
```

Pass:

```python
{
  "columns": {
      "revenue": "float",
      "month": "datetime"
  },
  "shape": [1200, 8],
  "description": "Monthly sales metrics"
}
```

Then retrieve the real dataframe server-side during tool execution.

---

# 9. Stream Intermediate Reasoning with Chainlit Steps

Chainlit `@cl.step` is excellent for visualization workflows. ([docs.chainlit.io][4])

Example:

```python
@cl.step(type="tool")
async def create_chart_tool(args):
    ...
```

This gives users:

* visible tool execution,
* progress transparency,
* debuggability.

Very useful for agentic workflows.

---

# 10. Build a Generic Visualization Router

Instead of many rigid tools:

```text
plot_sales()
plot_inventory()
plot_forecast()
```

Use one generalized router:

```python
async def visualization_tool(
    dataset,
    chart_type,
    x,
    y,
    filters=None
):
```

Internally:

```python
CHART_BUILDERS = {
    "line": build_line_chart,
    "bar": build_bar_chart,
    "scatter": build_scatter
}
```

This scales much better.

---

# Recommended Production Pattern

## LLM Tool Definition

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_visualization",
            "description": "Generate charts from datasets",
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset": {"type": "string"},
                    "chart_type": {"type": "string"},
                    "x": {"type": "string"},
                    "y": {"type": "string"},
                    "title": {"type": "string"}
                },
                "required": [
                    "dataset",
                    "chart_type",
                    "x"
                ]
            }
        }
    }
]
```

---

# Generic Tool Executor

```python
async def create_visualization(args):

    datasets = cl.user_session.get("datasets")
    df = datasets[args["dataset"]]

    chart_type = args["chart_type"]

    if chart_type == "line":
        fig = px.line(
            df,
            x=args["x"],
            y=args["y"],
            title=args["title"]
        )

        await cl.Message(
            content="Generated chart",
            elements=[
                cl.Plotly(
                    name="chart",
                    figure=fig,
                    display="inline"
                )
            ]
        ).send()
```

---

# Gemini vs OpenRouter Considerations

## Gemini

Strengths:

* strong structured reasoning,
* excellent long-context handling,
* good semantic chart selection.

Weaknesses:

* sometimes inconsistent tool-call formatting,
* occasional empty tool responses reported by developers. ([Reddit][2])

Best practices:

* use strict JSON schema,
* avoid deeply nested parameters,
* keep tools atomic,
* disable parallel tool calls when possible.

---

## OpenRouter

Strengths:

* unified provider abstraction,
* easier model swapping,
* flexible tool-calling APIs. ([OpenRouter][5])

Best practices:

* normalize tool outputs across providers,
* build a provider-agnostic adapter layer,
* implement retry logic for malformed tool arguments.

---

# Recommended UX Flow

Best UX pattern:

```text
User:
"Show monthly revenue trends"

LLM:
→ calls visualization tool

Chainlit:
→ shows "Generating visualization..."

Tool:
→ renders chart inline

Assistant:
"Revenue increased sharply in Q4."
```

Minimal friction.
No manual uploads.
No code generation exposed to users.

---

# Strong Recommendation: Use Plotly First

For modern analytical assistants:

| Library    | Best For                |
| ---------- | ----------------------- |
| Plotly     | interactive analytics   |
| Matplotlib | static scientific plots |
| Altair     | declarative analytics   |
| Bokeh      | complex dashboards      |
| Seaborn    | statistical exploration |

In Chainlit specifically, Plotly integrates most naturally for conversational analytics because of inline interactivity. ([docs.chainlit.io][1])

---

# Recommended Folder Structure

```text
app/
├── main.py
├── llm/
│   ├── provider.py
│   ├── prompts.py
│   └── tools.py
├── visualization/
│   ├── router.py
│   ├── plotly_renderer.py
│   ├── matplotlib_renderer.py
│   └── schemas.py
├── state/
│   └── session_store.py
└── datasets/
```

---

# Final Recommendation Stack

For a production-quality Chainlit visualization agent:

* UI: [Chainlit](https://docs.chainlit.io?utm_source=chatgpt.com)
* LLM API abstraction: [OpenRouter](https://openrouter.ai?utm_source=chatgpt.com)
* Primary visualization: [Plotly](https://plotly.com/python/?utm_source=chatgpt.com)
* Static exports: [Matplotlib](https://matplotlib.org/?utm_source=chatgpt.com)
* Validation: [Pydantic](https://docs.pydantic.dev?utm_source=chatgpt.com)
* Dataframes: [Pandas](https://pandas.pydata.org?utm_source=chatgpt.com)
* Tool orchestration: provider-agnostic agent loop
* State: `cl.user_session`

This combination gives the best balance of:

* reliability,
* UX,
* maintainability,
* model portability,
* and visualization quality.

[1]: https://docs.chainlit.io/api-reference/elements/plotly?utm_source=chatgpt.com "Plotly - Chainlit"
[2]: https://www.reddit.com/r/LangChain/comments/1dzp16b?utm_source=chatgpt.com "Tool Calling / Function Calling not working with Gemini"
[3]: https://docs.chainlit.io/api-reference/elements/pyplot?utm_source=chatgpt.com "Pyplot - Chainlit"
[4]: https://docs.chainlit.io/concepts/step?utm_source=chatgpt.com "Step - Chainlit"
[5]: https://openrouter.ai/docs/guides/features/tool-calling?utm_source=chatgpt.com "Tool & Function Calling | Use Tools with OpenRouter | OpenRouter | Documentation"
