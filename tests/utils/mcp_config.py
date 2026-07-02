from dataclasses import dataclass, field

@dataclass
class StdioMCPConfig:
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None

@dataclass
class StreamableHttpMCPConfig:
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 10
