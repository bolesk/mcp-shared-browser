# MCP Multi-Session Browser Server

An Advanced Model Context Protocol (MCP) server built with **Clean Architecture / Hexagonal Architecture** in Python. It overcomes the limitations of the standard Playwright MCP server (such as lacking persistent/multiple isolated sessions and downloads handling) and is optimized for automated AI agent interactions.

---

## Key Advanced Features

*   **Process-level Session Isolation**: Dynamically routes each connecting agent to its own isolated browser tab/session automatically based on connection transport identifiers.
*   **Global Lifespan Server Initialization**: Launches and boots the browser instance globally on HTTP server startup (before any client request arrives), eliminating lazy-loading connection delays for agent clients.
*   **Active Session Reference Counter**: Tracks connected sessions so that the shared browser singleton is only terminated when the last active agent disconnects.
*   **DuckDuckGo SERP Parser**: A custom Selector-based parser with built-in stealth evasion, allowing organic search queries to resolve reliably without getting blocked by bot filters.

---

## Architecture Setup

The project uses Hexagonal Architecture to separate business logic from external drivers:
*   `domain/`: Pure business models and entities (independent of Playwright/MCP).
*   `usecase/`: Application business rules and port definitions.
*   `infrastructure/`: Adapters for external services (e.g. `PlaywrightBrowser` implementing the browser ports).
*   `interfaces/`: Interface declarations (ABC ports like `Browser`).
*   `delivery/`: Entry points, including the MCP server tool definitions and CLI.

---

## Bypassing Headless Scraper Blocks via Xvfb

### The Challenge: JA3/TLS Fingerprinting
Modern search engines and CDNs (like DuckDuckGo/Cloudflare) detect and block standard Playwright headless browsers (`headless=True`) immediately at the network handshake level, returning `HTTP/2 400 Bad Request` or CAPTCHA pages. 
This occurs because headless Chromium generates a unique **TLS fingerprint (JA3)** that matches automated bots, even when user agents and webdriver parameters are customized.

### The Solution: Xvfb & Headful Browser in Docker
To run the server headlessly in a production environment (like a VPS or Docker container) without being blocked:
1.  **Headful Browser (`headless=False`)**: We configure Playwright to run in headful mode, which uses Chrome's standard desktop TLS handshake fingerprint and passes bot checks natively.
2.  **Xvfb (X Virtual Framebuffer)**: Inside the headless Linux environment, we launch a virtual display server in RAM. Playwright runs the headful browser inside this virtual buffer, keeping it invisible and memory-only.
3.  **The Docker `--init` / `init: true` Requirement**: When running in Docker, we must run the container with the `init` system. Docker runs container commands as PID 1 by default, which does not forward signals or reap zombie processes. This causes the `xvfb-run` wrapper to hang during screen setup. The `init` system inserts a lightweight init system (`tini`), allowing child Xvfb processes to start and clean up properly.

---

## Multi-Session Agent Routing Logic

Rather than relying on client applications (which may not support it) manually passing a `client_id` parameter inside the JSON-RPC `_meta` object, the server automatically resolves a unique agent session ID (`_resolve_agent_id`) using the underlying connection properties:
1.  **Streamable HTTP (Recommended)**: Extracts the unique session identifier from the `mcp-session-id` request header.
2.  **SSE (Server-Sent Events)**: Extracts the unique session identifier from the `session_id` URL query parameter.
3.  **Memory Address Fallback**: Falls back to the memory address of the connection session object (`id(ctx.session)`). This is unique and persistent for each active client socket, making session isolation 100% robust out of the box.

---

## Testing Strategy and Execution

The test suite validates every layer of the Hexagonal Architecture and ensures that the server can run both on local development machines (with a physical UI) and remote headless servers (using virtual framebuffers).

### What the Tests Verify

The project contains three main test modules under the `tests/` directory:

1.  **Adapter Integration Tests** ([tests/adapters/test_playwright_browser.py](file:///Users/massimomontanaro/projects/python/mcp/mcp_multi_session_browser/tests/adapters/test_playwright_browser.py))
    *   **`test_playwright_browser_lifecycle`**: Instantiates the `PlaywrightBrowser` adapter directly (in headful mode) and runs all core actions: opening tabs, navigation (via mock data HTML), click and fill interactions, accessibility tree snapshot generation, screenshot-to-file captures, base64 screenshot conversion, and tab closure.
    *   **`test_playwright_browser_search_queries`**: Runs multiple queries consecutively against DuckDuckGo to verify that the selectors correctly parse results, and that the stealth configurations (TLS fingerprinting bypass) prevent blocks.

2.  **Lifespan Management Tests** ([tests/delivery/test_lifespan.py](file:///Users/massimomontanaro/projects/python/mcp/mcp_multi_session_browser/tests/delivery/test_lifespan.py))
    *   **`test_mcp_lifespan`**: Verifies that Uvicorn/FastMCP lifespan events correctly control the browser singleton. It asserts that the browser singleton cannot be accessed before server startup, is successfully initialized and shared during active server runtime, and is safely closed and disposed of upon server shutdown.

3.  **MCP Tool Integration Tests** ([tests/delivery/test_tools.py](file:///Users/massimomontanaro/projects/python/mcp/mcp_multi_session_browser/tests/delivery/test_tools.py))
    *   **`test_mcp_tools_lifecycle`**: Simulates an actual client connection using a mocked `Context` object with unique agent client IDs. It verifies that the FastMCP tool wrappers (`open_tab`, `navigate`, `execute_js`, `close_tab`) correctly intercept context routing and invoke the underlying browser ports.

---

### How to Run the Tests

#### Local Execution (macOS / Windows Desktop)
On local environments with a physical display, you can run the entire test suite directly. The tests will physically launch headful browser windows on your screen so you can observe the actions:

```bash
# Sync dependencies
uv sync

# Run all tests
uv run pytest -v

# Run only a specific test file (e.g. adapter tests)
uv run pytest tests/adapters/test_playwright_browser.py -v
```

#### Headless Linux Execution (Docker + Xvfb)
To test the virtual framebuffer implementation in an environment matching your production server (e.g. Linux container without a physical display):

1.  **Build the Docker Image**:
    ```bash
    docker build -t mcp-browser-test .
    ```
2.  **Run the Container**:
    *   *Note*: The `--init` flag is required so that process signals and child Xvfb processes are correctly managed.
    ```bash
    docker run --init --rm mcp-browser-test
    ```

---

## Running the Server (Streamable HTTP / SSE)

The server defaults to **Streamable HTTP** transport (the modern bidirectional standard for web-hosted MCP servers), but can be configured to use **SSE** via environment variables.

### Configuration Environment Variables
All FastMCP settings can be configured using environment variables prefixed with `FASTMCP_`:
*   `FASTMCP_HOST`: Host to bind to (e.g. `0.0.0.0` for container networks, default `127.0.0.1`).
*   `FASTMCP_PORT`: Port to listen on (default `8000`).
*   `MCP_TRANSPORT`: Override transport layer (`streamable-http` or `sse`, default `streamable-http`).
*   `BROWSER_HEADLESS`: Enable/disable headless mode (default `false` to enable headful bot block bypass via Xvfb).

### Local Server Launch
To start the HTTP server locally:
```bash
uv run main.py
```
This runs the server on `http://127.0.0.1:8000`. The Streamable HTTP endpoint will be at `http://127.0.0.1:8000/mcp`.

### Docker Production Execution (with Xvfb)

#### Option A: Docker Compose (Recommended)
A preconfigured [docker-compose.yml](file:///Users/massimomontanaro/projects/python/mcp/mcp_multi_session_browser/docker-compose.yml) is included to simplify deployment, mapping the required virtual framebuffers and lifecycle signals automatically:

```bash
# Build and start the container in background
docker compose up --build -d

# Monitor server logs
docker compose logs -f

# Shut down the container
docker compose down
```

#### Option B: Standalone Docker Command
Alternatively, build and run the container manually:

```bash
# Build the server image
docker build -t mcp-browser-server .

# Run exposing port 8000 using xvfb-run
docker run --init -p 8000:8000 \
  -e FASTMCP_HOST=0.0.0.0 \
  -e FASTMCP_PORT=8000 \
  --rm mcp-browser-server xvfb-run --server-args="-screen 0 1920x1080x24" uv run main.py
```
The server will now be listening on `http://localhost:8000/mcp`.

---

## Client Configurations (Claude Desktop / Cursor / Agent SDKs)

To connect your MCP client (such as Claude Desktop, Cursor, or custom SDKs) to this running HTTP server, add the server entry to your configuration JSON file (e.g. `claude_desktop_config.json` or `mcp_config.json`):

### 1. Streamable HTTP Configuration (Recommended)
Use this configuration for modern clients supporting Streamable HTTP:
```json
{
  "mcpServers": {
    "multi-session-browser": {
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http"
    }
  }
}
```

### 2. SSE Configuration (Legacy Fallback)
If your client only supports SSE, ensure you start the server with the environment variable `MCP_TRANSPORT=sse` and use this configuration:
```json
{
  "mcpServers": {
    "multi-session-browser": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```
