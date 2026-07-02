from contextlib import asynccontextmanager
from typing import TypeVar, Optional
from pydantic import BaseModel
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp

from tests.utils.mcp_config import StdioMCPConfig, StreamableHttpMCPConfig

set_tracing_disabled(disabled=True)

T = TypeVar("T", bound=BaseModel)

MCPConfig = StdioMCPConfig | StreamableHttpMCPConfig


class BrowserAgent:
    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        mcp_config: MCPConfig | None = None,
        api_key: str = "not-needed",
        instructions: str = "You are a helpful assistant with access to a web browser.",
    ):
        self._mcp_config = mcp_config
        self._instructions = instructions
        self._model = OpenAIChatCompletionsModel(
            model=model,
            openai_client=AsyncOpenAI(api_key=api_key, base_url=base_url),
        )

    def _build_mcp_server(self):
        if isinstance(self._mcp_config, StdioMCPConfig):
            return MCPServerStdio(
                name="mcp-shared-browser",
                params={
                    "command": self._mcp_config.command,
                    "args": self._mcp_config.args,
                    **({"env": self._mcp_config.env} if self._mcp_config.env else {}),
                },
            )
        return MCPServerStreamableHttp(
            name="mcp-shared-browser",
            params={
                "url": self._mcp_config.url,
                "headers": self._mcp_config.headers,
                "timeout": self._mcp_config.timeout,
            },
            cache_tools_list=True,
        )

    @asynccontextmanager
    async def _mcp_context(self):
        if self._mcp_config is None:
            yield []
        else:
            async with self._build_mcp_server() as server:
                yield [server]

    async def get_response(self, prompt: str, output_model: type[T] | None = None) -> str | T:
        async with self._mcp_context() as servers:
            agent = Agent(
                name="BrowserAgent",
                instructions=self._instructions,
                mcp_servers=servers,
                model=self._model,
                output_type=output_model,
            )
            result = await Runner.run(agent, prompt)
            final_output = result.final_output

            if output_model is not None:
                if not isinstance(final_output, output_model):
                    raise TypeError(
                        f"Expected output of type {output_model.__name__}, "
                        f"got {type(final_output).__name__}"
                    )

            return final_output
