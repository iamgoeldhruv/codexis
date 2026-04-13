import dis
from pathlib import Path

from typing import Any
from rich.console import Console
from rich.theme import Theme
from rich.rule import Rule
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box
from utils.path import display_path_relative_to_cwd, resolve_path

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
        "code": "white",
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
        self.cwd = Path.cwd()

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

    def _ordered_args(self, tool_name: str, args: dict[str, Any]) -> list[tuple]:
        _PREFERRED_ORDER = {"read_file": ["path", "offset", "limit"]}
        tool = _PREFERRED_ORDER.get(tool_name, [])
        ordered: list[tuple[str, Any]] = []
        seen = set()
        for arg in tool:
            if arg in args:
                ordered.append((arg, args[arg]))
                seen.add(arg)
        remaining_keys = set(args.keys() - seen)
        ordered.extend([(k, args[k]) for k in sorted(remaining_keys)])
        return ordered

    def _render_args_table(self, tool_name: str, args: dict[str, Any]) -> Table:
        table = Table.grid(padding=(0, 1))
        table.add_column(justify="right", style="muted", no_wrap=True)
        table.add_column(style="code", overflow="fold")
        for key, value in self._ordered_args(tool_name, args):
            table.add_row(key, value)
        return table

    def tool_call_start(
        self, call_id: str, name: str, tool_kind: str | None, arguments: dict[str, Any]
    ) -> None:
        self._tool_args_by_call_id[call_id] = arguments
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"
        title = Text.assemble(
            (".", "muted"),
            (name, "tool"),
            ("  ", "muted"),
            (f"#{call_id[:8]}", "muted"),
        )
        display_args = dict(arguments)
        for key in ("path", "crd"):
            val = display_args.get(key)
            if isinstance(val, str) and self.cwd:
                display_args[key] = display_path_relative_to_cwd(val, self.cwd)
        panel = Panel(
            self._render_args_table(name, display_args)
            if display_args
            else Text("(no arguments)", style="muted"),
            box=box.ROUNDED,
            padding=(1, 2),
            title=title,
            border_style=border_style,
            subtitle=Text("running", style="muted"),
            text_align="left",
            subtitle_align="right",
        )
        self.console.print()
        self.console.print(panel)
