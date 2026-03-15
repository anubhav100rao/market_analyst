"""
SQLite MCP Server Wrapper

This module uses the official MCP Python SDK to communicate with a local
Node.js SQLite MCP server (`mcp-sqlite-server`).
It provides a persistent caching layer for API calls.
"""

import json
import logging
import os
import time
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# We want the database in the project root
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "market_analysis.db"
)

logger = logging.getLogger("market_analyst.tools.sqlite_mcp")


class SQLiteMCPTool:
    """Wrapper for the official SQLite MCP server to handle API caching."""
    
    _session: ClientSession | None = None
    _exit_stack = None

    @classmethod
    async def initialize(cls):
        """Start the MCP server process and establish a session."""
        if cls._session is not None:
            return

        logger.info("Initializing SQLite MCP Server at %s", DB_PATH)
        
        # Make sure the file exists
        if not os.path.exists(DB_PATH):
            open(DB_PATH, 'a').close()

        server_params = StdioServerParameters(
            command="npx",
            args=["--no", "mcp-sqlite-server", str(DB_PATH)],
        )

        from contextlib import AsyncExitStack
        cls._exit_stack = AsyncExitStack()
        
        try:
            stdio_transport = await cls._exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            cls._session = await cls._exit_stack.enter_async_context(ClientSession(read, write))
            await cls._session.initialize()
            
            logger.info("SQLite MCP Client connected successfully.")
            await cls._init_schema()
            
        except Exception as e:
            logger.error("Failed to initialize SQLite MCP client: %s", e)
            if cls._exit_stack:
                await cls._exit_stack.aclose()
            cls._session = None

    @classmethod
    async def shutdown(cls):
        """Close the MCP server connection."""
        if cls._exit_stack:
            await cls._exit_stack.aclose()
            cls._session = None
            logger.info("SQLite MCP connection closed.")

    @classmethod
    async def _init_schema(cls):
        """Create the cache table if it doesn't exist."""
        if not cls._session:
            return
            
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
        try:
            await cls._session.call_tool("query", arguments={
                "db": DB_PATH,
                "sql": query,
                "readonly": False
            })
            logger.info("Database schema initialized.")
        except Exception as e:
            logger.error("Error creating schema via MCP: %s", e)

    @classmethod
    async def get_cache(cls, tool_name: str, cache_key: str, max_age_seconds: int = 86400) -> dict[str, Any] | None:
        """
        Retrieve a cached API response via MCP if it hasn't expired.
        """
        if not cls._session:
            return None

        # Calculate the oldest timestamp we consider valid
        oldest_valid_time = time.time() - max_age_seconds

        query = f"SELECT response_data FROM api_cache WHERE tool_name = '{tool_name}' AND cache_key = '{cache_key}' AND created_at > {oldest_valid_time};"
        
        try:
            result = await cls._session.call_tool("query", arguments={
                "db": DB_PATH,
                "sql": query
            })
            
            # The MCP tool returns a list of content blocks.
            # `mcp-sqlite-server` returns an ASCII table as text, e.g.
            # "Rows: 1\n\nresponse_data\n------\n{...}"
            content = result.content[0].text
            
            if "Rows: 0" in content or "0 rows" in content.lower() or content.strip() == "":
                logger.info("Cache MISS for %s:%s (or expired)", tool_name, cache_key)
                return None
                
            # Try to extract the JSON dictionary from the text
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx+1]
                    logger.info("Cache HIT for %s:%s", tool_name, cache_key)
                    return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON from cache: %s", e)
                
            logger.info("Cache MISS for %s:%s (format unexpected)", tool_name, cache_key)
            return None
            
        except Exception as e:
            logger.error("Error reading cache via MCP: %s", e)
            return None

    @classmethod
    async def set_cache(cls, tool_name: str, cache_key: str, data: dict[str, Any]):
        """
        Store an API response in the SQLite database via MCP.
        """
        if not cls._session:
            return

        json_data = json.dumps(data).replace("'", "''") # Basic SQL escaping for single quotes
        now = time.time()
        
        query = f"""
        INSERT INTO api_cache (tool_name, cache_key, response_data, created_at) 
        VALUES ('{tool_name}', '{cache_key}', '{json_data}', {now})
        ON CONFLICT(tool_name, cache_key) DO UPDATE SET 
            response_data=excluded.response_data, 
            created_at=excluded.created_at;
        """
        
        try:
            await cls._session.call_tool("query", arguments={
                "db": DB_PATH,
                "sql": query,
                "readonly": False
            })
            logger.info("Cache SET for %s:%s", tool_name, cache_key)
        except Exception as e:
            logger.error("Error writing cache via MCP: %s", e)
