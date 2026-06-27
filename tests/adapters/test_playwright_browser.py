import pytest
import os
import tempfile
from infrastructure import get_playwright_browser

@pytest.mark.asyncio
async def test_playwright_browser_lifecycle():
    browser = get_playwright_browser(headless=False)
    agent_id = "test-agent-123"

    # 1. Open tab
    res = await browser.open_tab(agent_id)
    assert "Tab opened" in res

    # 2. Navigate using a data URL containing simple HTML
    html_content = "<html><body><h1 id='title'>Hello World</h1><button id='btn' onclick='console.log(\"button_clicked\")'>Click me</button></body></html>"
    data_url = f"data:text/html,{html_content}"
    res = await browser.navigate(agent_id, data_url)
    assert "Navigated" in res

    # 3. Test JS execution
    title_text = await browser.execute_js(agent_id, "document.getElementById('title').innerText")
    assert title_text == "Hello World"

    # 4. Test accessibility tree snapshot
    tree = await browser.get_accessibility_tree(agent_id)
    assert "Hello World" in tree

    # 5. Test interaction: click & console logs
    await browser.interact_click(agent_id, "#btn")
    await browser.wait(agent_id, 100)  # brief wait for callback to execute
    logs = await browser.get_console_logs(agent_id)
    assert "button_clicked" in logs

    # 6. Test screenshot to file
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "screenshot.png")
        screenshot_res = await browser.capture_screenshot_to_file(agent_id, file_path)
        assert "saved" in screenshot_res
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0

    # 7. Test base64 screenshot
    b64_screenshot = await browser.take_screenshot(agent_id)
    assert len(b64_screenshot) > 0

    # 8. Test search_duckduckgo_serp
    import json
    serp_json = await browser.search_duckduckgo_serp(agent_id, "python programming")
    serp_data = json.loads(serp_json)
    assert isinstance(serp_data, list)
    assert len(serp_data) > 0
    first = serp_data[0]
    assert "error" not in first
    assert "title" in first
    assert "url" in first
    assert "description" in first
    assert "year" in first


    # 9. Close tab
    close_res = await browser.close_tab(agent_id)
    assert "closed" in close_res

    # Cleanup browser resources
    await browser.close()


@pytest.mark.asyncio
async def test_playwright_browser_search_queries():
    import json
    import asyncio
    browser = get_playwright_browser(headless=False)
    agent_id = "test-search-agent"

    await browser.open_tab(agent_id)

    queries = [
        "clean architecture python",
        "playwright python documentation",
        "model context protocol mcp"
    ]

    for i, query in enumerate(queries):
        if i > 0:
            # Sleep 1 second between requests to be polite to DuckDuckGo
            await asyncio.sleep(1.0)
            
        serp_json = await browser.search_duckduckgo_serp(agent_id, query)
        results = json.loads(serp_json)

        if len(results) == 0:
            html = await browser.execute_js(agent_id, "document.body.innerHTML")
            print(f"\n--- FAILED QUERY HTML: {query} ---\n{html[:1000]}\n--- END FAILED QUERY HTML ---")
            await browser.capture_screenshot_to_file(agent_id, "failed_search.png")
            
        assert isinstance(results, list), f"Expected list for query '{query}', got {type(results)}"
        assert len(results) > 0, f"No search results returned for query: '{query}'"

        
        first_result = results[0]
        assert "error" not in first_result, f"Search returned error for query '{query}': {first_result.get('error')}"
        assert "title" in first_result and first_result["title"], f"Missing title in result for query '{query}'"
        assert "url" in first_result and first_result["url"], f"Missing url in result for query '{query}'"

    await browser.close_tab(agent_id)
    await browser.close()

