from typing import Any
from rich.console import Console
from rich.theme import Theme
from rich.rule import Rule
from rich.text import Text
from rich.panel import Panel

AGENT_THEME = Theme(
    {
        # Core levels
        "info": "bold cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        # Debug / internal
        "debug": "dim white",
        "trace": "dim magenta",
        # Agent states
        "thinking": "italic blue",
        "processing": "bold blue",
        "ready": "bold green",
        # User vs System
        "user": "bold bright_white",
        "assistant": "bold bright_cyan",
        "system": "bold magenta",
        # Highlight / emphasis
        "highlight": "bold bright_yellow",
        "muted": "dim white",
        # Headers / titles
        "title": "bold underline bright_blue",
        "subtitle": "bold bright_magenta",
        # 🔧 Tool kinds (NEW)
        "tool.read": "cyan",
        "tool.write": "green",
        "tool.shell": "yellow",
        "tool.memory": "magenta",
        "tool.network": "blue",
        "tool.mcp": "bright_cyan bold",
    }
)
_console: Console | None = None


def get_console() -> Console:
    global _console
    if _console is None:
        _console = Console(theme=AGENT_THEME, highlight=False)
    return _console


class TUI:
    def __init__(self, console: Console | None = None):
        self.console = console or get_console()
        self._assistant_stream_open = False
        self._tool_args_by_call_id: dict[str, dict[str, Any]] = {}

    def begin_assistant(self) -> None:
        self.console.print()
        self.console.print(Rule(Text("Assistant", style="assistant")))
        self._assistant_stream_open = True

    def stream_assistant_delta(self, content: str) -> None:
        self.console.print(content, markup=False, end=" ")

    def end_assistant(self) -> None:
        if self._assistant_stream_open:
            self.console.print()
            self._assistant_stream_open = False

    def tool_call_start(
        self, call_id: str, name: str, tool_kind: str | None, arguments: dict[str, Any]
    ) -> None:
        self._tool_args_by_call_id[call_id] = arguments
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"
        title=Text.assemble(
            (".","muted"),
            (name,"tool"),
            ("  ","muted"),
            (f"#{call_id[:8]}","muted"),
        )
        panel=Panel(
            
        )
