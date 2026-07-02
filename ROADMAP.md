# Roadmap

## Automated Agent Testing via pytest

Test suite that drives a real LLM agent against the running MCP server to verify every tool end-to-end.

### Stack

| Component | Choice | Notes |
|-----------|--------|-------|
| Test framework | `pytest` + `pytest-asyncio` | async-native |
| Agent SDK | `openai-agents` (Python) | provider-agnostic via `set_default_openai_client` |
| LLM inference | `llama-server` (llama.cpp) | OpenAI-compatible REST at `localhost:8080` |
| Primary model | **Gemma 4 27B** Q4_K_M (~16 GB) | best tool-calling quality, τ2-bench 86.4% |
| Fast/CI model | **Gemma 4 E4B** Q8 (~5 GB) | fast iteration and CI runs |
| Fallback model | **Qwen3-Coder-30B-A3B** Q4_K_M (~17 GB) | MoE, excellent for agentic coding; requires `--jinja` flag |
| Static test pages | `http.server` (stdlib) | local HTML fixtures for controlled scenarios |

### llama-server setup

```bash
# Gemma 4 27B (quality runs)
llama-server --model gemma-4-27b-Q4_K_M.gguf -c 8192 --port 8080

# Gemma 4 E4B (fast/CI)
llama-server --model gemma-4-E4B-Q8_0.gguf -c 8192 --port 8080

# Qwen3-Coder 30B-A3B (--jinja required for tool calling)
llama-server --model Qwen3-Coder-30B-A3B-Q4_K_M.gguf --jinja -c 8192 --port 8080
```

---

### Files to create

```
tests/
├── conftest.py                  # fixtures: MCP server, llama-server client, local HTTP server
├── agent_harness.py             # MCP→OpenAI tool bridge + agent run loop
├── test_browser_tools.py        # one test per tool / logical group
└── fixtures/
    └── pages/
        ├── form.html            # input text + dropdown + submit button
        ├── js_console.html      # emits console.log/error on load
        └── scroll.html          # long page with anchor links
```

---

### conftest.py — fixtures

- **`llm_client`** (scope `session`) — `AsyncOpenAI(base_url="http://localhost:8080/v1")` + `set_default_openai_client` + `set_default_openai_api("chat_completions")`
- **`mcp_server`** (scope `session`) — starts the MCP server as a subprocess, waits for it to be ready, tears it down after all tests
- **`local_http_server`** (scope `session`) — serves `tests/fixtures/pages/` on a random port via `http.server`
- **`agent`** (scope `function`) — builds an `Agent` with MCP tools attached; unique session-id per test for tab isolation

---

### agent_harness.py

- Connects to MCP server via streamable-http
- Converts MCP tool definitions to OpenAI function-calling schema
- Runs the agent loop: prompt → LLM → tool call → result → LLM → … → final answer
- Returns both the final text response and the ordered list of tool calls made (for assertions)

---

### test_browser_tools.py — test matrix

| Test | Tools covered | Scenario |
|------|--------------|----------|
| `test_open_close_tab` | `open_tab`, `close_tab` | open and close without navigating |
| `test_navigate_and_screenshot` | `navigate`, `take_screenshot` | navigate to `https://example.com`, verify base64 PNG returned |
| `test_accessibility_tree` | `navigate`, `get_accessibility_tree` | verify ARIA tree contains expected landmarks |
| `test_interact_form` | `navigate`, `interact_type`, `interact_click`, `wait_for_selector` | fill and submit local form |
| `test_execute_js` | `navigate`, `execute_js` | inject JS, verify return value |
| `test_console_logs` | `navigate`, `get_console_logs` | verify JS console messages are captured |
| `test_scroll` | `navigate`, `interact_scroll` | scroll long local page, verify position changed |
| `test_dropdown` | `navigate`, `select_dropdown_option` | select option in `<select>`, verify via JS |
| `test_wait_for_selector` | `navigate`, `wait_for_selector` | element appears after JS delay |
| `test_wait_for_load_state` | `navigate`, `wait_for_load_state` | wait for `networkidle` after navigation |
| `test_wait_ms` | `navigate`, `wait` | pause execution for specified ms |
| `test_duckduckgo_search` | `search_duckduckgo_serp` | real query, verify JSON list structure |
| `test_save_pdf` | `navigate`, `save_as_pdf` | verify base64 output starts with PDF magic bytes |
| `test_screenshot_to_file` | `navigate`, `capture_screenshot_to_file` | verify file written to disk |
| `test_multi_session_isolation` | all navigation tools | two agents in parallel on different pages, verify no cross-contamination |

Tests assert on **observable side effects** (page state via `get_accessibility_tree`, files on disk, structure of JSON results), not on the LLM's text response.

---

### pytest markers

```ini
# pyproject.toml [tool.pytest.ini_options]
markers = [
    "slow: tests that use the full 27B model (deselect with -m 'not slow')",
]
asyncio_mode = "auto"
```
