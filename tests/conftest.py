import os
import asyncio
import pytest
from adapters import XvfbDisplay, NoopDisplay

@pytest.fixture(scope="session", autouse=True)
def virtual_display():
    in_docker = os.path.exists("/.dockerenv")
    display = XvfbDisplay() if in_docker else NoopDisplay()
    asyncio.run(display.start())
    yield
    asyncio.run(display.stop())
