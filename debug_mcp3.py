import asyncio
from backend.tools.sqlite_mcp_tool import SQLiteMCPTool, DB_PATH

async def main():
    await SQLiteMCPTool.initialize()
    query = """
    CREATE TABLE IF NOT EXISTS api_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_name TEXT NOT NULL,
        cache_key TEXT NOT NULL,
        response_data TEXT NOT NULL,
        created_at REAL NOT NULL,
        UNIQUE(tool_name, cache_key)
    )
    """
    result = await SQLiteMCPTool._session.call_tool("query", arguments={"db": DB_PATH, "sql": query})
    with open("mcp_output3.txt", "w") as f:
        f.write(f"isError: {getattr(result, 'isError', False)}\n")
        f.write(repr(result.content[0].text))
    await SQLiteMCPTool.shutdown()

asyncio.run(main())
