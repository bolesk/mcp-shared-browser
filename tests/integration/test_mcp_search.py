import asyncio
import pytest
from pydantic import BaseModel
from tests.utils import Agent, StreamableHttpMCPConfig
from tests.integration.conftest import LLAMA_BASE_URL, LLAMA_MODEL_NAME, MCP_URL


class SearchResult(BaseModel):
    title: str
    url: str


class SearchResults(BaseModel):
    results: list[SearchResult]


SEARCH_INSTRUCTIONS = """
You are a web research assistant connected to a real browser via an MCP server.

You have access to the following tools provided by the MCP server:
- open_tab: opens an isolated browser tab for your session. You MUST call this first.
- search_duckduckgo_serp: performs a DuckDuckGo web search and returns real results from the internet.
- close_tab: closes your browser tab. You MUST call this after you are done.

You MUST follow this exact sequence for every request:
1. Call open_tab to open your browser session.
2. Call search_duckduckgo_serp with the search query to fetch real results.
3. Call close_tab to release the browser session.
4. Return the results you received from the search tool formatted as a JSON object with this exact structure:
   {"results": [{"title": "...", "url": "..."}, ...]}

Return at most 3 results.
You must NEVER invent or hallucinate search results.
You must NEVER skip calling the tools.
The results you return must come exclusively from what search_duckduckgo_serp returned.
After calling close_tab, immediately return your final answer. Do not call any more tools.
"""


def make_agent() -> Agent:
    return Agent(
        model=LLAMA_MODEL_NAME,
        base_url=LLAMA_BASE_URL,
        instructions=SEARCH_INSTRUCTIONS,
        mcp_config=StreamableHttpMCPConfig(url=MCP_URL),
    )


async def search(query: str):
    agent = make_agent()
    return await agent.get_response(
        f'Search for: "{query}". Return the top 3 results.',
        output_model=SearchResults,
    )


def assert_results(response, label: str):
    response.assert_tool_called("open_tab")
    response.assert_tool_called("search_duckduckgo_serp")
    response.assert_tool_called("close_tab")
    results = response.output.results
    assert len(results) >= 1, f"[{label}] No results returned"
    assert len(results) <= 3, f"[{label}] Too many results: {len(results)}"
    for r in results:
        assert r.title, f"[{label}] Empty title"
        assert r.url.startswith("http"), f"[{label}] Invalid URL: {r.url}"


@pytest.mark.asyncio
async def test_search_milan_architecture(llama_server, mcp_server):
    response = await search("architettura liberty e razionalista a Milano")
    assert_results(response, "milan_architecture")



@pytest.mark.asyncio
async def test_search_campari(llama_server, mcp_server):
    response = await search("storia del Campari e Gaspare Campari Milano")
    assert_results(response, "campari")


@pytest.mark.asyncio
async def test_concurrent_search_multiple_agents(llama_server, mcp_server):
    """Three agents run simultaneously, each on its own isolated tab."""
    queries = [
        "navigli Milano storia canali",
        "panettone artigianale Milano storia",
        "aperitivo milanese tradizione storia",
    ]

    responses = await asyncio.gather(*[search(q) for q in queries])

    for label, response in zip(["navigli", "panettone", "aperitivo"], responses):
        assert_results(response, label)
