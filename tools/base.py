import abc
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from dataclasses import dataclass

@dataclass
class ToolInvocation:
    cwd:Path
    parameters:dict[str,Any]


class ToolKind(str, Enum):
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    MEMPORY = "memory"
    NETWORK = "network"
    MCP = "mcp"


class Tool(abc.ABC):
    name: str = "base_tool"
    description: str = "Base tool does nothing"
    kind: ToolKind = ToolKind.READ

    def __init__(self) -> None:
        pass

    def schema(self) -> dict[str, Any] | type[BaseModel]:
        raise NotImplementedError("Tool schema not implemented for base tool")
    abc.abstractmethod
    async def execute(self,invocation:ToolInvocation)->ToolResults:
        pass
