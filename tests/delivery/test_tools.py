import pytest
from delivery.app import mcp, open_tab, close_tab, navigate, execute_js
from delivery.factories import get_browser

class MockContext:
    def __init__(self, client_id: str):
        self.client_id = client_id

@pytest.mark.asyncio
async def test_mcp_tools_lifecycle(monkeypatch):
    # Set BROWSER_HEADLESS=false so it runs headful inside Xvfb/macOS and avoids bot detection
    monkeypatch.setenv("BROWSER_HEADLESS", "false")

    async with mcp.settings.lifespan(mcp):
        ctx = MockContext(client_id="test-tool-agent-999")

        # 1. Open tab
        res = await open_tab(ctx)
        assert "opened" in res

        # 2. Navigate
        html_content = "<html><body><h1 id='title'>Hello Tools</h1></body></html>"
        data_url = f"data:text/html,{html_content}"
        res = await navigate(data_url, ctx)
        assert "Navigated" in res

        # 3. Execute JS
        res = await execute_js("document.getElementById('title').innerText", ctx)
        assert res == "Hello Tools"

        # 4. Close tab
        res = await close_tab(ctx)
        assert "closed" in res
