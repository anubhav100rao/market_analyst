import asyncio
import logging
from backend.tools.sqlite_mcp_tool import SQLiteMCPTool
from backend.workflows.market_graph import run_analysis

logging.basicConfig(level=logging.INFO)

async def main():
    await SQLiteMCPTool.initialize()
    
    # First call (should MISS graph cache, but might hit tool caches, then populate graph cache)
    print("\n--- FIRST CALL ---")
    res1 = await run_analysis("Tell me about Infy stock.")
    print(f"Result 1 Recommendation: {res1.get('recommendation')}")
    
    # Second call (should HIT graph cache)
    print("\n--- SECOND CALL ---")
    res2 = await run_analysis("What is the outlook for Infosys?")
    print(f"Result 2 Recommendation: {res2.get('recommendation')}")
    
    await SQLiteMCPTool.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
