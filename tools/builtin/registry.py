from tools.base import Tool
import logging

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
