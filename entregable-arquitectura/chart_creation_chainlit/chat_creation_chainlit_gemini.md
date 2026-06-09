Integrating data visualization into a Chainlit application via LLM tool calling requires a clean separation between **data management**, **tool logic**, and **UI rendering**.

### 1. Data Management & Session State

Do not store large datasets directly within the LLM's conversation history. Instead, use `cl.user_session` to persist data throughout the chat session.

* **Initialization:** Load your primary dataset in `@cl.on_chat_start` and store it in the user session.
* **Retrieval:** Inside your tool functions, retrieve the dataframe using `df = cl.user_session.get("my_data")`.

### 2. Defining Custom Plotting Tools

Define your tools as asynchronous functions. To allow the LLM to invoke them, describe the arguments clearly in the docstring or via a tool definition schema.

**Pattern for a Plotly Tool:**

```python
import plotly.express as px
import chainlit as cl

@cl.step(type="tool")
async def generate_chart(column_name: str):
    df = cl.user_session.get("my_data")
    fig = px.bar(df, x=column_name)
    
    # Send the element back to the UI
    chart_element = cl.Plotly(name="chart", figure=fig, display="inline")
    await cl.Message(content=f"Here is the chart for {column_name}", elements=[chart_element]).send()
    return "Chart generated successfully."

```

### 3. Best Practices for Tool Calling

* **Type Hinting:** Use clear type hints for arguments to help the LLM understand what parameters are required.
* **Structured Output:** Ensure the LLM tool choice is set to `auto` or `forced` if you want to guarantee a visualization is created.
* **Metadata:** When rendering, use `cl.Message` to provide context (a caption or summary) alongside the `elements=[...]` list.
* **Validation:** Before passing data to your plotting library, add basic validation (e.g., checking if the column name exists in the dataframe) to prevent the application from crashing when the LLM hallucinates an invalid column.

### 4. Comparison of Rendering Options

| Element | Library | Interactivity | Best For |
| --- | --- | --- | --- |
| `cl.Plotly` | Plotly | Yes (Zoom/Hover) | Interactive data exploration |
| `cl.Pyplot` | Matplotlib | No (Static Image) | Quick, simple summary snapshots |
| `cl.Dataframe` | Pandas/Polars | Sortable/Paginatable | Raw data verification before plotting |

### 5. Workflow Summary

1. **Context:** The LLM receives the column names or summary statistics (via system prompt) so it knows *what* can be plotted.
2. **Request:** When a user asks to "Visualize sales," the LLM selects the `generate_chart` tool.
3. **Execution:** Your tool function fetches the data from `cl.user_session`, generates the Plotly/Matplotlib figure, and returns it to the interface.
4. **Feedback:** Always include a text response with the chart to confirm the action was successful.

[How to render Matplotlib charts in Chainlit](https://www.youtube.com/watch?v=IHAZh1iXHF0)

This video provides a practical walkthrough on using `cl.Pyplot` to render charts as static images, which is useful for understanding the basic integration flow.