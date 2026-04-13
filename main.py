from agent.agent import Agent
from agent.events import AgentEventType

import asyncio
import click
import sys

from ui.tui import TUI, get_console

console = get_console()


class CLI:
    def __init__(self):
        self.agent: Agent | None = None
        self.tui = TUI(console)

    async def run_single(self, message: str) -> str | None:
        async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)

    async def _process_message(self, message: str) -> str | None:
        if not self.agent:
            return None
        assistant_streaming = False
        final_response = None
        async for event in self.agent.run(message):
            if event and event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content", "") if event else ""
                if not assistant_streaming:
                    self.tui.begin_assistant()
                    assistant_streaming = True

                self.tui.stream_assistant_delta(content)

            elif event and event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
                if assistant_streaming:
                    self.tui.end_assistant()
                    assistant_streaming = False
            elif event and event.type == AgentEventType.AGENT_ERROR:
                error = event.data.get("error", "Unknown Error")
                console.print(f"[error]Agent Error:[/error] {error}")

            elif event and event.type == AgentEventType.TOOL_CALL_START:
                tool_name = event.data.get("name", "unknown")
                tool_kind=None
                tool=self.agent.tool_registry.get(tool_name)
                if not tool:
                    tool_kind=None
                else:
                    tool_kind=tool.kind.value
                    self.tui.tool_call_start(
                        event.data.get("call_id", ""),
                        tool_name,
                        tool_kind,
                        event.data.get("arguments", {}),
                    )


            return final_response


@click.command()
@click.argument("prompt", required=False)
def main(prompt: str | None):
    cli = CLI()
    message = [{"role": "user", "content": prompt}] if prompt else None
    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if not result:
            sys.exit(1)


main()
