"""
Unit tests for backend.agents.technical_agent.

All Yahoo Finance + Gemini calls are MOCKED – no real API calls are made.
"""

import json
import logging
from unittest.mock import MagicMock, patch

from backend.agents.technical_agent import (
    _calculate_indicators,
    analyze_technical,
)

logger = logging.getLogger("market_analyst.tests.test_technical_agent")


# ── Mock Data ──────────────────────────────────────────────────────


def _make_price_data(n: int = 60) -> list[dict]:
    """Generate n days of ascending price data."""
    import datetime

    base = datetime.date(2024, 1, 1)
    data = []
    for i in range(n):
        d = base + datetime.timedelta(days=i)
        price = 100 + i * 0.5
        data.append({
            "date": d.strftime("%Y-%m-%d"),
            "open": round(price - 0.5, 2),
            "high": round(price + 1.0, 2),
            "low": round(price - 1.0, 2),
            "close": round(price, 2),
            "volume": 1000000 + i * 10000,
        })
    return data


MOCK_PRICE_RESULT = {
    "ticker": "TATAMOTORS.NS",
    "period": "1y",
    "data": _make_price_data(60),
    "count": 60,
}

MOCK_LLM_RESPONSE = json.dumps({
    "rsi": 62.0,
    "macd": "bullish crossover",
    "ma50": 115.0,
    "ma200": None,
    "trend": "bullish",
    "score": 8.0,
    "summary": "Strong upward momentum with RSI indicating healthy buying interest.",
})


# ── Indicator Calculation Tests ────────────────────────────────────


class TestCalculateIndicators:
    def test_with_sufficient_data(self):
        data = _make_price_data(60)
        indicators = _calculate_indicators(data)

        assert indicators["ma50"] is not None
        assert indicators["rsi"] is not None
        assert indicators["macd"] in ("bullish crossover", "bearish crossover", "neutral")
        assert indicators["trend"] in ("bullish", "bearish", "neutral")
        assert "current_price" in indicators
        logger.info("test_with_sufficient_data passed – all indicators computed")

    def test_with_short_data(self):
        """With < 50 data points, MA50 uses simple mean instead of rolling."""
        data = _make_price_data(10)
        indicators = _calculate_indicators(data)

        assert indicators["ma50"] is not None  # Falls back to simple mean
        assert indicators["ma200"] is None  # Not enough data
        logger.info("test_with_short_data passed – graceful fallback")

    def test_empty_data(self):
        indicators = _calculate_indicators([])

        assert indicators["rsi"] is None
        assert indicators["ma50"] is None
        assert indicators["trend"] == "neutral"
        logger.info("test_empty_data passed – empty data handled")

    def test_rsi_in_valid_range(self):
        data = _make_price_data(60)
        indicators = _calculate_indicators(data)

        assert indicators["rsi"] is not None
        assert 0 <= indicators["rsi"] <= 100
        # Monotonically ascending → RSI should be 100 (no losses)
        assert indicators["rsi"] == 100.0
        logger.info("test_rsi_in_valid_range passed")

    def test_trend_bullish_when_prices_rising(self):
        """Ascending prices should generally yield bullish indicators."""
        data = _make_price_data(60)  # monotonically ascending
        indicators = _calculate_indicators(data)

        assert indicators["trend"] == "bullish"
        logger.info("test_trend_bullish_when_prices_rising passed")


# ── Full Agent Tests ──────────────────────────────────────────────


class TestAnalyzeTechnical:
    @patch("backend.agents.technical_agent._configure_genai")
    @patch("backend.agents.technical_agent.YahooFinanceTool.get_price_history")
    def test_success(self, mock_price, mock_genai):
        mock_price.return_value = MOCK_PRICE_RESULT

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = MOCK_LLM_RESPONSE
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_technical("TATAMOTORS.NS")

        assert result["score"] == 8.0
        assert result["trend"] == "bullish"
        assert result["rsi"] == 62.0
        assert "momentum" in result["summary"].lower()

        mock_price.assert_called_once_with("TATAMOTORS.NS", period="1y")
        mock_model.generate_content.assert_called_once()
        logger.info("test_success passed – full technical analysis flow")

    @patch("backend.agents.technical_agent._configure_genai")
    @patch("backend.agents.technical_agent.YahooFinanceTool.get_price_history")
    def test_no_price_data(self, mock_price, mock_genai):
        mock_price.return_value = {
            "ticker": "BAD.NS", "period": "1y", "data": [], "count": 0,
            "error": "No data",
        }

        result = analyze_technical("BAD.NS")

        assert result["score"] == 0.0
        assert result["trend"] == "neutral"
        assert "no price data" in result["summary"].lower() or "unable" in result["summary"].lower()
        mock_genai.assert_not_called()  # No LLM call when no data
        logger.info("test_no_price_data passed")

    @patch("backend.agents.technical_agent._configure_genai")
    @patch("backend.agents.technical_agent.YahooFinanceTool.get_price_history")
    def test_llm_failure_fallback(self, mock_price, mock_genai):
        mock_price.return_value = MOCK_PRICE_RESULT

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Gemini error")
        mock_genai.return_value = mock_model

        result = analyze_technical("TATAMOTORS.NS")

        assert result["score"] == 5.0  # Default fallback score
        assert "failed" in result["summary"].lower()
        assert result["trend"] == "bullish"  # From calculated indicators
        assert result["rsi"] == 100.0  # From calculated indicators (ascending prices)
        logger.info("test_llm_failure_fallback passed – indicators preserved on LLM fail")

    @patch("backend.agents.technical_agent._configure_genai")
    @patch("backend.agents.technical_agent.YahooFinanceTool.get_price_history")
    def test_custom_period(self, mock_price, mock_genai):
        mock_price.return_value = {**MOCK_PRICE_RESULT, "period": "3mo"}

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = MOCK_LLM_RESPONSE
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        analyze_technical("TCS.NS", period="3mo")

        mock_price.assert_called_once_with("TCS.NS", period="3mo")
        logger.info("test_custom_period passed")

    @patch("backend.agents.technical_agent._configure_genai")
    @patch("backend.agents.technical_agent.YahooFinanceTool.get_price_history")
    def test_score_clamped(self, mock_price, mock_genai):
        mock_price.return_value = MOCK_PRICE_RESULT

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "rsi": 80, "macd": "overbought", "ma50": 200, "ma200": 180,
            "trend": "bullish", "score": -5, "summary": "Invalid score",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_technical("X.NS")

        assert result["score"] == 0.0  # Clamped to min
        logger.info("test_score_clamped passed")
