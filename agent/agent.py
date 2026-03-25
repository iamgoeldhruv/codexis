from __future__ import annotations
from pathlib import Path
from typing import AsyncGenerator, cast

from agent.events import AgentEvent, AgentEventType
from client.llm_client import LLMClient
from client.response import StreamEventType, ToolCall, ToolResultsMessage
from context.manager import ContextManager
from tools.builtin.registry import create_default_registry


class Agent:
    def __init__(self):
        self.client = LLMClient()
        self.context_manager = ContextManager()
        self.tool_registry = create_default_registry()

    async def run(self, message: str):
        yield AgentEvent.agent_start(message)
        self.context_manager.add_user_message(message)
        final_text: str | None = None
        async for event in self._agentic_loop():
            yield event
            if event and event.type == AgentEventType.TEXT_COMPLETE:
                final_text = cast(str, event.data.get("content"))

        yield AgentEvent.agent_end(response=final_text)

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent | None]:
        client = self.client

        response_text = ""
        if not client:
            yield None
            return
        tool_schemas = self.tool_registry.get_schemas()
        tool_calls: list[ToolCall] = []
        tool_call_results: list[ToolResultsMessage] = []
        async for event in client.chat_completions(
            messages=self.context_manager.get_messages(),
            tools=tool_schemas if tool_schemas else None,
            stream=True,
        ):
            if event.type == StreamEventType.MESSAGE_DELTA:
                content = event.text_delta.content if event.text_delta else ""
                response_text += content
                yield AgentEvent.text_delta(content)
            elif event.type == StreamEventType.TOOL_CALL_COMPLETE:
                if event.tool_call:
                    tool_calls.append(event.tool_call)
            elif event.type == StreamEventType.ERROR:
                yield AgentEvent.agent_error(event.error or "Unknown error occured")
        self.context_manager.add_assistant_message(response_text or None)
        if response_text:
            yield AgentEvent.text_complete(response_text)

        for tool_call in tool_calls:
            yield AgentEvent.tool_call_start(
                tool_call.call_id, tool_call.name, tool_call.arguments
            )
            result = await self.tool_registry.invoke(
                tool_call.name, tool_call.arguments, Path.cwd()
            )
            yield AgentEvent.tool_call_complete(
                tool_call.call_id, tool_call.name, result
            )
            tool_call_results.append(
                ToolResultsMessage(
                    tool_call_id=tool_call.call_id,
                    content=result.to_model_output(),
                    is_error=not result.success,
                )
            )
        for tool_result in tool_call_results:
            self.context_manager.add_tool_results(
                tool_result.tool_call_id, tool_result.content
            )

    async def __aenter__(self) -> Agent:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close()
            self.client = None
