from client.llm_client import LLMClient
import asyncio

async def main():
    client=LLMClient();
    messages=[
        {"role":"system","content":"You are a helpful assistant."},
    ]
    await client.chat_completions(messages=messages,stream=False)
    print("Done")

asyncio.run(main())