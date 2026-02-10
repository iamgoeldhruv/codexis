from client.llm_client import LLMClient
import asyncio

async def main():
    client=LLMClient();
    messages=[
        {"role":"system","content":"You are a helpful assistant."},
    ]
    async for event in client.chat_completions(messages=messages,stream=True):
        print(event)
    print("Done")

asyncio.run(main())