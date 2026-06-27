from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class Browser(ABC):
    @abstractmethod
    async def open_tab(self, agent_id: str) -> str:
        """Opens a new tab or isolated browser context for the specified agent.
        
        Args:
            agent_id: Unique identifier for the agent session.
            
        Returns:
            A status message confirming the tab is open.
        """
        pass

    @abstractmethod
    async def close_tab(self, agent_id: str) -> str:
        """Closes the tab/context associated with the agent to free resources.
        
        Args:
            agent_id: Unique identifier for the agent session.
            
        Returns:
            A status message confirming the tab is closed.
        """
        pass

    @abstractmethod
    async def navigate(self, agent_id: str, url: str) -> str:
        """Navigates the agent's tab to a specified URL.
        
        Args:
            agent_id: Unique identifier for the agent session.
            url: The target web address.
            
        Returns:
            A status message confirming navigation or error.
        """
        pass

    @abstractmethod
    async def execute_js(self, agent_id: str, script: str) -> str:
        """Executes arbitrary JavaScript code on the agent's active page.
        
        Args:
            agent_id: Unique identifier for the agent session.
            script: The JavaScript code to execute.
            
        Returns:
            The stringified result of the script execution.
        """
        pass

    @abstractmethod
    async def get_console_logs(self, agent_id: str) -> str:
        """Retrieves formatted console logs, errors, and messages for the agent's tab.
        
        Args:
            agent_id: Unique identifier for the agent session.
            
        Returns:
            A formatted string listing the console log entries.
        """
        pass

    @abstractmethod
    async def get_accessibility_tree(self, agent_id: str) -> str:
        """Generates a simplified accessibility tree of the page for LLM consumption.
        
        Args:
            agent_id: Unique identifier for the agent session.
            
        Returns:
            A stringified JSON or formatted representation of the accessibility tree.
        """
        pass

    @abstractmethod
    async def interact_click(self, agent_id: str, selector_or_id: str) -> str:
        """Clicks an element matching the selector or test ID.
        
        Args:
            agent_id: Unique identifier for the agent session.
            selector_or_id: The CSS selector or ID of the element to click.
            
        Returns:
            A status message.
        """
        pass

    @abstractmethod
    async def interact_type(self, agent_id: str, selector_or_id: str, text: str) -> str:
        """Types text into an input field matching the selector or ID.
        
        Args:
            agent_id: Unique identifier for the agent session.
            selector_or_id: The input element selector.
            text: The text to type.
            
        Returns:
            A status message.
        """
        pass

    @abstractmethod
    async def search_duckduckgo_serp(self, agent_id: str, query: str) -> str:
        """Performs a search on DuckDuckGo and returns results.
        
        Args:
            agent_id: Unique identifier for the agent session.
            query: The search query.
            
        Returns:
            A string containing the search results (e.g. JSON list).
        """
        pass


    @abstractmethod
    async def take_screenshot(self, agent_id: str) -> str:
        """Captures a screenshot of the current page, returning base64 representation.
        
        Args:
            agent_id: Unique identifier for the agent session.
            
        Returns:
            Base64 encoded image string.
        """
        pass

    @abstractmethod
    async def capture_screenshot_to_file(self, agent_id: str, file_path: str) -> str:
        """Captures a screenshot of the current page and saves it to a file.
        
        Args:
            agent_id: Unique identifier for the agent session.
            file_path: Absolute or relative file path to save the screenshot.
            
        Returns:
            A status message confirming the file path where the screenshot was saved.
        """
        pass

    @abstractmethod
    async def save_as_pdf(self, agent_id: str, file_path: Optional[str] = None) -> str:
        """Saves the current page layout as a PDF.
        
        Args:
            agent_id: Unique identifier for the agent session.
            file_path: Optional path to save the PDF. If not specified, returning base64.
            
        Returns:
            The file path to the generated PDF, status message, or base64 representation.
        """
        pass

    @abstractmethod
    async def wait_for_selector(self, agent_id: str, selector: str, timeout_ms: int = 30000) -> str:
        """Waits until an element matching the selector appears on the page.
        
        Args:
            agent_id: Unique identifier for the agent session.
            selector: The CSS selector to wait for.
            timeout_ms: Timeout duration in milliseconds.
            
        Returns:
            A status message confirming the element appeared or timeout message.
        """
        pass

    @abstractmethod
    async def wait_for_load_state(self, agent_id: str, state: str = "networkidle") -> str:
        """Waits for a specific loading state (e.g. load, domcontentloaded, networkidle).
        
        Args:
            agent_id: Unique identifier for the agent session.
            state: The target load state.
            
        Returns:
            A status message.
        """
        pass

    @abstractmethod
    async def wait(self, agent_id: str, time_ms: int) -> str:
        """Pauses execution for a specified duration in milliseconds.
        
        Args:
            agent_id: Unique identifier for the agent session.
            time_ms: Duration to wait in milliseconds.
            
        Returns:
            A status message confirming the wait completed.
        """
        pass

    @abstractmethod
    async def interact_scroll(self, agent_id: str, direction: str, amount: int) -> str:
        """Scrolls the page in a given direction.
        
        Args:
            agent_id: Unique identifier for the agent session.
            direction: 'up', 'down', 'left', or 'right'.
            amount: The number of pixels or window heights to scroll.
            
        Returns:
            A status message.
        """
        pass

    @abstractmethod
    async def select_dropdown_option(self, agent_id: str, selector: str, value: str) -> str:
        """Selects a value in a dropdown menu.
        
        Args:
            agent_id: Unique identifier for the agent session.
            selector: The dropdown element selector.
            value: The option value to select.
            
        Returns:
            A status message.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Closes the browser instance and releases all active sessions/resources."""
        pass

