from tkinter import N
from typing import Any
from httpx._transports import base
from openai import AsyncOpenAI

class LLMClient:

    def __init__(self)->None:
        self.client:AsyncOpenAI|None = None

    def get_client(self)->AsyncOpenAI:
        if self.client is None:
            self.client=AsyncOpenAI(
                api_key="sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                base_url="https://openrouter.ai/api/v1"
            )
        return self.client
    
    async def close(self)->None:
        if self.client:
            await self.client.close()
            self.client=None

    async def chat_completions(self,messages:list[dict[str,Any]],stream:bool=True)-:
        pass