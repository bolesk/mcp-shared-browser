# Infrastructure layer containing adapters for external systems (e.g. database, browser, HTTP clients).

from .playwright_browser import PlaywrightBrowser, get_playwright_browser

__all__ = ["PlaywrightBrowser", "get_playwright_browser"]

