import asyncio

from typing import Any, AsyncGenerator


from client.response import StreamEventType, StreamEvent, TextDelta, TokenUsage
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APIError
from dotenv import load_dotenv
import os

load_dotenv()


class LLMClient:
    def __init__(self) -> None:
        self.client: AsyncOpenAI | None = None
        self.max_retries: int = 3

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
    ) -> AsyncGenerator[StreamEvent, None]:
        client = self.get_client()
        kwargs = {
            "model": "mistralai/mistral-small-3.1-24b-instruct:free",
            "messages": messages,
            "stream": stream,
        }
        for attempt in range(self.max_retries + 1):
            try:
                if stream:
                    async for event in self._stream_response(client, kwargs):
                        yield event
                else:
                    event = await self._non_stream_response(client, kwargs)

                    yield event
                return
            except RateLimitError as e:
                if attempt < self.max_retries:
                    backoff_time = 2**attempt
                    await asyncio.sleep(backoff_time)
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR, error=f"Rate limit exceeded {e}."
                    )
                    return
            except APIConnectionError as e:
                if attempt < self.max_retries:
                    backoff_time = 2**attempt
                    await asyncio.sleep(backoff_time)
                else:
                    yield StreamEvent(
                        type=StreamEventType.ERROR,
                        error=f"API Connection Error exceeded {e}.",
                    )
                    return
            except APIError as e:
                yield StreamEvent(type=StreamEventType.ERROR, error=f"API Error:{e}.")
                return

    async def _stream_response(
        self, client: AsyncOpenAI, kwargs: dict[str, Any]
    ) -> AsyncGenerator[StreamEvent, None]:
        response = await client.chat.completions.create(**kwargs)
        usage: TokenUsage | None = None
        finish_reason: str | None = None
        for chunk in response:
            if hasattr(chunk, "usage") and chunk.usage:
                usage = TokenUsage(
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    total_tokens=chunk.usage.total_tokens,
                    cached_tokens=chunk.usage.prompt_tokens_details.cached_tokens,
                )
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = choice.delta
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            if delta.content:
                yield StreamEvent(
                    type=StreamEventType.MESSAGE_DELTA,
                    text_delta=TextDelta(content=delta.content),
                    usage=usage,
                    finish_reason=finish_reason,
                )
        yield StreamEvent(
            type=StreamEventType.MESSAGE_COMPLETE,
            usage=usage,
            finish_reason=finish_reason,
        )

    async def _non_stream_response(
        self, client: AsyncOpenAI, kwargs: dict[str, Any]
    ) -> StreamEvent:
        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message
        text_delta = None
        if message.content:
            text_delta = TextDelta(content=message.content)
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cached_tokens=response.usage.prompt_tokens_details.cached_tokens,
            )
        else:
            usage = None
        return StreamEvent(
            type=StreamEventType.MESSAGE_COMPLETE,
            text_delta=text_delta,
            finish_reason=choice.finish_reason,
            usage=usage,
        )
