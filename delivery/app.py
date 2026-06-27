import os
from contextlib import asynccontextmanager
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context
from delivery.factories import initialize_browser, shutdown_browser, get_browser

@asynccontextmanager
async def mcp_lifespan(server: FastMCP):
    # Detect if running inside Docker
    in_docker = os.path.exists("/.dockerenv")
    
    # Configure headless mode: default to False (headed) to bypass bot detection.
    # On local machines, this opens a physical browser window.
    # In Docker/headless environments, this works inside the Xvfb virtual display.
    headless_str = os.getenv("BROWSER_HEADLESS")
    if headless_str is not None:
        headless = headless_str.lower() not in ("false", "0", "no")
    else:
        headless = False
        
    print(f"Starting shared browser (headless={headless}, docker={in_docker})...")
    await initialize_browser(headless=headless)
    yield
    print("Stopping shared browser...")
    await shutdown_browser()

mcp = FastMCP("mcp-multi-session-browser", lifespan=mcp_lifespan)


def _resolve_agent_id(ctx: Context) -> str:
    """Resolves a unique, persistent agent session identifier from the connection context."""
    # 1. Respect explicitly sent client IDs from MCP JSON-RPC _meta if present
    if ctx.client_id:
        return ctx.client_id
        
    # 2. Try to extract HTTP/SSE transport-level session IDs
    request = getattr(ctx.request_context, "request", None)
    if request is not None:
        # Streamable HTTP session ID header
        mcp_session_id = request.headers.get("mcp-session-id")
        if mcp_session_id:
            return f"stream-{mcp_session_id}"
        # SSE session ID query parameter
        sse_session_id = request.query_params.get("session_id")
        if sse_session_id:
            return f"sse-{sse_session_id}"
            
    # 3. Fallback to the memory address of the connection session (stable per connection)
    if ctx.session is not None:
        return f"conn-{id(ctx.session)}"
        
    return "default"


@mcp.tool()
async def open_tab(ctx: Context) -> str:
    """Opens a new tab/session associated with the current agent."""
    browser = get_browser()
    return await browser.open_tab(_resolve_agent_id(ctx))


@mcp.tool()
async def close_tab(ctx: Context) -> str:
    """Closes the tab/session associated with the current agent to free memory."""
    browser = get_browser()
    return await browser.close_tab(_resolve_agent_id(ctx))


@mcp.tool()
async def navigate(url: str, ctx: Context) -> str:
    """Navigates the current agent's tab to a specified URL."""
    browser = get_browser()
    return await browser.navigate(_resolve_agent_id(ctx), url)


@mcp.tool()
async def execute_js(script: str, ctx: Context) -> str:
    """Executes arbitrary JavaScript code on the current agent's active page."""
    browser = get_browser()
    return await browser.execute_js(_resolve_agent_id(ctx), script)


@mcp.tool()
async def get_console_logs(ctx: Context) -> str:
    """Retrieves all captured console messages, errors, and logs for the current agent's tab."""
    browser = get_browser()
    return await browser.get_console_logs(_resolve_agent_id(ctx))


@mcp.tool()
async def get_accessibility_tree(ctx: Context) -> str:
    """Generates a simplified accessibility tree (ARIA snapshot) of the current page for LLM consumption."""
    browser = get_browser()
    return await browser.get_accessibility_tree(_resolve_agent_id(ctx))


@mcp.tool()
async def interact_click(selector: str, ctx: Context) -> str:
    """Clicks an element matching the specified selector on the page."""
    browser = get_browser()
    return await browser.interact_click(_resolve_agent_id(ctx), selector)


@mcp.tool()
async def interact_type(selector: str, text: str, ctx: Context) -> str:
    """Fills/types text into an input field matching the specified selector."""
    browser = get_browser()
    return await browser.interact_type(_resolve_agent_id(ctx), selector, text)


@mcp.tool()
async def search_duckduckgo_serp(query: str, ctx: Context) -> str:
    """Performs a search on DuckDuckGo and returns a JSON list of organic results (Title, URL, Description, Year)."""
    browser = get_browser()
    return await browser.search_duckduckgo_serp(_resolve_agent_id(ctx), query)


@mcp.tool()
async def take_screenshot(ctx: Context) -> str:
    """Captures a screenshot of the current page and returns its base64 string representation."""
    browser = get_browser()
    return await browser.take_screenshot(_resolve_agent_id(ctx))


@mcp.tool()
async def capture_screenshot_to_file(file_path: str, ctx: Context) -> str:
    """Captures a screenshot of the current page and saves it to a specified file path."""
    browser = get_browser()
    return await browser.capture_screenshot_to_file(_resolve_agent_id(ctx), file_path)


@mcp.tool()
async def save_as_pdf(file_path: Optional[str] = None, ctx: Context = None) -> str:
    """Saves the current page layout as a PDF. Returns base64 representation if file_path is not specified."""
    browser = get_browser()
    return await browser.save_as_pdf(_resolve_agent_id(ctx), file_path)


@mcp.tool()
async def wait_for_selector(selector: str, timeout_ms: int = 30000, ctx: Context = None) -> str:
    """Waits until an element matching the selector appears on the page or the timeout is exceeded."""
    browser = get_browser()
    return await browser.wait_for_selector(_resolve_agent_id(ctx), selector, timeout_ms)


@mcp.tool()
async def wait_for_load_state(state: str = "networkidle", ctx: Context = None) -> str:
    """Waits for a specific page load state (e.g. load, domcontentloaded, networkidle)."""
    browser = get_browser()
    return await browser.wait_for_load_state(_resolve_agent_id(ctx), state)


@mcp.tool()
async def wait(time_ms: int, ctx: Context) -> str:
    """Pauses browser execution/waiting for a specified duration in milliseconds."""
    browser = get_browser()
    return await browser.wait(_resolve_agent_id(ctx), time_ms)


@mcp.tool()
async def interact_scroll(direction: str, amount: int, ctx: Context) -> str:
    """Scrolls the page in a given direction (up, down, left, right) by a specific pixel amount."""
    browser = get_browser()
    return await browser.interact_scroll(_resolve_agent_id(ctx), direction, amount)


@mcp.tool()
async def select_dropdown_option(selector: str, value: str, ctx: Context) -> str:
    """Selects an option in a dropdown menu matching the specified selector."""
    browser = get_browser()
    return await browser.select_dropdown_option(_resolve_agent_id(ctx), selector, value)
