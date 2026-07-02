# mcp-shared-browser

A Model Context Protocol (MCP) server that lets **multiple AI agents share a single browser deployment**, each with its own isolated tab and session. Built with Python, Playwright, and FastMCP.

---

## The Problem with the Official Playwright MCP Server

The [official Playwright MCP server](https://github.com/microsoft/playwright-mcp) has two significant limitations:

- **Single-agent only**: it runs as a local process tied to one client. A second agent connecting is blocked. Every agent needs its own separate process, its own deployment, its own browser instance — making shared or remote deployments impractical.
- **No web search tool**: it exposes raw browser primitives (navigate, click, screenshot) but provides no built-in tool for performing a web search and getting back structured results. Agents have to navigate to a search engine, parse the HTML, and extract results themselves — which breaks under bot detection.

This makes it impractical to build multi-agent systems that share a browser, or to give agents a reliable web search capability without running into blocks.

---

## How mcp-shared-browser Works

This server runs as a **persistent HTTP service**. Any number of agents can connect to it simultaneously over Streamable HTTP or SSE. Each connecting agent is automatically routed to its own isolated browser tab — no configuration needed, no manual session management.

```
┌─────────────────────────────────────────┐
│         mcp-shared-browser (VPS)        │
│                                         │
│  Agent A ──→ Tab A  (amazon.com)        │
│  Agent B ──→ Tab B  (github.com)        │
│  Agent C ──→ Tab C  (duckduckgo.com)    │
│                                         │
│  Single Chromium process, shared        │
└─────────────────────────────────────────┘
```

Session isolation is automatic. The server extracts a unique identifier from the connection transport (`mcp-session-id` header for Streamable HTTP, `session_id` query param for SSE, or socket memory address as fallback) and maps it to a dedicated `BrowserContext` and `Page`.

---

## Bot Detection Bypass

Standard headless Playwright is blocked immediately by DuckDuckGo, Cloudflare, and most search engines via TLS/JA3 fingerprinting — even with custom user agents. The fix is running Chromium in **headful mode**, which uses the standard desktop TLS handshake.

On a server without a physical display, this server automatically launches an **Xvfb virtual framebuffer** (managed by `pyvirtualdisplay`) so the headful browser has a display to render into without consuming any visible screen. On macOS or Windows development machines, the browser window opens normally.

---

## Available Tools

| Tool | Description |
|---|---|
| `open_tab` | Opens an isolated browser tab for the current agent |
| `close_tab` | Closes the agent's tab and frees resources |
| `navigate` | Navigates to a URL |
| `execute_js` | Executes arbitrary JavaScript and returns the result |
| `get_console_logs` | Returns captured console messages and errors |
| `get_accessibility_tree` | Returns an ARIA snapshot of the page for LLM consumption |
| `interact_click` | Clicks an element by CSS selector |
| `interact_type` | Types text into an input field |
| `interact_scroll` | Scrolls the page in a direction by pixel amount |
| `select_dropdown_option` | Selects a value in a `<select>` dropdown |
| `wait_for_selector` | Waits until an element appears on the page |
| `wait_for_load_state` | Waits for a page load state (`load`, `domcontentloaded`, `networkidle`) |
| `wait` | Pauses execution for a given number of milliseconds |
| `take_screenshot` | Returns a base64-encoded screenshot of the current page |
| `capture_screenshot_to_file` | Saves a screenshot to a file path on the server |
| `save_as_pdf` | Saves the page as PDF, to file or as base64 |
| `search_duckduckgo_serp` | Searches DuckDuckGo and returns structured JSON results |

---

## Quickstart

### Local (macOS / Windows)

```bash
# Install dependencies
uv sync

# Start the server (opens a real browser window)
uv run main.py
```

The server starts on `http://127.0.0.1:8000`. The MCP endpoint is at `/mcp`.

### Docker (Linux / VPS)

A single command builds and starts the server with Xvfb running automatically:

```bash
docker compose up --build -d
```

The server will be available at `http://your-server:8000/mcp`.

> **Note**: The `init: true` setting in `docker-compose.yml` is required. It inserts a lightweight init system (tini) so that child Xvfb processes spawned by pyvirtualdisplay are correctly managed and do not become zombies.

---

## Connecting Your Agent

### Claude Desktop / Cursor (Streamable HTTP)

```json
{
  "mcpServers": {
    "shared-browser": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http"
    }
  }
}
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `FASTMCP_HOST` | `127.0.0.1` | Host to bind to (`0.0.0.0` for containers) |
| `FASTMCP_PORT` | `8000` | Port to listen on |
| `BROWSER_HEADLESS` | `false` | Set to `true` to disable bot-bypass mode |

---

## Running the Tests

The test suite is split into three groups with different requirements.

### Unit and adapter tests

```bash
uv run pytest tests/adapters/ tests/delivery/ -v
```

No external dependencies. On macOS a real Chromium window will open during adapter tests.

### Docker (adapter tests in a headless environment)

```bash
docker build -t mcp-shared-browser-test .
docker run --init --rm mcp-shared-browser-test
```

Xvfb is started automatically by the test session fixture via `pyvirtualdisplay` — no `xvfb-run` wrapper needed.

### Integration tests (LLM agent + MCP server)

```bash
uv run pytest tests/integration/ -v
```

These tests verify that a real LLM agent correctly uses the MCP browser tools end-to-end. They require two external processes, both started automatically by `tests/integration/conftest.py`:

- **llama-server** — the [llama.cpp](https://github.com/ggerganov/llama.cpp) inference server, started on port `8080` with an 80k context window
- **mcp-shared-browser** — this server, started on port `8000` in headed mode

The conftest polls both servers on their health endpoints before running any test, with a 120-second startup timeout.

**Prerequisites:**

- `llama-server` binary available in `$PATH` (install via llama.cpp)
- A compatible GGUF model downloaded to `~/models/gemma-4-E4B-it-Q8_0.gguf`

To download the model via the Hugging Face CLI:

```bash
pip install huggingface_hub
huggingface-cli download bartowski/gemma-4-E4B-it-GGUF \
  gemma-4-E4B-it-Q8_0.gguf \
  --local-dir ~/models
```

> **Note**: make sure no other process is already listening on ports `8080` or `8000` before running the integration tests, as the conftest starts its own instances.

#### Manual verification script

To test the agent interactively with servers you start yourself:

```bash
# Terminal 1
uv run main.py

# Terminal 2
llama-server --model ~/models/gemma-4-E4B-it-Q8_0.gguf -c 81920 --port 8080

# Terminal 3
uv run verify_agent_mcp.py
```

---

## Architecture

The project uses Hexagonal Architecture:

```
ports/       → Browser and VirtualDisplay abstractions (ABCs)
adapters/    → PlaywrightBrowser, XvfbDisplay, NoopDisplay implementations
delivery/    → FastMCP tool definitions, singleton lifecycle management
main.py      → HTTP server entry point (Uvicorn + Streamable HTTP / SSE)
```

The `VirtualDisplay` port separates display management from browser management. The two are started in sequence by the server lifespan (`display.start()` → `browser.init()`), but neither object knows about the other. On macOS, `NoopDisplay` is used (no-op). On Docker, `XvfbDisplay` starts a 1920×1080 virtual framebuffer before Playwright launches.

---

## Roadmap

- **Tab concurrency limit**: define a maximum number of simultaneous open tabs to cap RAM usage. Agents that request a new tab when the limit is reached are queued and wait until an existing tab is closed before proceeding.
- **Tests for remaining browser tools**: the current integration tests only cover `search_duckduckgo_serp`. Tools like `interact_click`, `interact_type`, `interact_scroll`, `select_dropdown_option`, `execute_js`, `get_accessibility_tree`, and `wait_for_selector` are not yet tested via an LLM agent. The plan is to write a small self-contained HTML page that exposes known elements and interactions, serve it from a local HTTP server started in the conftest, and have the agent navigate and interact with it to verify each tool.

---

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- For Docker: Docker with Compose v2
