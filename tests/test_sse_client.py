import asyncio
import sys

# Asegurar soporte de asyncio loop en Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    url = "http://11.170.12.150:8000/sse"
    print(f"Connecting to MCP SSE server at {url}...")
    try:
        async with sse_client(url) as (read_stream, write_stream):
            print("SSE connection established. Initializing session...")
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("Session initialized successfully!")
                
                # List tools
                print("\nFetching tools via SSE Client...")
                tools_result = await session.list_tools()
                # En mcp python sdk, list_tools devuelve un objeto con un campo tools
                tools = tools_result.tools if hasattr(tools_result, 'tools') else tools_result
                print(f"Total tools found: {len(tools)}")
                for t in tools:
                    print(f"  - {t.name}: {t.description[:60]}...")
                
                # Call tool
                print("\nCalling get_catalogo_datos via SSE Client...")
                result = await session.call_tool("get_catalogo_datos", {})
                print("Call successful!")
                print("Result content (first 500 chars):")
                print(str(result.content)[:500])
    except Exception as e:
        print("\n❌ Error during SSE MCP Client execution:", e)

if __name__ == "__main__":
    asyncio.run(main())
