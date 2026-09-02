import base64

import pytest
import os
import tempfile
from adapters import get_playwright_browser

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



@pytest.mark.asyncio
async def test_interact_type():
    browser = get_playwright_browser(headless=False)
    agent_id = "test-agent-type"

    await browser.open_tab(agent_id)
    html_content = "<html><body><input id='field' type='text'></body></html>"
    await browser.navigate(agent_id, f"data:text/html,{html_content}")

    res = await browser.interact_type(agent_id, "#field", "hello world")
    assert "Typed text into" in res

    value = await browser.execute_js(agent_id, "document.getElementById('field').value")
    assert value == "hello world"

    await browser.close_tab(agent_id)
    await browser.close()


@pytest.mark.asyncio
async def test_select_dropdown_option():
    browser = get_playwright_browser(headless=False)
    agent_id = "test-agent-dropdown"

    await browser.open_tab(agent_id)
    html_content = (
        "<html><body><select id='dropdown'>"
        "<option value='a'>A</option><option value='b'>B</option>"
        "</select></body></html>"
    )
    await browser.navigate(agent_id, f"data:text/html,{html_content}")

    res = await browser.select_dropdown_option(agent_id, "#dropdown", "b")
    assert "Selected option b" in res

    value = await browser.execute_js(agent_id, "document.getElementById('dropdown').value")
    assert value == "b"

    await browser.close_tab(agent_id)
    await browser.close()


@pytest.mark.asyncio
async def test_interact_scroll():
    browser = get_playwright_browser(headless=False)
    agent_id = "test-agent-scroll"

    await browser.open_tab(agent_id)
    html_content = "<html><body style='height:3000px'><h1>top</h1></body></html>"
    await browser.navigate(agent_id, f"data:text/html,{html_content}")

    res = await browser.interact_scroll(agent_id, "down", 500)
    assert "Scrolled down by 500" in res

    scroll_y = await browser.execute_js(agent_id, "window.scrollY")
    assert int(scroll_y) == 500

    await browser.close_tab(agent_id)
    await browser.close()


@pytest.mark.asyncio
async def test_wait_for_selector():
    browser = get_playwright_browser(headless=False)
    agent_id = "test-agent-wait-selector"

    await browser.open_tab(agent_id)
    html_content = (
        "<html><body><script>"
        "setTimeout(() => {"
        "  const el = document.createElement('div');"
        "  el.id = 'late'; el.textContent = 'arrived';"
        "  document.body.appendChild(el);"
        "}, 300);"
        "</script></body></html>"
    )
    await browser.navigate(agent_id, f"data:text/html,{html_content}")

    res = await browser.wait_for_selector(agent_id, "#late", timeout_ms=3000)
    assert "#late" in res and "visible" in res

    text = await browser.execute_js(agent_id, "document.getElementById('late').textContent")
    assert text == "arrived"

    await browser.close_tab(agent_id)
    await browser.close()


@pytest.mark.asyncio
async def test_wait_for_load_state():
    browser = get_playwright_browser(headless=False)
    agent_id = "test-agent-wait-load-state"

    await browser.open_tab(agent_id)
    await browser.navigate(agent_id, "data:text/html,<h1>loaded</h1>")

    res = await browser.wait_for_load_state(agent_id, "networkidle")
    assert res == "Page load state reached: networkidle"

    await browser.close_tab(agent_id)
    await browser.close()


@pytest.mark.asyncio
async def test_save_as_pdf():
    browser = get_playwright_browser(headless=False)
    agent_id = "test-agent-pdf"

    await browser.open_tab(agent_id)
    await browser.navigate(agent_id, "data:text/html,<h1>pdf content</h1>")

    # Variante base64 (nessun file_path)
    b64_pdf = await browser.save_as_pdf(agent_id)
    pdf_bytes = base64.b64decode(b64_pdf)
    assert pdf_bytes.startswith(b"%PDF")

    # Variante su file
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "output.pdf")
        res = await browser.save_as_pdf(agent_id, file_path)
        assert "PDF saved to" in res
        assert os.path.exists(file_path)
        with open(file_path, "rb") as f:
            assert f.read(4) == b"%PDF"

    await browser.close_tab(agent_id)
    await browser.close()


@pytest.mark.asyncio
async def test_multi_session_isolation():
    """Verifica la feature differenziante del progetto: due agent
    connessi in parallelo devono avere tab isolate, senza cross-talk."""
    browser = get_playwright_browser(headless=False)
    agent_a = "test-agent-isolation-a"
    agent_b = "test-agent-isolation-b"

    await browser.open_tab(agent_a)
    await browser.open_tab(agent_b)

    await browser.navigate(
        agent_a, "data:text/html,<body style='height:3000px'><h1 id='marker'>Page A</h1></body>"
    )
    await browser.navigate(
        agent_b, "data:text/html,<body style='height:3000px'><h1 id='marker'>Page B</h1></body>"
    )

    text_a = await browser.execute_js(agent_a, "document.getElementById('marker').textContent")
    text_b = await browser.execute_js(agent_b, "document.getElementById('marker').textContent")

    assert text_a == "Page A"
    assert text_b == "Page B"

    # Un'azione su un agent non deve toccare la tab dell'altro.
    await browser.interact_scroll(agent_a, "down", 200)
    scroll_a = await browser.execute_js(agent_a, "window.scrollY")
    scroll_b = await browser.execute_js(agent_b, "window.scrollY")
    assert int(scroll_a) == 200
    assert int(scroll_b) == 0

    await browser.close_tab(agent_a)
    # La tab di B deve restare viva e funzionante dopo la chiusura di A.
    text_b_after = await browser.execute_js(agent_b, "document.getElementById('marker').textContent")
    assert text_b_after == "Page B"

    await browser.close_tab(agent_b)
    await browser.close()
