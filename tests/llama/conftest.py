import os
import time
import subprocess
import requests
import pytest

LLAMA_HOST = "http://localhost:8080"
MODEL_PATH = os.path.expanduser("~/models/gemma-4-E4B-it-Q8_0.gguf")
LLAMA_MODEL_NAME = "gemma-4-E4B-it-Q8_0"
LLAMA_BASE_URL = f"{LLAMA_HOST}/v1"

STARTUP_TIMEOUT_S = 60
POLL_INTERVAL_S = 1


def _wait_until_ready():
    deadline = time.time() + STARTUP_TIMEOUT_S
    while time.time() < deadline:
        try:
            resp = requests.get(f"{LLAMA_HOST}/health", timeout=2)
            if resp.status_code == 200:
                return
        except requests.ConnectionError:
            pass
        time.sleep(POLL_INTERVAL_S)
    raise RuntimeError(f"llama-server did not become ready within {STARTUP_TIMEOUT_S}s")


@pytest.fixture(scope="session")
def llama_server():
    process = subprocess.Popen(
        [
            "llama-server",
            "--model", MODEL_PATH,
            "-c", "8192",
            "--port", "8080",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_ready()
        yield
    finally:
        process.terminate()
        process.wait()
