
import asyncio
from datetime import timedelta
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def call_mcp_tool(tool_name: str, args: dict) -> str:
    try:
        async with sse_client("http://127.0.0.1:8080/sse") as streams:
            async with ClientSession(streams[0], streams[1], read_timeout_seconds=timedelta(seconds=60)) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, args)
                return result.content[0].text
    except ExceptionGroup as eg:
        sub_errors = [f"{type(e).__name__}: {e}" for e in eg.exceptions]
        return f"Error: {type(eg).__name__}: {eg} (Sub-errors: {', '.join(sub_errors)})"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

if __name__ == "__main__":
    res = asyncio.run(call_mcp_tool("query_sql", {"sql_query": "SELECT * FROM movies LIMIT 1"}))
    print(res)
