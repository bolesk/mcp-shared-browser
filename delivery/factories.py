import os
from typing import Optional
from ports import Browser, VirtualDisplay
from adapters import get_playwright_browser, XvfbDisplay, NoopDisplay

_browser_instance: Optional[Browser] = None
_display_instance: Optional[VirtualDisplay] = None
_ref_count: int = 0


def get_browser() -> Browser:
    global _browser_instance
    if _browser_instance is None:
        raise RuntimeError("Browser singleton is not initialized. Make sure FastMCP lifespan has run.")
    return _browser_instance


def _make_display(headless: bool) -> VirtualDisplay:
    in_docker = os.path.exists("/.dockerenv")
    if not headless and in_docker:
        return XvfbDisplay()
    return NoopDisplay()


async def initialize_browser(headless: bool = True) -> Browser:
    global _browser_instance, _display_instance, _ref_count
    if _browser_instance is None:
        _display_instance = _make_display(headless)
        await _display_instance.start()
        _browser_instance = get_playwright_browser(headless=headless)
    _ref_count += 1
    return _browser_instance


async def shutdown_browser():
    global _browser_instance, _display_instance, _ref_count
    if _ref_count > 0:
        _ref_count -= 1
    if _ref_count == 0 and _browser_instance is not None:
        await _browser_instance.close()
        _browser_instance = None
    if _ref_count == 0 and _display_instance is not None:
        await _display_instance.stop()
        _display_instance = None
