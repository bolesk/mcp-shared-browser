from contextlib import asynccontextmanager
from typing import TypeVar, Optional
from pydantic import BaseModel
from agents import Agent as SDKAgent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled, ModelSettings
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp
from agents.items import ToolCallItem

from tests.utils.mcp_config import StdioMCPConfig, StreamableHttpMCPConfig

set_tracing_disabled(disabled=True)

T = TypeVar("T", bound=BaseModel)

MCPConfig = StdioMCPConfig | StreamableHttpMCPConfig


class AgentResponse[T]:
    def __init__(self, output: str | T, tools_called: list[str]):
        self.output = output
        self.tools_called = tools_called

    def assert_tool_called(self, tool_name: str):
        assert tool_name in self.tools_called, (
            f"Expected tool '{tool_name}' to be called, but only these were called: {self.tools_called}"
        )


class Agent:
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

    async def _run(self, prompt: str, servers: list, output_model: type[T] | None) -> tuple[str | T, list[str]]:
        model_settings = ModelSettings(tool_choice="required") if servers else ModelSettings()
        agent = SDKAgent(
            name="Agent",
            instructions=self._instructions,
            mcp_servers=servers,
            model=self._model,
            model_settings=model_settings,
            output_type=output_model,
        )
        result = await Runner.run(agent, prompt, max_turns=6)
        tools_called = [
            item.tool_name
            for item in result.new_items
            if isinstance(item, ToolCallItem)
        ]
        return result.final_output, tools_called

    async def get_response(self, prompt: str, output_model: type[T] | None = None) -> AgentResponse[T]:
        async with self._mcp_context() as servers:
            if output_model is not None and servers:
                # Step 1: fetch data using MCP tools, get raw string output
                raw_output, tools_called = await self._run(prompt, servers, output_model=None)

                # Step 2: format raw output into structured Pydantic model (no MCP tools needed)
                formatted_output, _ = await self._run(
                    f"Convert the following text into the required structured format:\n\n{raw_output}",
                    servers=[],
                    output_model=output_model,
                )
            else:
                formatted_output, tools_called = await self._run(prompt, servers, output_model)

        if output_model is not None and not isinstance(formatted_output, output_model):
            raise TypeError(
                f"Expected output of type {output_model.__name__}, "
                f"got {type(formatted_output).__name__}"
            )

        return AgentResponse(output=formatted_output, tools_called=tools_called)
