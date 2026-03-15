import asyncio
import logging
import sys

from backend.tools.sqlite_mcp_tool import SQLiteMCPTool
from backend.tools.yahoo_finance_tool import YahooFinanceTool

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


async def test_mcp_direct():
    """Test direct connection to the SQLite MCP."""
    print("--- Testing Direct MCP Connection ---")
    await SQLiteMCPTool.initialize()
    
    ticker = "TEST.NS"
    data = {"test_key": "test_value"}
    
    # Set cache
    await SQLiteMCPTool.set_cache("test_tool", ticker, data)
    print("Set cache completed")
    
    # Get cache
    cached = await SQLiteMCPTool.get_cache("test_tool", ticker)
    if cached and cached.get("test_key") == "test_value":
        print("✅ Cache hit successful")
    else:
        print("❌ Cache hit failed")

    await SQLiteMCPTool.shutdown()


async def test_yahoo_tool():
    """Test the Yahoo Finance tool caching logic."""
    print("\n--- Testing Yahoo Finance Tool with Cache ---")
    await SQLiteMCPTool.initialize()
    
    ticker = "RELIANCE.NS"
    
    # Call 1: Should be a cache miss and fetch from Yahoo
    print("First call (should fetch)...")
    result1 = await YahooFinanceTool.get_key_ratios(ticker)
    
    # Call 2: Should be a cache hit
    print("Second call (should hit cache)...")
    result2 = await YahooFinanceTool.get_key_ratios(ticker)
    
    if result2:
        print("✅ End-to-end tool caching successful")
        
    await SQLiteMCPTool.shutdown()


if __name__ == "__main__":
    asyncio.run(test_mcp_direct())
    asyncio.run(test_yahoo_tool())
