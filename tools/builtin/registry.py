from tools.base import Tool, ToolInvocation, ToolResults
import logging
from pathlib import Path
from tools.builtin import ReadFileTool, get_all_builtin_tools
from typing import Any

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning(f"overriding existing tool {tool.name}")

        self._tools[tool.name] = tool
        logger.debug(f"Registered tool {tool.name}")

    def unregister(self, tool: Tool) -> bool:
        if tool.name in self._tools:
            del self._tools[tool.name]
            return True
        return False

    def get(self, name: str) -> Tool | None:
        if name in self._tools:
            return self._tools[name]
        return None

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        for tool in self._tools.values():
            tools.append(tool)
        return tools

    def get_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.get_tools()]

    async def invoke(self, name: str, params: dict[str, Any], cwd: Path | None):
        tool = self.get(name)
        if tool is None:
            return ToolResults.error_result(
                f"Unkown Tool {name}", metadata={"tool_name": name}
            )

        validation_errors = tool.validate_params(params)
        if validation_errors:
            return ToolResults.error_result(
                f"Invalid paraeters for tool {';'.join(validation_errors)}",
                metadata={"tool_name": name, "validation_errors": validation_errors},
            )

        invocation = ToolInvocation(parameters=params, cwd=cwd)

        try:
            await tool.execute(invocation)
        except Exception as e:
            logger.exception(f"Internal error {name}")
            return ToolResults.error_result(
                f"Internal error executing tool {name}: {str(e)}",
                metadata={"tool_name": name},
            )


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    BUILTIN_TOOLS = [ReadFileTool]
    for tool_cls in get_all_builtin_tools():
        registry.register(tool_cls())

    return registry
