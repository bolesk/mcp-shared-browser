import pytest
from delivery.app import mcp
from delivery.factories import get_browser

@pytest.mark.asyncio
async def test_mcp_lifespan(monkeypatch):
    # Set headless=False so it works natively on macOS/Xvfb without getting blocked
    monkeypatch.setenv("BROWSER_HEADLESS", "false")

    # 1. Assert get_browser raises error prior to initialization
    with pytest.raises(RuntimeError):
        get_browser()

    # 2. Enter FastMCP lifespan context manager
    async with mcp.settings.lifespan(mcp):
        # 3. Assert browser singleton is initialized and accessible
        browser = get_browser()
        assert browser is not None

        # 4. Assert browser performs standard actions
        res = await browser.open_tab("lifespan-test-agent")
        assert "opened" in res or "already open" in res
        
        await browser.close_tab("lifespan-test-agent")

    # 5. Assert get_browser raises error after shutdown
    with pytest.raises(RuntimeError):
        get_browser()
