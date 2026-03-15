import asyncio
import sys
import logging
from backend.tools.sqlite_mcp_tool import SQLiteMCPTool

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    try:
        await SQLiteMCPTool.initialize()
        query = "SELECT 1 as num;"
        result = await SQLiteMCPTool._session.call_tool("read_query", arguments={"query": query})
        print("RAW CONTENT BLOCK 0:")
        print(repr(result.content[0].text))
    except Exception as e:
        print("ERROR:", e)
    finally:
        await SQLiteMCPTool.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
