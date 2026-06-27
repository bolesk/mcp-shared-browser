import base64
import json
from typing import Dict, Any, Optional, List

from playwright.async_api import async_playwright, Playwright, Browser as PlaywrightBrowserInstance, BrowserContext, Page
from playwright_stealth import Stealth
from interfaces import Browser

class PlaywrightBrowser(Browser):
    def __init__(self, headless: bool = True):
        """
        Implements the interfaces.Browser interface using standard Playwright.

        This adapter launches a Playwright Chromium instance and manages separate 
        isolated BrowserContexts and Pages for different agent sessions.

        Args:
            headless: Whether to run the browser in headless mode. Defaults to True.
        """
        self._headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[PlaywrightBrowserInstance] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}
        self._console_logs: Dict[str, List[str]] = {}

    async def _ensure_browser(self):
        if not self._playwright:
            self._playwright = await async_playwright().start()
        if not self._browser:
            self._browser = await self._playwright.chromium.launch(headless=self._headless)

    def _setup_console_logging(self, agent_id: str, page: Page):
        self._console_logs[agent_id] = []
        page.on("console", lambda msg: self._console_logs[agent_id].append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: self._console_logs[agent_id].append(f"[error] {err.message}"))

    async def close(self):
        for agent_id in list(self._pages.keys()):
            await self.close_tab(agent_id)
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def open_tab(self, agent_id: str) -> str:
        await self._ensure_browser()
        if agent_id not in self._contexts:
            context = await self._browser.new_context()
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)
            self._contexts[agent_id] = context
            self._pages[agent_id] = page
            self._setup_console_logging(agent_id, page)
            return f"Tab opened for agent {agent_id}"
        return f"Tab already open for agent {agent_id}"

    async def close_tab(self, agent_id: str) -> str:
        page = self._pages.pop(agent_id, None)
        if page:
            await page.close()
        context = self._contexts.pop(agent_id, None)
        if context:
            await context.close()
        self._console_logs.pop(agent_id, None)
        return f"Tab closed for agent {agent_id}"

    async def navigate(self, agent_id: str, url: str) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        await page.goto(url)
        return f"Navigated to {url}"

    async def execute_js(self, agent_id: str, script: str) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        result = await page.evaluate(script)
        return str(result)

    async def get_console_logs(self, agent_id: str) -> str:
        logs = self._console_logs.get(agent_id, [])
        self._console_logs[agent_id] = []
        return "\n".join(logs)

    async def get_accessibility_tree(self, agent_id: str) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        snapshot = await page.aria_snapshot()
        return str(snapshot)


    async def interact_click(self, agent_id: str, selector_or_id: str) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        await page.click(selector_or_id)
        return f"Clicked element {selector_or_id}"

    async def interact_type(self, agent_id: str, selector_or_id: str, text: str) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        await page.fill(selector_or_id, text)
        return f"Typed text into {selector_or_id}"

    async def search_duckduckgo_serp(self, agent_id: str, query: str) -> str:
        import re
        await self._ensure_browser()
        if agent_id not in self._contexts:
            await self.open_tab(agent_id)
        page = self._pages.get(agent_id)
        if not page:
            return json.dumps([{"error": f"Error: No active tab found for agent {agent_id}"}])
        
        encoded_query = query.replace(" ", "+")
        url = f"https://duckduckgo.com/?q={encoded_query}&ia=web"
        
        try:
            await page.goto(url, wait_until="domcontentloaded")
            
            result_selector = 'article[data-testid="result"]'
            try:
                await page.wait_for_selector(result_selector, timeout=5000)
            except Exception:
                return json.dumps([])
            
            articles = await page.locator(result_selector).all()
            serp_results = []
            
            year_pattern = re.compile(r'\b(19\d\d|20[0-2]\d)\b')
            
            for article in articles:
                try:
                    link_element = article.locator('a[data-testid="result-title-a"]')
                    title = await link_element.inner_text()
                    url_href = await link_element.get_attribute("href")
                    
                    snippet_element = article.locator('[data-testid="result-snippet"]')
                    description = ""
                    if await snippet_element.count() > 0:
                        description = await snippet_element.inner_text()
                    
                    year_match = year_pattern.search(description)
                    year = year_match.group(0) if year_match else "Non specificato"
                    
                    if url_href and url_href.startswith("http"):
                        serp_results.append({
                            "title": title.strip(),
                            "url": url_href,
                            "description": description.strip(),
                            "year": year
                        })
                except Exception:
                    continue
            
            return json.dumps(serp_results)
        except Exception as e:
            return json.dumps([{"error": f"Errore durante il recupero della SERP: {str(e)}"}])


    async def take_screenshot(self, agent_id: str) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        screenshot_bytes = await page.screenshot()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        return screenshot_b64

    async def capture_screenshot_to_file(self, agent_id: str, file_path: str) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        await page.screenshot(path=file_path)
        return f"Screenshot saved to {file_path}"

    async def save_as_pdf(self, agent_id: str, file_path: Optional[str] = None) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        if file_path:
            await page.pdf(path=file_path)
            return f"PDF saved to {file_path}"
        else:
            pdf_bytes = await page.pdf()
            pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
            return pdf_b64

    async def wait_for_selector(self, agent_id: str, selector: str, timeout_ms: int = 30000) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        await page.wait_for_selector(selector, timeout=timeout_ms)
        return f"Element {selector} is now visible"

    async def wait_for_load_state(self, agent_id: str, state: str = "networkidle") -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        valid_states = ["load", "domcontentloaded", "networkidle"]
        if state not in valid_states:
            state = "networkidle"
        await page.wait_for_load_state(state=state)
        return f"Page load state reached: {state}"

    async def wait(self, agent_id: str, time_ms: int) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        await page.wait_for_timeout(time_ms)
        return f"Waited for {time_ms} ms"

    async def interact_scroll(self, agent_id: str, direction: str, amount: int) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        x, y = 0, 0
        if direction == "up":
            y = -amount
        elif direction == "down":
            y = amount
        elif direction == "left":
            x = -amount
        elif direction == "right":
            x = amount
        await page.evaluate(f"window.scrollBy({x}, {y})")
        return f"Scrolled {direction} by {amount} pixels"

    async def select_dropdown_option(self, agent_id: str, selector: str, value: str) -> str:
        page = self._pages.get(agent_id)
        if not page:
            return f"Error: No active tab found for agent {agent_id}"
        await page.select_option(selector, value=value)
        return f"Selected option {value} in {selector}"


def get_playwright_browser(headless: bool = True) -> Browser:
    """Factory function to instantiate the Playwright browser adapter."""
    return PlaywrightBrowser(headless=headless)
