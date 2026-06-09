Now let me write a comprehensive, production-ready guide with full working code:Here's a complete breakdown of every design decision in the implementation:

---

## Architecture Overview

```
User message
     │
     ▼
on_message() ── CSV upload? ── pd.read_csv() ──► user_session["dataframe"]
     │
     ▼
run_agent()  ◄── build_system_prompt() injects column names + dtypes
     │
     ▼
OpenRouter /v1/chat/completions (tools=TOOLS)
     │
     ├── tool_calls? ──► dispatch_tool() ──► plot_bar / plot_line / …
     │       │                                    │
     │       │                         Plotly → PNG → cl.Image
     │       │                         Matplotlib   → cl.Pyplot
     │       └──► append tool_result to history ──► loop back to LLM
     │
     └── text response ──► cl.Message(content=…).send()
```

---

## The 6 Best Practices Implemented

**1. Tool Schema Design** — Each tool has a narrow, single-purpose signature with clear descriptions. The LLM picks the right one reliably because the descriptions say *when* to use each chart type, not just *what* it does. Optional parameters (`color_col`, `size_col`) are marked optional so the model doesn't hallucinate required fields.

**2. Session-Scoped Dataset State** — The DataFrame lives in `cl.user_session` (per-user, per-session dict). It's set once on CSV upload and read by every tool call. History is also stored there, giving the LLM full conversation context across turns. Uploading a new file resets history so stale column references don't bleed in.

**3. Dynamic System Prompt Injection** — `build_system_prompt()` is called fresh on every LLM invocation. It embeds the actual column names and dtypes from the live DataFrame. This means the LLM always has accurate column info without needing to call `summarize_dataset` first — but that tool is still available for edge cases.

**4. Agentic Tool Loop** — `run_agent()` runs a `for` loop up to 10 iterations. Each iteration sends the full history and checks if the response contains `tool_calls`. If yes, it dispatches all tools in the batch, appends the results as `role: "tool"` messages, and loops again. This naturally supports multi-step chains like *"summarize then plot"* without any special wiring.

**5. Dual Renderer Strategy** — Plotly charts use `fig.to_image(format="png")` via `kaleido` wrapped in `cl.Image`. Matplotlib uses `cl.Pyplot(figure=fig)` which is the native Chainlit pathway. Both are `display="inline"` so they appear in the message stream rather than a sidebar. `matplotlib.use("Agg")` at the top is mandatory — without it the headless server will crash.

**6. LLM Self-Correction via Error Strings** — Every tool returns a plain string. On failure it returns `"ERROR: Column 'xyz' not found. Available: [...]"`. This gets appended to history as a tool result, and the LLM sees it on the next iteration and retries with corrected arguments — no special error-handling logic needed beyond the `try/except` in `dispatch_tool`.

---

## Switching Models

The `OpenAI` client points at `https://openrouter.ai/api/v1`, so changing the model is just changing the `MODEL` env var:

```bash
MODEL=anthropic/claude-3.5-sonnet chainlit run app.py -w
MODEL=openai/gpt-4o chainlit run app.py -w
MODEL=google/gemini-2.0-flash-001 chainlit run app.py -w   # default
```

For **direct Gemini** (no OpenRouter), use `google-generativeai` with `genai.protos.FunctionDeclaration` — the tool schemas translate 1:1, only the client instantiation changes.


--app.py
"""
Chainlit + Gemini/OpenRouter: Data Visualization with Tool Calling
=================================================================
Best-practice reference implementation.

Features:
  - Session-scoped DataFrame store (upload once, query many times)
  - Tool calling via OpenRouter (works with any model: GPT-4o, Claude, Gemini, etc.)
  - Matplotlib + Plotly dual-renderer (cl.Pyplot / cl.Image)
  - Structured tool schemas that the LLM can reliably invoke
  - Error surfacing back to the LLM so it can self-correct
  - Dataset summary injected into every system prompt turn

Install:
  pip install chainlit openai pandas matplotlib plotly kaleido

Run:
  OPENROUTER_API_KEY=<key> chainlit run app.py -w
"""

import io
import json
import os
import traceback
from typing import Any

import chainlit as cl
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openai import AsyncOpenAI  # OpenRouter exposes an OpenAI-compatible API

matplotlib.use("Agg")  # headless – required inside async server

# ─────────────────────────────────────────────────────────
# 1.  CLIENT SETUP  (swap base_url for direct Gemini/OpenAI)
# ─────────────────────────────────────────────────────────

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = os.environ.get("MODEL", "google/gemini-2.0-flash-001")

# ─────────────────────────────────────────────────────────
# 2.  TOOL SCHEMAS  (what the LLM "sees")
# ─────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "plot_bar",
            "description": (
                "Render a bar chart from the loaded dataset. "
                "Use when the user wants to compare categorical values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "x_col": {
                        "type": "string",
                        "description": "Column name to use as the X-axis (categories).",
                    },
                    "y_col": {
                        "type": "string",
                        "description": "Column name to use as the Y-axis (values).",
                    },
                    "title": {
                        "type": "string",
                        "description": "Chart title shown above the plot.",
                    },
                    "color_col": {
                        "type": "string",
                        "description": "(Optional) Column name to use for color grouping.",
                    },
                },
                "required": ["x_col", "y_col", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plot_line",
            "description": (
                "Render a line chart from the loaded dataset. "
                "Best for time-series or sequential numeric data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "x_col": {"type": "string", "description": "Column for X-axis."},
                    "y_cols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "One or more column names to plot as separate lines.",
                    },
                    "title": {"type": "string", "description": "Chart title."},
                },
                "required": ["x_col", "y_cols", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plot_scatter",
            "description": "Render a scatter plot to explore correlation between two numeric columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x_col": {"type": "string"},
                    "y_col": {"type": "string"},
                    "title": {"type": "string"},
                    "color_col": {
                        "type": "string",
                        "description": "(Optional) Categorical column for color grouping.",
                    },
                    "size_col": {
                        "type": "string",
                        "description": "(Optional) Numeric column controlling marker size.",
                    },
                },
                "required": ["x_col", "y_col", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plot_histogram",
            "description": "Render a histogram for the distribution of a single numeric column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "col": {
                        "type": "string",
                        "description": "Numeric column whose distribution to visualize.",
                    },
                    "bins": {
                        "type": "integer",
                        "description": "Number of histogram bins (default 20).",
                        "default": 20,
                    },
                    "title": {"type": "string"},
                },
                "required": ["col", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plot_heatmap",
            "description": (
                "Render a correlation heatmap of all numeric columns. "
                "Useful for identifying relationships between variables."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_dataset",
            "description": (
                "Return descriptive statistics and schema information about "
                "the loaded dataset. Always call this before plotting if you "
                "are unsure which columns exist."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# ─────────────────────────────────────────────────────────
# 3.  TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────

async def _send_plotly_fig(fig: go.Figure, title: str) -> str:
    """Convert a Plotly figure to PNG bytes and send as cl.Image."""
    img_bytes = fig.to_image(format="png", width=900, height=500, scale=2)
    img_el = cl.Image(
        name=title,
        content=img_bytes,
        display="inline",
        size="large",
    )
    await cl.Message(content="", elements=[img_el]).send()
    return f"Chart '{title}' rendered successfully."


def _get_df() -> pd.DataFrame | None:
    return cl.user_session.get("dataframe")


async def tool_plot_bar(x_col: str, y_col: str, title: str, color_col: str | None = None) -> str:
    df = _get_df()
    if df is None:
        return "ERROR: No dataset loaded. Ask the user to upload a CSV file first."
    if x_col not in df.columns:
        return f"ERROR: Column '{x_col}' not found. Available: {list(df.columns)}"
    if y_col not in df.columns:
        return f"ERROR: Column '{y_col}' not found. Available: {list(df.columns)}"

    fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title,
                 template="plotly_white", barmode="group")
    fig.update_layout(title_font_size=16, margin=dict(t=60, b=40))
    return await _send_plotly_fig(fig, title)


async def tool_plot_line(x_col: str, y_cols: list[str], title: str) -> str:
    df = _get_df()
    if df is None:
        return "ERROR: No dataset loaded."
    missing = [c for c in [x_col] + y_cols if c not in df.columns]
    if missing:
        return f"ERROR: Columns not found: {missing}. Available: {list(df.columns)}"

    fig = px.line(df, x=x_col, y=y_cols, title=title, template="plotly_white",
                  markers=True)
    fig.update_layout(title_font_size=16)
    return await _send_plotly_fig(fig, title)


async def tool_plot_scatter(
    x_col: str, y_col: str, title: str,
    color_col: str | None = None, size_col: str | None = None
) -> str:
    df = _get_df()
    if df is None:
        return "ERROR: No dataset loaded."
    for col in [x_col, y_col]:
        if col not in df.columns:
            return f"ERROR: Column '{col}' not found. Available: {list(df.columns)}"

    fig = px.scatter(df, x=x_col, y=y_col, color=color_col, size=size_col,
                     title=title, template="plotly_white",
                     hover_data=df.columns.tolist())
    fig.update_layout(title_font_size=16)
    return await _send_plotly_fig(fig, title)


async def tool_plot_histogram(col: str, title: str, bins: int = 20) -> str:
    df = _get_df()
    if df is None:
        return "ERROR: No dataset loaded."
    if col not in df.columns:
        return f"ERROR: Column '{col}' not found. Available: {list(df.columns)}"

    fig = px.histogram(df, x=col, nbins=bins, title=title, template="plotly_white")
    fig.update_layout(title_font_size=16, bargap=0.05)
    return await _send_plotly_fig(fig, title)


async def tool_plot_heatmap(title: str) -> str:
    df = _get_df()
    if df is None:
        return "ERROR: No dataset loaded."

    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        return "ERROR: Need at least 2 numeric columns to compute a correlation heatmap."

    corr = numeric_df.corr()

    # Use matplotlib for the heatmap (cl.Pyplot pathway)
    fig, ax = plt.subplots(figsize=(max(6, len(corr)), max(5, len(corr) - 1)))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(corr.columns, fontsize=9)
    for i in range(len(corr)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if abs(corr.iloc[i, j]) > 0.5 else "black")
    ax.set_title(title, fontsize=14, pad=12)
    plt.tight_layout()

    # Send via cl.Pyplot (native Chainlit matplotlib support)
    pyplot_el = cl.Pyplot(figure=fig, display="inline", size="large")
    await cl.Message(content="", elements=[pyplot_el]).send()
    plt.close(fig)
    return f"Correlation heatmap '{title}' rendered successfully."


async def tool_summarize_dataset() -> str:
    df = _get_df()
    if df is None:
        return "No dataset loaded. Ask the user to upload a CSV file."

    lines = [
        f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
        f"Columns: {list(df.columns)}",
        "",
        "Dtypes:",
        df.dtypes.to_string(),
        "",
        "Describe (numeric):",
        df.describe().to_string(),
        "",
        "Null counts:",
        df.isnull().sum().to_string(),
        "",
        "First 3 rows:",
        df.head(3).to_string(),
    ]
    return "\n".join(lines)


# Dispatcher ─ maps function name → coroutine
TOOL_HANDLERS: dict[str, Any] = {
    "plot_bar": tool_plot_bar,
    "plot_line": tool_plot_line,
    "plot_scatter": tool_plot_scatter,
    "plot_histogram": tool_plot_histogram,
    "plot_heatmap": tool_plot_heatmap,
    "summarize_dataset": tool_summarize_dataset,
}


async def dispatch_tool(name: str, arguments: str) -> str:
    """Parse JSON args and call the matching tool. Catches all exceptions."""
    try:
        kwargs = json.loads(arguments) if arguments else {}
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            return f"ERROR: Unknown tool '{name}'."
        return await handler(**kwargs)
    except Exception:
        return f"ERROR executing '{name}':\n{traceback.format_exc()}"


# ─────────────────────────────────────────────────────────
# 4.  SYSTEM PROMPT BUILDER
# ─────────────────────────────────────────────────────────

def build_system_prompt() -> str:
    df: pd.DataFrame | None = cl.user_session.get("dataframe")
    dataset_context = ""

    if df is not None:
        cols_info = ", ".join(
            f"{col} ({dtype})" for col, dtype in df.dtypes.items()
        )
        dataset_context = f"""
## Loaded Dataset
- File: {cl.user_session.get("filename", "unknown")}
- Shape: {df.shape[0]} rows × {df.shape[1]} columns
- Columns: {cols_info}
- Numeric columns: {list(df.select_dtypes('number').columns)}
- Categorical columns: {list(df.select_dtypes('object').columns)}

When the user asks about data or visualizations, use the tools above.
Always call `summarize_dataset` first if uncertain about column names.
"""
    else:
        dataset_context = """
## No Dataset Loaded
Ask the user to upload a CSV file to enable charting and analysis.
"""

    return f"""You are DataViz AI, an expert data analyst assistant embedded in a Chainlit app.
You help users explore and visualize their data through natural conversation.

{dataset_context}

## Guidelines
- When a user asks for a chart or graph, **immediately call the appropriate tool** — do not ask for clarification unless the request is genuinely ambiguous.
- Prefer Plotly tools (bar, line, scatter, histogram) for interactive feel; use heatmap for correlations.
- After a chart renders, provide 2-3 concise insights about what the visualization reveals.
- If a tool returns an ERROR, apologize briefly, explain the issue, and suggest a fix.
- For data questions that don't require a chart (averages, counts), answer from your statistical knowledge of the dataset context above.
"""


# ─────────────────────────────────────────────────────────
# 5.  AGENTIC LLM LOOP  (supports multi-step tool chains)
# ─────────────────────────────────────────────────────────

async def run_agent(user_message: str) -> None:
    """
    Sends the conversation to the LLM, handles tool calls in a loop,
    and streams the final text response to the Chainlit UI.
    """
    history: list[dict] = cl.user_session.get("history", [])
    history.append({"role": "user", "content": user_message})

    async with cl.Step(name="🤖 Thinking…", show_input=False) as step:
        for _iteration in range(10):  # safety cap on tool-call loops
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    *history,
                ],
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
            )

            msg = response.choices[0].message

            # ── A: The LLM wants to call one or more tools ──────────────
            if msg.tool_calls:
                # Show which tools are being called in the step
                tool_names = [tc.function.name for tc in msg.tool_calls]
                step.output = f"Calling tools: {', '.join(tool_names)}"

                # Add assistant turn (with tool_calls) to history
                history.append(msg.model_dump(exclude_unset=True))

                # Execute every tool call (possibly in parallel in production)
                tool_results = []
                for tc in msg.tool_calls:
                    result_text = await dispatch_tool(
                        tc.function.name, tc.function.arguments
                    )
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_text,
                    })

                history.extend(tool_results)
                # Loop back → LLM will now see the tool results
                continue

            # ── B: Plain text response → stream to chat ─────────────────
            final_text = msg.content or ""
            history.append({"role": "assistant", "content": final_text})
            cl.user_session.set("history", history)

            # Stream the response token by token
            await cl.Message(content=final_text).send()
            return

    # If we exit the loop without returning, something went wrong
    await cl.Message(
        content="⚠️ Reached the maximum tool-call iterations. Please try a simpler request."
    ).send()


# ─────────────────────────────────────────────────────────
# 6.  CHAINLIT LIFECYCLE HOOKS
# ─────────────────────────────────────────────────────────

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    cl.user_session.set("dataframe", None)
    cl.user_session.set("filename", None)

    await cl.Message(
        content=(
            "👋 **Welcome to DataViz AI!**\n\n"
            "Upload a **CSV file** and I'll help you explore and visualize it.\n"
            "I can create bar charts, line charts, scatter plots, histograms, and correlation heatmaps.\n\n"
            "_Drag & drop a CSV below, or just ask me a question to get started._"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    # ── Handle CSV upload ─────────────────────────────────
    if message.elements:
        for element in message.elements:
            if hasattr(element, "path") and element.path and element.path.endswith(".csv"):
                try:
                    df = pd.read_csv(element.path)
                    cl.user_session.set("dataframe", df)
                    cl.user_session.set("filename", element.name)
                    # Reset history so the new dataset context is fresh
                    cl.user_session.set("history", [])

                    await cl.Message(
                        content=(
                            f"✅ **{element.name}** loaded — "
                            f"**{df.shape[0]:,} rows × {df.shape[1]} columns**\n\n"
                            f"Columns: `{'`, `'.join(df.columns)}`\n\n"
                            "What would you like to explore? I can plot charts or answer questions about the data."
                        )
                    ).send()
                    return
                except Exception as e:
                    await cl.Message(
                        content=f"❌ Failed to read CSV: {e}"
                    ).send()
                    return

    # ── Regular conversation / chart request ─────────────
    await run_agent(message.content)



--config.toml

[project]
# Project name shown in the header
name = "DataViz AI"
 
[features]
# Allow users to upload files (CSV)
spontaneous_file_upload = true
unsafe_allow_html = false
 
[UI]
name = "DataViz AI"
description = "Chat-driven data visualization powered by Gemini / OpenRouter"
default_theme = "dark"
 
# Show the chain-of-thought (tool call) steps
show_readme_as_default = false
 

--readme

# DataViz AI — Chainlit + OpenRouter/Gemini

Chat-driven data visualization: upload a CSV, ask in plain English, get charts.

## Quick Start

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY=sk-or-...          # or GEMINI_API_KEY (see below)
export MODEL=google/gemini-2.0-flash-001     # any OpenRouter model string
chainlit run app.py -w
```

Then open http://localhost:8000, upload `sample_data.csv`, and try:

- *"Show me a bar chart of revenue by month"*
- *"Plot profit vs expenses as a scatter"*
- *"What's the correlation between all numeric columns?"*
- *"Show the distribution of customer counts"*

---

## Architecture

```
User message
     │
     ▼
on_message()  ──── CSV upload? ──── pd.read_csv() ──► user_session["dataframe"]
     │
     ▼
run_agent()                          ◄── build_system_prompt() injects column names
     │
     ▼
OpenRouter /v1/chat/completions  (tools=TOOLS)
     │
     ├── tool_calls? ──► dispatch_tool() ──► tool_plot_bar / tool_plot_line / …
     │       │                                        │
     │       │                              Plotly → PNG → cl.Image
     │       │                              Matplotlib → cl.Pyplot
     │       │
     │       └──► append tool_result to history ──► loop back to LLM
     │
     └── text response ──► cl.Message(content=…).send()
```

### Key Design Decisions

| Concern | Solution |
|---|---|
| Dataset state | `cl.user_session` — per-user, survives message turns |
| Column discovery | System prompt always includes dtype-annotated column list |
| LLM self-correction | Tool errors return `"ERROR: …"` string; LLM retries with correct args |
| Multi-step chains | `for _iteration in range(10)` loop lets LLM call summarize → then plot |
| Matplotlib (headless) | `matplotlib.use("Agg")` before any import; use `cl.Pyplot` |
| Plotly export | `fig.to_image(format="png")` via `kaleido`; wrap in `cl.Image` |
| Streaming UX | `cl.Step` shows "Calling tools: plot_bar" while rendering |

---

## Switching to Gemini Direct (no OpenRouter)

```python
from google import generativeai as genai  # pip install google-generativeai
# Chainlit's async loop needs the async client:
import google.generativeai as genai
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
```
Tool calling with the native Gemini SDK uses `genai.protos.FunctionDeclaration`.
OpenRouter is recommended for production as it normalises the API across providers.

---

## Extending with New Chart Types

1. Add a function `async def tool_plot_pie(…) -> str` in the tool implementations section.
2. Append its JSON schema to `TOOLS`.
3. Add `"plot_pie": tool_plot_pie` to `TOOL_HANDLERS`.

That's it — no other changes needed.

---

## Environment Variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `OPENROUTER_API_KEY` | Yes | — | From openrouter.ai |
| `MODEL` | No | `google/gemini-2.0-flash-001` | Any OpenRouter model string |



