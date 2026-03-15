"""
Unit tests for backend.models.state – LangGraph state definitions.

All tests are pure Python, no LLM calls required.
"""

import logging

from backend.models.state import (
    FundamentalResult,
    MarketState,
    SentimentResult,
    TechnicalResult,
)

logger = logging.getLogger("market_analyst.tests.test_state")


class TestFundamentalResult:
    """Tests for FundamentalResult TypedDict."""

    def test_create_full(self):
        """Can create a FundamentalResult with all fields."""
        result: FundamentalResult = {
            "revenue": "₹2.5T",
            "pe_ratio": 24.0,
            "earnings_growth": "8%",
            "market_cap": "₹18T",
            "debt": "moderate",
            "profit_margin": "11%",
            "score": 7.0,
            "summary": "Strong fundamentals overall",
        }
        assert result["score"] == 7.0
        assert result["pe_ratio"] == 24.0
        assert result["revenue"] == "₹2.5T"
        logger.info("test_create_full passed – FundamentalResult created with all fields")

    def test_create_partial(self):
        """Can create with only some fields (total=False)."""
        result: FundamentalResult = {"score": 5.0, "summary": "Incomplete data"}
        assert result["score"] == 5.0
        assert "pe_ratio" not in result
        logger.info("test_create_partial passed – partial FundamentalResult works")

    def test_pe_ratio_none(self):
        """PE ratio can be None when data is unavailable."""
        result: FundamentalResult = {"pe_ratio": None, "score": 0.0}
        assert result["pe_ratio"] is None
        logger.info("test_pe_ratio_none passed")


class TestTechnicalResult:
    """Tests for TechnicalResult TypedDict."""

    def test_create_full(self):
        result: TechnicalResult = {
            "rsi": 62.0,
            "macd": "bullish crossover",
            "ma50": 450.0,
            "ma200": 420.0,
            "trend": "bullish",
            "score": 8.0,
            "summary": "Strong bullish momentum",
        }
        assert result["trend"] == "bullish"
        assert result["rsi"] == 62.0
        assert result["score"] == 8.0
        logger.info("test_create_full passed – TechnicalResult")

    def test_trend_values(self):
        """Trend accepts any string (validation is semantic, not structural)."""
        for trend in ("bullish", "bearish", "neutral"):
            result: TechnicalResult = {"trend": trend, "score": 5.0}
            assert result["trend"] == trend
        logger.info("test_trend_values passed")


class TestSentimentResult:
    """Tests for SentimentResult TypedDict."""

    def test_create_full(self):
        result: SentimentResult = {
            "positive_signals": ["EV expansion", "Record sales"],
            "negative_signals": ["Supply chain concerns"],
            "score": 6.0,
            "summary": "Mildly positive sentiment",
        }
        assert len(result["positive_signals"]) == 2
        assert len(result["negative_signals"]) == 1
        assert result["score"] == 6.0
        logger.info("test_create_full passed – SentimentResult")

    def test_empty_signals(self):
        result: SentimentResult = {
            "positive_signals": [],
            "negative_signals": [],
            "score": 5.0,
        }
        assert result["positive_signals"] == []
        logger.info("test_empty_signals passed")


class TestMarketState:
    """Tests for the top-level MarketState TypedDict."""

    def test_create_initial_state(self):
        """Master state starts with query and stocks only."""
        state: MarketState = {
            "query": "Compare Tata Motors and Mahindra",
            "stocks": ["TATAMOTORS.NS", "M&M.NS"],
            "analysis_type": "compare",
        }
        assert state["query"] == "Compare Tata Motors and Mahindra"
        assert len(state["stocks"]) == 2
        assert state["analysis_type"] == "compare"
        logger.info("test_create_initial_state passed")

    def test_progressive_population(self):
        """State can be populated step by step as agents complete."""
        state: MarketState = {
            "query": "How is Reliance doing?",
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "single",
        }
        # Agent 1 completes
        state["fundamental_result"] = {
            "RELIANCE.NS": {"score": 7.0, "summary": "Strong"}
        }
        # Agent 2 completes
        state["technical_result"] = {
            "RELIANCE.NS": {"score": 8.0, "summary": "Bullish"}
        }
        # Agent 3 completes
        state["sentiment_result"] = {
            "RELIANCE.NS": {"score": 6.0, "summary": "Neutral"}
        }
        # Master agent
        state["final_decision"] = "BUY – strong across all dimensions"

        assert "fundamental_result" in state
        assert "technical_result" in state
        assert "sentiment_result" in state
        assert state["final_decision"].startswith("BUY")
        logger.info("test_progressive_population passed – full state lifecycle")

    def test_portfolio_state(self):
        """State supports multiple stocks for portfolio analysis."""
        state: MarketState = {
            "query": "How is my portfolio?",
            "stocks": ["RELIANCE.NS", "TCS.NS", "INFY.NS"],
            "analysis_type": "portfolio",
        }
        assert len(state["stocks"]) == 3
        assert state["analysis_type"] == "portfolio"
        logger.info("test_portfolio_state passed")

    def test_empty_stocks_list(self):
        """State with no stocks identified yet."""
        state: MarketState = {
            "query": "Market overview",
            "stocks": [],
        }
        assert state["stocks"] == []
        logger.info("test_empty_stocks_list passed")
