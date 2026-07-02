import os
import time
import subprocess
import requests
import pytest

# llama-server
LLAMA_HOST = "http://localhost:8080"
LLAMA_BASE_URL = f"{LLAMA_HOST}/v1"
LLAMA_MODEL_NAME = "gemma-4-E4B-it-Q8_0"
LLAMA_MODEL_PATH = os.path.expanduser("~/models/gemma-4-E4B-it-Q8_0.gguf")
LLAMA_CONTEXT_SIZE = 81920

# MCP server
MCP_HOST = "http://localhost:8000"
MCP_URL = f"{MCP_HOST}/mcp"

STARTUP_TIMEOUT_S = 120
POLL_INTERVAL_S = 1


def _wait_until_ready(url: str, label: str):
    deadline = time.time() + STARTUP_TIMEOUT_S
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code < 500:
                return
        except requests.ConnectionError:
            pass
        time.sleep(POLL_INTERVAL_S)
    raise RuntimeError(f"{label} did not become ready within {STARTUP_TIMEOUT_S}s")


@pytest.fixture(scope="session")
def llama_server():
    process = subprocess.Popen(
        [
            "llama-server",
            "--model", LLAMA_MODEL_PATH,
            "-c", str(LLAMA_CONTEXT_SIZE),
            "--port", "8080",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_ready(f"{LLAMA_HOST}/health", "llama-server")
        yield
    finally:
        process.terminate()
        process.wait()


@pytest.fixture(scope="session")
def mcp_server():
    process = subprocess.Popen(
        ["uv", "run", "main.py"],
        env={**os.environ, "FASTMCP_HOST": "127.0.0.1", "FASTMCP_PORT": "8000", "BROWSER_HEADLESS": "false"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_ready(MCP_HOST, "mcp-server")
        yield
    finally:
        process.terminate()
        process.wait()
