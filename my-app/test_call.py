import asyncio
from langgraph_sdk import get_client

async def main():
    client = get_client(url="http://127.0.0.1:2030")  # matches --port above
    assistant_id = "agent"  # server logs say: Registering graph with id 'agent'
    payload = {"messages": [{"role": "user", "content": "say hi"}]}
    result = await client.runs.wait(None, assistant_id, input=payload)  # stateless run
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
