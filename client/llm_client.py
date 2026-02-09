from re import S
from typing import Any, AsyncGenerator

from client.response import EventType, StreamEvent, TextDelta, TokenUsage
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv()


class LLMClient:
    def __init__(self) -> None:
        self.client: AsyncOpenAI | None = None

    def get_client(self) -> AsyncOpenAI:
        if self.client is None:
            self.client = AsyncOpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
            )
        return self.client

    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None

    async def chat_completions(
        self, messages: list[dict[str, Any]], stream: bool = True
    )->AsyncGenerator[StreamEvent, None]:
        client=self.get_client()
        kwargs={
            "model":"mistralai/mistral-small-3.1-24b-instruct:free",
            "messages":messages,
            "stream":stream
        }
        if stream:
            await self._stream_response(client)
        else:
            event=await self._non_stream_response(client,kwargs)
            yield event
        return

    async def _stream_response(self, client: AsyncOpenAI):
        pass

    async def _non_stream_response(self, client: AsyncOpenAI ,kwargs:dict[str,Any])->StreamEven:
        response = await client.chat.completions.create(**kwargs)
        choice=response.choices[0]
        message=choice.message
        text_delta=None
        if message.content:
            text_delta=TextDelta(content=message.content)
        if response.usage:
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cached_tokens=response.prompt_tokens_details.cached_tokens
            )
        else:
            usage=None
        return StreamEvent(
            type=EventType.MESSAGE_COMPLETE,
            text_delta=text_delta,
            finish_reason=choice.finish_reason,
            usage=usage

        )

