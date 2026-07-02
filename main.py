import os
import anyio
import uvicorn
from contextlib import asynccontextmanager
from delivery.app import mcp

@asynccontextmanager
async def wrapped_lifespan(app_inst, original_lifespan):
    if original_lifespan:
        async with original_lifespan(app_inst) as ctx:
            yield ctx
    else:
        yield

def run_http_server(transport: str):
    if transport == "streamable-http":
        app = mcp.streamable_http_app()
    elif transport == "sse":
        app = mcp.sse_app()
    else:
        raise ValueError(f"Unknown HTTP transport: {transport}")

    # Wrap the Starlette router lifespan
    original_lifespan = app.router.lifespan_context

    def custom_lifespan(app_inst):
        return wrapped_lifespan(app_inst, original_lifespan)

    app.router.lifespan_context = custom_lifespan

    host = os.getenv("FASTMCP_HOST", mcp.settings.host)
    port = int(os.getenv("FASTMCP_PORT", mcp.settings.port))
    log_level = mcp.settings.log_level.lower()

    config = uvicorn.Config(app, host=host, port=port, log_level=log_level)
    server = uvicorn.Server(config)
    
    print(f"Starting MCP server with transport: {transport} on http://{host}:{port}", flush=True)
    anyio.run(server.serve)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    if transport in ("sse", "streamable-http"):
        run_http_server(transport)
    else:
        print(f"Starting MCP server with transport: {transport}", flush=True)
        mcp.run(transport=transport)
