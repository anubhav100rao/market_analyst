"""
LangGraph Market Analysis Workflow.

Orchestrates the full analysis pipeline:
  START → intent_analyzer → [fundamental, technical, sentiment] (parallel) → aggregator → END

Uses LangGraph StateGraph for node coordination and state management.
"""

from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.fundamental_agent import analyze_fundamental
from backend.agents.intent_analyzer import analyze_intent, analyze_intent_from_request
from backend.agents.master_agent import aggregate_analysis
from backend.agents.sentiment_agent import analyze_sentiment
from backend.agents.technical_agent import analyze_technical
from backend.tools.sqlite_mcp_tool import SQLiteMCPTool

logger = logging.getLogger("market_analyst.workflows.market_graph")


# ── State Definition ──────────────────────────────────────────────
# TypedDict with default values so LangGraph knows every channel.


def _replace(old, new):
    """Reducer: always use the latest value."""
    return new


class MarketGraphState(TypedDict, total=False):
    """State that flows through every node in the graph."""

    query: str
    stocks: list[str]
    analysis_type: str
    parsed_query: str
    fundamental_result: dict
    technical_result: dict
    sentiment_result: dict
    final_decision: str
    recommendation: str
    reasoning: str
    stock_verdicts: dict


# ── Node Functions ────────────────────────────────────────────────


def intent_node(state: dict) -> dict:
    """
    Entry node: parse the user query to extract stocks and analysis type.

    If stocks and analysis_type are already set (from typed API endpoints),
    skip LLM-based intent analysis.
    """
    logger.info("=== Intent Analyzer Node ===")
    logger.info("Input state keys: %s", list(state.keys()))

    # If stocks already provided (from typed endpoints), skip LLM
    if state.get("stocks") and state.get("analysis_type"):
        logger.info("Intent pre-set: stocks=%s, type=%s", state["stocks"], state["analysis_type"])
        return {
            "parsed_query": state.get("query", ""),
        }

    # Otherwise, use LLM to parse the query
    query = state.get("query", "")
    intent = analyze_intent(query)

    logger.info("Intent result: %s", intent)
    return {
        "stocks": intent["stocks"],
        "analysis_type": intent["analysis_type"],
        "parsed_query": intent["parsed_query"],
    }


async def fundamental_node(state: dict) -> dict:
    """Run fundamental analysis for all stocks in the state."""
    logger.info("=== Fundamental Analyst Node ===")
    stocks = state.get("stocks", [])
    results = {}

    for ticker in stocks:
        logger.info("Running fundamental analysis for %s", ticker)
        results[ticker] = await analyze_fundamental(ticker)

    logger.info("Fundamental analysis complete for %d stocks", len(results))
    return {"fundamental_result": results}


async def technical_node(state: dict) -> dict:
    """Run technical analysis for all stocks in the state."""
    logger.info("=== Technical Analyst Node ===")
    stocks = state.get("stocks", [])
    results = {}

    for ticker in stocks:
        logger.info("Running technical analysis for %s", ticker)
        results[ticker] = await analyze_technical(ticker)

    logger.info("Technical analysis complete for %d stocks", len(results))
    return {"technical_result": results}


async def sentiment_node(state: dict) -> dict:
    """Run sentiment analysis for all stocks in the state."""
    logger.info("=== Sentiment Analyst Node ===")
    stocks = state.get("stocks", [])
    results = {}

    for ticker in stocks:
        logger.info("Running sentiment analysis for %s", ticker)
        results[ticker] = await analyze_sentiment(ticker)

    logger.info("Sentiment analysis complete for %d stocks", len(results))
    return {"sentiment_result": results}


def aggregator_node(state: dict) -> dict:
    """Combine all agent results into a final recommendation."""
    logger.info("=== Master Aggregator Node ===")

    stocks = state.get("stocks", [])
    analysis_type = state.get("analysis_type", "single")
    fundamental = state.get("fundamental_result", {})
    technical = state.get("technical_result", {})
    sentiment = state.get("sentiment_result", {})

    logger.info(
        "Aggregating: stocks=%s, type=%s, has_fundamental=%s, has_technical=%s, has_sentiment=%s",
        stocks, analysis_type,
        bool(fundamental), bool(technical), bool(sentiment),
    )

    result = aggregate_analysis(
        stocks=stocks,
        analysis_type=analysis_type,
        fundamental_results=fundamental,
        technical_results=technical,
        sentiment_results=sentiment,
    )

    logger.info("Aggregation complete: recommendation=%s", result.get("recommendation"))
    return {
        "final_decision": result.get("recommendation", "HOLD"),
        "recommendation": result.get("recommendation", "HOLD"),
        "reasoning": result.get("reasoning", ""),
        "stock_verdicts": result.get("stock_verdicts", {}),
    }


# ── Graph Construction ────────────────────────────────────────────


def build_market_graph() -> StateGraph:
    """
    Build and compile the LangGraph workflow.

    Graph structure:
        START → intent_analyzer → [fundamental, technical, sentiment] → aggregator → END

    The three analyst nodes run in parallel (fan-out / fan-in).
    """
    logger.info("Building market analysis graph")

    # Create the graph with typed state
    graph = StateGraph(MarketGraphState)

    # Add nodes
    graph.add_node("intent_analyzer", intent_node)
    graph.add_node("fundamental", fundamental_node)
    graph.add_node("technical", technical_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("aggregator", aggregator_node)

    # START → intent_analyzer
    graph.add_edge(START, "intent_analyzer")

    # intent_analyzer → parallel fan-out to all three analysts
    graph.add_edge("intent_analyzer", "fundamental")
    graph.add_edge("intent_analyzer", "technical")
    graph.add_edge("intent_analyzer", "sentiment")

    # All three analysts → aggregator (fan-in)
    graph.add_edge("fundamental", "aggregator")
    graph.add_edge("technical", "aggregator")
    graph.add_edge("sentiment", "aggregator")

    # aggregator → END
    graph.add_edge("aggregator", END)

    logger.info("Market analysis graph built successfully")
    return graph


def compile_market_graph():
    """Build and compile the graph, returning a runnable."""
    graph = build_market_graph()
    compiled = graph.compile()
    logger.info("Market analysis graph compiled")
    return compiled


async def _check_and_run_graph(initial_state: dict) -> dict:
    """Helper to check graph-level cache before running the full workflow."""
    stocks = initial_state.get("stocks", [])
    analysis_type = initial_state.get("analysis_type", "single")
    
    # Simple cache key based on intent, avoiding the raw user query
    # E.g., 'single_RELIANCE.NS', 'compare_INFY.NS_TCS.NS'
    cache_key = f"{analysis_type}_{'_'.join(sorted(stocks))}"
    
    # Attempt to fetch full graph result from cache
    cached = await SQLiteMCPTool.get_cache("market_graph", cache_key, max_age_seconds=86400)
    if cached:
        logger.info("Graph cache HIT for %s", cache_key)
        # Restore the original query strings for context
        cached["query"] = initial_state.get("query", "")
        cached["parsed_query"] = initial_state.get("parsed_query", "")
        return cached

    logger.info("Graph cache MISS for %s. Running workflow...", cache_key)
    compiled = compile_market_graph()
    result = await compiled.ainvoke(initial_state)
    
    # Save successful execution to cache
    await SQLiteMCPTool.set_cache("market_graph", cache_key, result)
    return result


async def parse_intent_cached(query: str) -> dict:
    """
    Parse user intent with caching to avoid redundant LLM calls.

    Cache key is the normalised query string. Returns the intent dict
    with stocks, analysis_type, and parsed_query.
    """
    cache_key = query.strip().lower()

    cached = await SQLiteMCPTool.get_cache(
        "intent_analysis", cache_key, max_age_seconds=86400,
    )
    if cached:
        logger.info("Intent cache HIT for %r", cache_key)
        return cached

    logger.info("Intent cache MISS for %r – calling LLM", cache_key)
    intent = analyze_intent(query)

    await SQLiteMCPTool.set_cache("intent_analysis", cache_key, intent)
    return intent


async def run_analysis(query: str) -> dict:
    """
    Run the full analysis pipeline from a free-form query.
    1. Parse intent (cached to avoid duplicate LLM calls).
    2. Check the graph cache for those parsed stocks.
    3. Run graph on miss.
    """
    logger.info("Starting analysis pipeline for query: %r", query)

    intent = await parse_intent_cached(query)
    initial_state = {
        "query": query,
        "stocks": intent["stocks"],
        "analysis_type": intent["analysis_type"],
        "parsed_query": intent["parsed_query"],
    }

    return await _check_and_run_graph(initial_state)


async def run_single_stock_analysis(ticker: str) -> dict:
    """Run analysis for a single stock (typed endpoint)."""
    logger.info("Starting single stock analysis for %s", ticker)

    initial_state = {
        "query": f"Analyze {ticker}",
        "stocks": [ticker],
        "analysis_type": "single",
        "parsed_query": f"Analyze {ticker}",
    }

    return await _check_and_run_graph(initial_state)


async def run_compare_stocks(ticker_a: str, ticker_b: str) -> dict:
    """Run comparison analysis for two stocks (typed endpoint)."""
    logger.info("Starting comparison: %s vs %s", ticker_a, ticker_b)

    initial_state = {
        "query": f"Compare {ticker_a} and {ticker_b}",
        "stocks": [ticker_a, ticker_b],
        "analysis_type": "compare",
        "parsed_query": f"Compare {ticker_a} and {ticker_b}",
    }

    return await _check_and_run_graph(initial_state)


async def run_portfolio_analysis(tickers: list[str]) -> dict:
    """Run portfolio analysis for multiple stocks (typed endpoint)."""
    logger.info("Starting portfolio analysis for %s", tickers)

    initial_state = {
        "query": f"Portfolio analysis: {', '.join(tickers)}",
        "stocks": tickers,
        "analysis_type": "portfolio",
        "parsed_query": f"Portfolio analysis: {', '.join(tickers)}",
    }

    return await _check_and_run_graph(initial_state)
