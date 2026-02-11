from typing import Any
from client.llm_client import LLMClient
import asyncio
import click


class CLI:
    def __init__(self):
        pass

    def run_single(self):
        pass

async def run(messages:list[dict[str,Any]]):
    client=LLMClient()
    async for event in client.chat_completions(messages=messages,stream=True):
        print(event)


@click.command()
@click.argument("prompt",required=False)
def main(prompt:str|None):
    print("prompt",prompt)
    
   
    asyncio.run(run(messages))
   
    print("Done")

main()