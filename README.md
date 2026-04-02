# FigureOut - a lightweight and resilient multi-LLM orchestrator

[![PyPI version](https://img.shields.io/pypi/v/figureout.svg)](https://pypi.org/project/figureout/)
[![License](https://img.shields.io/pypi/l/figureout.svg)](https://pypi.org/project/figureout/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/figureout?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=ORANGE&left_text=downloads)](https://pepy.tech/projects/figureout)

FigureOut is a lightweight, modular orchestrator for developers who want to build LLM workflows without the framework bloat. Unlike heavy frameworks that hide logic behind abstractions, FigureOut keeps your code clean, predictable, and easy to debug. Perfect for prototyping and production-grade apps where you need full control.

The package classifies incoming queries and dispatches them to the appropriate role, returning a structured JSON response.

## Demo

This demo shows the FigureOut package integration into a Concert event's Seat Selection page. The user enters queries like "Find me cheap seats", "Find me premium seats", and so on. The query is sent to the package and it sends the query to LLM. LLM will process the query and orchestrate MCP tool calling accordingly.

https://github.com/user-attachments/assets/b638644f-d9e7-404d-8978-1cd9ffebb308

## Installation

Install the base package plus the extra for your LLM provider:

```bash
pip install figureout[openai]   # OpenAI
pip install figureout[gemini]   # Google Gemini
pip install figureout[claude]   # Anthropic Claude
pip install figureout[meta]     # Meta (Llama)
pip install figureout[mistral]  # Mistral
pip install figureout[groq]     # Groq
pip install figureout[all]      # All providers
```

## Supported LLM Providers

| Provider | Enum | API Key Env Var | Install Extra |
|---|---|---|---|
| OpenAI | `LLM.OPENAI` | `OPENAI_API_KEY` | `pip install figureout[openai]` |
| Google Gemini | `LLM.GEMINI` | `GEMINI_API_KEY` | `pip install figureout[gemini]` |
| Anthropic Claude | `LLM.CLAUDE` | `ANTHROPIC_API_KEY` | `pip install figureout[claude]` |
| Meta (Llama) | `LLM.META` | `META_API_KEY` | `pip install figureout[meta]` |
| Mistral | `LLM.MISTRAL` | `MISTRAL_API_KEY` | `pip install figureout[mistral]` |
| Groq | `LLM.GROQ` | `GROQ_API_KEY` | `pip install figureout[groq]` |

Only install the extra for the provider(s) you intend to use.

## Quick Start

```python
import asyncio
from figureout import FigureOut, RoleDefinition

concierge = FigureOut(
    llm="openai",
    llm_version="gpt-4o",
    roles={
        "product_search": RoleDefinition(
            prompt="You are a product search specialist. Help users find products.",
            schema='{"results": [{"id": int, "name": str, "price": float}], "summary": str}',
            guideline="queries about finding or searching for products",
        ),
        "off_topic": RoleDefinition(
            prompt="Politely decline and explain you can only help with product searches.",
            schema='{"message": str}',
            guideline="anything unrelated to products",
        ),
    },
)

result = asyncio.run(concierge.run("Find me a blue running shoe under $100"))
print(result)
# {"results": [...], "summary": "..."}
```

## API

### `FigureOut` Constructor

```python
FigureOut(
    llm: str | LLM,
    llm_version: str,
    roles: dict[str, RoleDefinition],
    lite_llm_version: str | None = None,
    verbose: bool = False,
    max_roles: int = 1,
    max_output_tokens: int = 16384,
    max_retries: int = 2,
    max_tool_rounds: int = 3,
    interpret_tool_response: bool | None = None,
    cache_enabled: bool = True,
    cache_size: int = 128,
    inject_date: bool = True,
    api_key: str | None = None,
    mcp_server=None,
)
```

All constructor params can also be set via environment variables:

| Param | Env Var |
|---|---|
| `llm` | `FIGUREOUT_LLM` |
| `llm_version` | `FIGUREOUT_LLM_VERSION` |
| `lite_llm_version` | `FIGUREOUT_LITE_LLM_VERSION` |
| `verbose` | `FIGUREOUT_VERBOSE` |
| `max_roles` | `FIGUREOUT_MAX_ROLES` |
| `max_output_tokens` | `FIGUREOUT_MAX_OUTPUT_TOKENS` |
| `max_retries` | `FIGUREOUT_MAX_RETRIES` |
| `max_tool_rounds` | `FIGUREOUT_MAX_TOOL_ROUNDS` |
| `interpret_tool_response` | `FIGUREOUT_INTERPRET_TOOL_RESPONSE` |
| `cache_enabled` | `FIGUREOUT_CACHE_ENABLED` |
| `cache_size` | `FIGUREOUT_CACHE_SIZE` |
| `inject_date` | `FIGUREOUT_INJECT_DATE` |

### `RoleDefinition`

```python
RoleDefinition(
    prompt: str,      # System prompt for this role
    schema: str,      # JSON schema string defining the output shape
    guideline: str,   # Short description used by the classifier to select this role
)
```

### `run()` Method

```python
await concierge.run(
    user_query: str,
    role: str | None = None,         # Skip classification, use this role directly
    context: str | None = None,      # Prepended to user_query as additional context
    output_schema: str | None = None # Override the role's default schema
)
```

Returns a dict matching the role's output schema.

## Multi-Role Queries

Set `max_roles > 1` to allow multiple roles to handle a single query in parallel:

```python
concierge = FigureOut(llm="openai", llm_version="gpt-4o", roles=ROLES, max_roles=3)
result = await concierge.run("Find concerts and sports events this weekend")
# {"concert_discovery": {...}, "sports_discovery": {...}}
```

When a single role is selected, the result is returned directly (not wrapped in a role-keyed dict).

## `off_topic` Role

Define an `"off_topic"` role to control fallback behavior. The classifier never selects it directly — it is used automatically when no other role matches:

```python
"off_topic": RoleDefinition(
    prompt="Politely decline.",
    schema='{"message": str}',
    guideline="anything unrelated",
)
```

## Tool Use (FastMCP)

Pass a FastMCP server to enable tool calling:

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def search_products(query: str) -> list:
    ...

concierge = FigureOut(llm="gemini", llm_version="gemini-2.0-flash", roles=ROLES, mcp_server=mcp)
```

### `interpret_tool_response`

Controls how tool results are handled after tool execution:

| Value | Behavior |
|---|---|
| `None` (default) | Normal loop — LLM responds naturally after tool calls |
| `True` | Bridge messages appended after tool calls + forced JSON mode round; ensures nested fields are populated |
| `False` | Return raw tool output without sending back to the LLM |

Use `interpret_tool_response=True` for roles that return complex nested JSON structures.

## Verbose Mode

With `verbose=True`, the response is wrapped under a `"response"` key and a `"debug"` key is added with token usage and timing information:

```python
concierge = FigureOut(..., verbose=True)
result = await concierge.run("Find flights to Tokyo")
# {"response": {"flights": [...]}, "debug": {"input_tokens": 512, "output_tokens": 256, ...}}
```

## Examples

The `examples/` directory contains complete domain-specific backends with React+Vite frontends:

| Example | Domain |
|---|---|
| `event-sports-booking/` | Sports event discovery and booking |
| `flight-booking/` | Flight search and booking |
| `restaurant-reservation/` | Restaurant discovery and reservations |
| `things-to-do/` | Activity and places discovery |
| `customer-support-chat/` | FAQ-based customer support chat |

To run an example:

```bash
cd examples/<example-name>/mcp-server
python app.py
```

## Streamlit Demo

Install demo dependencies first (from the repo root):

```bash
pip install -r demo/requirements.txt
```

### Startup Advisor (`demo/app.py`)

An interactive chatbot that routes questions to specialist roles (market research, technical advice, fundraising).

```bash
streamlit run demo/app.py
```

### Events & Sports Booking (`demo/app_mcp.py`)

A conversational booking assistant backed by live MCP tool calls — search events, check seat availability, and explore fees.

```bash
streamlit run demo/app_mcp.py
```

Use the sidebar to choose an LLM provider, paste your API key, and optionally set your location and date range. Toggle **Show debug info** to see which MCP tools were called and token usage per query.

### Utility: Postpone Event Dates (`demo/postpone_dates.py`)

Shifts all past dates in `events.json` forward so every event is in the future from today. Run this whenever the demo data goes stale:

```bash
python demo/postpone_dates.py

# Add a buffer of N days beyond today
python demo/postpone_dates.py --offset-days 7

# Point at a custom events.json
python demo/postpone_dates.py --data-path path/to/events.json
```

## Development

```bash
pip install -e ".[dev]"
pytest
pytest tests/test_figureout.py::test_name  # Run a single test
```
