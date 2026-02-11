from typing import AsyncGenerator

from agent.events import AgentEvent
from client.llm_client import LLMClient
from client.response import StreamEventType


class Agent:
    def __init__(self):
        self.client = LLMClient()

    async def _agentic_loop(self) -> AsyncGenerator[AgentEvent | None]:
        client = self.client
        messages = [
            {"role": "system", "content": "Hey waths up"},
        ]
        async for event in client.chat_completions(messages=messages, stream=True):
            if event.type==StreamEventType.MESSAGE_DELTA:
                content=event.text_delta.content if event.text_delta else ""
                yield AgentEvent.text_delta(content)

