import os
from typing import Optional
from interfaces import Browser
from infrastructure import get_playwright_browser

_browser_instance: Optional[Browser] = None
_ref_count: int = 0

def get_browser() -> Browser:
    """Returns the shared Browser singleton. Raises RuntimeError if not initialized."""
    global _browser_instance
    if _browser_instance is None:
        raise RuntimeError("Browser singleton is not initialized. Make sure FastMCP lifespan has run.")
    return _browser_instance

async def initialize_browser(headless: bool = True) -> Browser:
    """Initializes the shared Browser singleton instance, tracking active session references."""
    global _browser_instance, _ref_count
    if _browser_instance is None:
        _browser_instance = get_playwright_browser(headless=headless)
    _ref_count += 1
    return _browser_instance

async def shutdown_browser():
    """Decrements active session references and shuts down the browser if no references remain."""
    global _browser_instance, _ref_count
    if _ref_count > 0:
        _ref_count -= 1
    if _ref_count == 0 and _browser_instance is not None:
        await _browser_instance.close()
        _browser_instance = None
