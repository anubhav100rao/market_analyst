"""
Integration tests for backend.workflows.market_graph.

All external calls (Gemini, Yahoo Finance, DuckDuckGo) are MOCKED.
Tests verify the full LangGraph pipeline execution.
"""

import json
import logging
from unittest.mock import MagicMock, patch

from backend.workflows.market_graph import (
    aggregator_node,
    build_market_graph,
    compile_market_graph,
    fundamental_node,
    intent_node,
    parse_intent_cached,
    run_analysis,
    run_compare_stocks,
    run_portfolio_analysis,
    run_single_stock_analysis,
    sentiment_node,
    technical_node,
)

logger = logging.getLogger("market_analyst.tests.test_market_graph")


# ── Mock Responses ─────────────────────────────────────────────────

MOCK_FUNDAMENTAL_RESULT = {
    "revenue": "₹2.5T",
    "pe_ratio": 24.5,
    "score": 7.0,
    "summary": "Strong fundamentals",
}

MOCK_TECHNICAL_RESULT = {
    "rsi": 62.0,
    "trend": "bullish",
    "score": 8.0,
    "summary": "Bullish momentum",
}

MOCK_SENTIMENT_RESULT = {
    "positive_signals": ["Strong Q3"],
    "negative_signals": ["Oil pressure"],
    "score": 6.0,
    "summary": "Mildly positive",
}

MOCK_AGGREGATION_RESULT = {
    "recommendation": "BUY",
    "reasoning": "Strong across all dimensions",
    "stock_verdicts": {
        "RELIANCE.NS": {
            "recommendation": "BUY",
            "confidence": 7.5,
            "one_liner": "Strong overall",
        },
    },
}


# ── Individual Node Tests ─────────────────────────────────────────


class TestIntentNode:
    def test_pre_set_intent(self):
        """When stocks and analysis_type are preset, skip LLM."""
        state = {
            "query": "Analyze RELIANCE.NS",
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "single",
        }
        result = intent_node(state)

        assert "parsed_query" in result
        # Should NOT modify stocks or analysis_type
        assert "stocks" not in result
        logger.info("test_pre_set_intent passed – LLM skipped")

    @patch("backend.workflows.market_graph.analyze_intent")
    def test_llm_intent_parsing(self, mock_analyze):
        mock_analyze.return_value = {
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "single",
            "parsed_query": "Analyze Reliance",
        }

        state = {"query": "How is Reliance?"}
        result = intent_node(state)

        assert result["stocks"] == ["RELIANCE.NS"]
        assert result["analysis_type"] == "single"
        mock_analyze.assert_called_once_with("How is Reliance?")
        logger.info("test_llm_intent_parsing passed")


class TestFundamentalNode:
    @patch("backend.workflows.market_graph.analyze_fundamental")
    def test_single_stock(self, mock_analyze):
        mock_analyze.return_value = MOCK_FUNDAMENTAL_RESULT

        state = {"stocks": ["RELIANCE.NS"]}
        result = fundamental_node(state)

        assert "RELIANCE.NS" in result["fundamental_result"]
        assert result["fundamental_result"]["RELIANCE.NS"]["score"] == 7.0
        mock_analyze.assert_called_once_with("RELIANCE.NS")
        logger.info("test_single_stock passed")

    @patch("backend.workflows.market_graph.analyze_fundamental")
    def test_multiple_stocks(self, mock_analyze):
        mock_analyze.return_value = MOCK_FUNDAMENTAL_RESULT

        state = {"stocks": ["A.NS", "B.NS"]}
        result = fundamental_node(state)

        assert len(result["fundamental_result"]) == 2
        assert mock_analyze.call_count == 2
        logger.info("test_multiple_stocks passed")


class TestTechnicalNode:
    @patch("backend.workflows.market_graph.analyze_technical")
    def test_single_stock(self, mock_analyze):
        mock_analyze.return_value = MOCK_TECHNICAL_RESULT

        state = {"stocks": ["RELIANCE.NS"]}
        result = technical_node(state)

        assert result["technical_result"]["RELIANCE.NS"]["trend"] == "bullish"
        logger.info("test_single_stock passed")


class TestSentimentNode:
    @patch("backend.workflows.market_graph.analyze_sentiment")
    def test_single_stock(self, mock_analyze):
        mock_analyze.return_value = MOCK_SENTIMENT_RESULT

        state = {"stocks": ["RELIANCE.NS"]}
        result = sentiment_node(state)

        assert result["sentiment_result"]["RELIANCE.NS"]["score"] == 6.0
        logger.info("test_single_stock passed")


class TestAggregatorNode:
    @patch("backend.workflows.market_graph.aggregate_analysis")
    def test_aggregation(self, mock_aggregate):
        mock_aggregate.return_value = MOCK_AGGREGATION_RESULT

        state = {
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "single",
            "fundamental_result": {"RELIANCE.NS": MOCK_FUNDAMENTAL_RESULT},
            "technical_result": {"RELIANCE.NS": MOCK_TECHNICAL_RESULT},
            "sentiment_result": {"RELIANCE.NS": MOCK_SENTIMENT_RESULT},
        }
        result = aggregator_node(state)

        assert result["recommendation"] == "BUY"
        assert result["final_decision"] == "BUY"
        assert "reasoning" in result
        logger.info("test_aggregation passed")


# ── Graph Construction Tests ──────────────────────────────────────


class TestGraphConstruction:
    def test_build_graph(self):
        """Graph builds without errors."""
        graph = build_market_graph()
        assert graph is not None
        logger.info("test_build_graph passed")

    def test_compile_graph(self):
        """Graph compiles into a runnable."""
        compiled = compile_market_graph()
        assert compiled is not None
        logger.info("test_compile_graph passed")


# ── Full Pipeline Integration Tests ──────────────────────────────


class TestRunSingleStockAnalysis:
    @patch("backend.workflows.market_graph.aggregate_analysis")
    @patch("backend.workflows.market_graph.analyze_sentiment")
    @patch("backend.workflows.market_graph.analyze_technical")
    @patch("backend.workflows.market_graph.analyze_fundamental")
    def test_full_pipeline(self, mock_fundamental, mock_technical, mock_sentiment, mock_aggregate):
        mock_fundamental.return_value = MOCK_FUNDAMENTAL_RESULT
        mock_technical.return_value = MOCK_TECHNICAL_RESULT
        mock_sentiment.return_value = MOCK_SENTIMENT_RESULT
        mock_aggregate.return_value = MOCK_AGGREGATION_RESULT

        result = run_single_stock_analysis("RELIANCE.NS")

        assert result["recommendation"] == "BUY"
        assert result["stocks"] == ["RELIANCE.NS"]
        assert result["analysis_type"] == "single"
        assert "RELIANCE.NS" in result["fundamental_result"]
        assert "RELIANCE.NS" in result["technical_result"]
        assert "RELIANCE.NS" in result["sentiment_result"]

        mock_fundamental.assert_called_once_with("RELIANCE.NS")
        mock_technical.assert_called_once_with("RELIANCE.NS")
        mock_sentiment.assert_called_once_with("RELIANCE.NS")
        logger.info("test_full_pipeline passed – single stock E2E")


class TestRunCompareStocks:
    @patch("backend.workflows.market_graph.aggregate_analysis")
    @patch("backend.workflows.market_graph.analyze_sentiment")
    @patch("backend.workflows.market_graph.analyze_technical")
    @patch("backend.workflows.market_graph.analyze_fundamental")
    def test_full_pipeline(self, mock_fundamental, mock_technical, mock_sentiment, mock_aggregate):
        mock_fundamental.return_value = MOCK_FUNDAMENTAL_RESULT
        mock_technical.return_value = MOCK_TECHNICAL_RESULT
        mock_sentiment.return_value = MOCK_SENTIMENT_RESULT
        mock_aggregate.return_value = MOCK_AGGREGATION_RESULT

        result = run_compare_stocks("TATAMOTORS.NS", "M&M.NS")

        assert result["analysis_type"] == "compare"
        assert len(result["stocks"]) == 2
        assert mock_fundamental.call_count == 2
        assert mock_technical.call_count == 2
        assert mock_sentiment.call_count == 2
        logger.info("test_full_pipeline passed – comparison E2E")


class TestRunPortfolioAnalysis:
    @patch("backend.workflows.market_graph.aggregate_analysis")
    @patch("backend.workflows.market_graph.analyze_sentiment")
    @patch("backend.workflows.market_graph.analyze_technical")
    @patch("backend.workflows.market_graph.analyze_fundamental")
    def test_full_pipeline(self, mock_fundamental, mock_technical, mock_sentiment, mock_aggregate):
        mock_fundamental.return_value = MOCK_FUNDAMENTAL_RESULT
        mock_technical.return_value = MOCK_TECHNICAL_RESULT
        mock_sentiment.return_value = MOCK_SENTIMENT_RESULT
        mock_aggregate.return_value = MOCK_AGGREGATION_RESULT

        result = run_portfolio_analysis(["RELIANCE.NS", "TCS.NS", "INFY.NS"])

        assert result["analysis_type"] == "portfolio"
        assert len(result["stocks"]) == 3
        assert mock_fundamental.call_count == 3
        logger.info("test_full_pipeline passed – portfolio E2E")


class TestRunAnalysis:
    @patch("backend.workflows.market_graph.aggregate_analysis")
    @patch("backend.workflows.market_graph.analyze_sentiment")
    @patch("backend.workflows.market_graph.analyze_technical")
    @patch("backend.workflows.market_graph.analyze_fundamental")
    @patch("backend.workflows.market_graph.analyze_intent")
    def test_chat_pipeline(self, mock_intent, mock_fundamental, mock_technical, mock_sentiment, mock_aggregate):
        mock_intent.return_value = {
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "single",
            "parsed_query": "Analyze Reliance",
        }
        mock_fundamental.return_value = MOCK_FUNDAMENTAL_RESULT
        mock_technical.return_value = MOCK_TECHNICAL_RESULT
        mock_sentiment.return_value = MOCK_SENTIMENT_RESULT
        mock_aggregate.return_value = MOCK_AGGREGATION_RESULT

        result = run_analysis("How is Reliance?")

        assert result["recommendation"] == "BUY"
        mock_intent.assert_called_once_with("How is Reliance?")
        logger.info("test_chat_pipeline passed – free-form query E2E")


# ── Intent Caching Tests ─────────────────────────────────────────


class TestParseIntentCached:
    @patch("backend.workflows.market_graph.SQLiteMCPTool.set_cache")
    @patch("backend.workflows.market_graph.SQLiteMCPTool.get_cache")
    @patch("backend.workflows.market_graph.analyze_intent")
    async def test_cache_miss_calls_llm(self, mock_intent, mock_get_cache, mock_set_cache):
        """On cache miss, call LLM and store result."""
        mock_get_cache.return_value = None
        mock_intent.return_value = {
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "single",
            "parsed_query": "Analyze Reliance",
        }
        mock_set_cache.return_value = None

        result = await parse_intent_cached("How is Reliance?")

        assert result["stocks"] == ["RELIANCE.NS"]
        assert result["analysis_type"] == "single"
        mock_intent.assert_called_once_with("How is Reliance?")
        mock_get_cache.assert_called_once()
        mock_set_cache.assert_called_once()
        logger.info("test_cache_miss_calls_llm passed")

    @patch("backend.workflows.market_graph.SQLiteMCPTool.get_cache")
    @patch("backend.workflows.market_graph.analyze_intent")
    async def test_cache_hit_skips_llm(self, mock_intent, mock_get_cache):
        """On cache hit, return cached intent without calling LLM."""
        mock_get_cache.return_value = {
            "stocks": ["INFY.NS"],
            "analysis_type": "single",
            "parsed_query": "Analyze Infosys",
        }

        result = await parse_intent_cached("Tell me about Infosys")

        assert result["stocks"] == ["INFY.NS"]
        mock_intent.assert_not_called()
        logger.info("test_cache_hit_skips_llm passed")

    @patch("backend.workflows.market_graph.SQLiteMCPTool.set_cache")
    @patch("backend.workflows.market_graph.SQLiteMCPTool.get_cache")
    @patch("backend.workflows.market_graph.analyze_intent")
    async def test_normalises_cache_key(self, mock_intent, mock_get_cache, mock_set_cache):
        """Cache key is normalised (lowered and stripped)."""
        mock_get_cache.return_value = None
        mock_set_cache.return_value = None
        mock_intent.return_value = {
            "stocks": ["TCS.NS"],
            "analysis_type": "single",
            "parsed_query": "Analyze TCS",
        }

        await parse_intent_cached("  How Is TCS?  ")

        # Verify cache was queried with normalised key
        call_args = mock_get_cache.call_args
        assert call_args[0][1] == "how is tcs?"
        logger.info("test_normalises_cache_key passed")
