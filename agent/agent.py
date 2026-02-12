from __future__ import annotations
from typing import AsyncGenerator, cast

from agent.events import AgentEvent, AgentEventType
from client.llm_client import LLMClient
from client.response import StreamEventType


class Agent:
    def __init__(self):
        self.client = LLMClient()

    async def run(self, message: str):
        yield AgentEvent.agent_start(message)
        final_text: str = ""
        async for event in self._agentic_loop():
            yield event
            if event and event.type == AgentEventType.TEXT_COMPLETE:
                final_text = cast(str, event.data.get("content"))

        yield AgentEvent.agent_end(response=final_text)

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent | None]:
        client = self.client
        messages = [
            {"role": "system", "content": "Hey waths up"},
        ]
        response_text = ""
        if not client:
            yield None
            return 
        async for event in client.chat_completions(messages=messages, stream=True):
            if event.type == StreamEventType.MESSAGE_DELTA:
                content = event.text_delta.content if event.text_delta else ""
                response_text += content
                yield AgentEvent.text_delta(content)
            if event.type == StreamEventType.ERROR:
                yield AgentEvent.agent_error(event.error or "Unknown error occured")
        if response_text:
            yield AgentEvent.text_complete(response_text)

    async def __aenter__(self) -> Agent:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.close()
            self.client = None
