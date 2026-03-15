import asyncio
from backend.tools.sqlite_mcp_tool import SQLiteMCPTool, DB_PATH

async def main():
    await SQLiteMCPTool.initialize()
    query = "SELECT * FROM api_cache;"
    result = await SQLiteMCPTool._session.call_tool("query", arguments={"db": DB_PATH, "sql": query})
    with open("mcp_output.txt", "w") as f:
        f.write(repr(result.content[0].text))
    await SQLiteMCPTool.shutdown()

asyncio.run(main())
