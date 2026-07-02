"""
Verification script for agent + MCP server integration.

Before running this script, start the MCP server manually:
    uv run main.py

Then run this script:
    uv run verify_agent_mcp.py
"""
import asyncio
from tests.utils import Agent, StreamableHttpMCPConfig

MCP_URL = "http://localhost:8000/mcp"
LLAMA_BASE_URL = "http://localhost:8080/v1"
LLAMA_MODEL = "gemma-4-E4B-it-Q8_0"

INSTRUCTIONS = """
You are a web research assistant connected to a real browser via an MCP server.

You have access to the following tools provided by the MCP server:
- open_tab: opens an isolated browser tab for your session. You MUST call this first.
- search_duckduckgo_serp: performs a DuckDuckGo web search and returns real results from the internet.
- close_tab: closes your browser tab. You MUST call this after you are done.

You MUST follow this exact sequence for every request:
1. Call open_tab to open your browser session.
2. Call search_duckduckgo_serp with the search query to fetch real results.
3. Call close_tab to release the browser session.
4. Return the results you received from the search tool.

You must NEVER invent or hallucinate search results.
You must NEVER skip calling the tools.
The results you return must come exclusively from what search_duckduckgo_serp returned.
"""


async def main():
    agent = Agent(
        model=LLAMA_MODEL,
        base_url=LLAMA_BASE_URL,
        instructions=INSTRUCTIONS,
        mcp_config=StreamableHttpMCPConfig(url=MCP_URL),
    )

    print("Running agent with MCP server...")
    print(f"  LLM:        {LLAMA_BASE_URL}")
    print(f"  MCP server: {MCP_URL}")
    print()

    response = await agent.get_response(
        "Search for: storia del Campari e Gaspare Campari Milano"
    )

    print("=== Tools called ===")
    if response.tools_called:
        for tool in response.tools_called:
            print(f"  ✓ {tool}")
    else:
        print("  ✗ No tools were called — the model hallucinated the response!")

    print()
    print("=== Output ===")
    print(response.output)

    print()
    if "search_duckduckgo_serp" in response.tools_called:
        print("✓ PASS: agent correctly used the MCP search tool")
    else:
        print("✗ FAIL: agent did not use the MCP search tool")


if __name__ == "__main__":
    asyncio.run(main())
