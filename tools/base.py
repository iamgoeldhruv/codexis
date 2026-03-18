import abc
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from dataclasses import dataclass
from pydantic.json_schema import model_json_schema


@dataclass
class ToolInvocation:
    cwd: Path
    parameters: dict[str, Any]


class ToolKind(str, Enum):
    READ = "read"
    WRITE = "write"
    SHELL = "shell"
    MEMPORY = "memory"
    NETWORK = "network"
    MCP = "mcp"


@dataclass
class ToolConfirmation:
    tool_name: str
    params: dict[str, Any]
    description: str


@dataclass
class ToolResults:
    success: bool
    output: str
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    truncated: bool = False

    @classmethod
    def error_result(cls, error: str, output: str = "", **kwargs: Any):
        return cls(success=False, output=output, error=error, **kwargs)

    @classmethod
    def success_result(cls, truncated: bool, output: str, **kwargs: Any):
        return cls(
            success=True, output=output, error=None, truncated=truncated, **kwargs
        )

    @classmethod
    def to_model_output(self) -> str:
        if self.success:
            return self.output
        return f"Error:{self.error}\n\nOutput:\n{self.output}"


class Tool(abc.ABC):
    name: str = "base_tool"
    description: str = "Base tool does nothing"
    kind: ToolKind = ToolKind.READ

    def __init__(self) -> None:
        pass

    def schema(self) -> dict[str, Any] | type[BaseModel]:
        raise NotImplementedError("Tool schema not implemented for base tool")

    abc.abstractmethod

    async def execute(self, invocation: ToolInvocation) -> ToolResults:
        pass

    def validate_params(self, params: dict[str, Any]) -> list[Any]:
        schema = self.schema
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                BaseModel(**params)
            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error.get("loc", []))
                    msg = error.get("msg", "Validation error")
                    errors.append(f"Parameter '{field}': {msg}")
                return errors
            except Exception as e:
                return [str(e)]

        return []

    def is_mutating(self, params: dict[str, Any]) -> bool:
        return self.kind in {
            ToolKind.WRITE,
            ToolKind.SHELL,
            ToolKind.MEMPORY,
            ToolKind.NETWORK,
        }

    async def get_confirmation(
        self, invocation: ToolInvocation
    ) -> ToolConfirmation | None:
        if not self.is_mutating(invocation.parameters):
            return None

        return ToolConfirmation(
            tool_name=self.name,
            params=invocation.parameters,
            description=f"execute tool {self.name}",
        )

    def to_openai_schema(self) -> dict[str, Any]:
        schema = self.schema
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            json_schema = model_json_schema(schema, mode="serialization")
            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": json_schema.get("properties", {}),
                    "required": json_schema.get("required", []),
                },
            }
        if isinstance(schema, dict):
            result = {
                "name": self.name,
                "description": self.description,
            }
            if "parameters" in schema:
                result["parameters"] = schema["parameters"]
            else:
                result["parameters"] = schema
            return result
        raise ValueError(
            f"Invalid schema type for tool{self.name} of type {type(schema)}"
        )
