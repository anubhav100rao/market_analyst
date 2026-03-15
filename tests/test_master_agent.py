"""
Unit tests for backend.agents.master_agent.

All Gemini calls are MOCKED – no real API calls are made.
"""

import json
import logging
from unittest.mock import MagicMock, patch

from backend.agents.master_agent import (
    _build_fallback_recommendation,
    aggregate_analysis,
)

logger = logging.getLogger("market_analyst.tests.test_master_agent")


# ── Mock Data ──────────────────────────────────────────────────────


MOCK_FUNDAMENTAL = {
    "RELIANCE.NS": {
        "score": 7.0,
        "summary": "Strong fundamentals",
        "pe_ratio": 24.5,
    },
}

MOCK_TECHNICAL = {
    "RELIANCE.NS": {
        "score": 8.0,
        "trend": "bullish",
        "summary": "Strong momentum",
    },
}

MOCK_SENTIMENT = {
    "RELIANCE.NS": {
        "score": 6.0,
        "positive_signals": ["Strong Q3"],
        "negative_signals": ["Oil price"],
        "summary": "Mildly positive",
    },
}

MOCK_LLM_RESPONSE = json.dumps({
    "recommendation": "BUY",
    "reasoning": "Strong fundamentals, bullish technicals, and mildly positive sentiment justify a BUY.",
    "stock_verdicts": {
        "RELIANCE.NS": {
            "recommendation": "BUY",
            "confidence": 7.5,
            "one_liner": "Strong across all dimensions.",
        },
    },
})

MOCK_COMPARE_FUNDAMENTAL = {
    "TATAMOTORS.NS": {"score": 6.0, "summary": "Average"},
    "M&M.NS": {"score": 7.5, "summary": "Strong balance sheet"},
}

MOCK_COMPARE_TECHNICAL = {
    "TATAMOTORS.NS": {"score": 8.0, "trend": "bullish"},
    "M&M.NS": {"score": 6.0, "trend": "neutral"},
}

MOCK_COMPARE_SENTIMENT = {
    "TATAMOTORS.NS": {"score": 5.5, "positive_signals": [], "negative_signals": []},
    "M&M.NS": {"score": 6.0, "positive_signals": ["SUV demand"], "negative_signals": []},
}

MOCK_COMPARE_LLM_RESPONSE = json.dumps({
    "recommendation": "BUY",
    "reasoning": "Tata Motors has short-term momentum. Mahindra is fundamentally stronger.",
    "stock_verdicts": {
        "TATAMOTORS.NS": {"recommendation": "BUY", "confidence": 7.0, "one_liner": "Strong technical momentum"},
        "M&M.NS": {"recommendation": "HOLD", "confidence": 6.5, "one_liner": "Fundamentally strong, wait for dip"},
    },
})


# ── Fallback Recommendation Tests ─────────────────────────────────


class TestBuildFallbackRecommendation:
    def test_buy_recommendation(self):
        """Average score >= 7.0 should trigger BUY."""
        result = _build_fallback_recommendation(
            {"S1": {"score": 8.0}},
            {"S1": {"score": 7.0}},
            {"S1": {"score": 7.0}},
        )
        assert result["recommendation"] == "BUY"
        assert "S1" in result["stock_verdicts"]
        logger.info("test_buy_recommendation passed")

    def test_sell_recommendation(self):
        """Average score <= 4.0 should trigger SELL."""
        result = _build_fallback_recommendation(
            {"S1": {"score": 3.0}},
            {"S1": {"score": 4.0}},
            {"S1": {"score": 3.0}},
        )
        assert result["recommendation"] == "SELL"
        logger.info("test_sell_recommendation passed")

    def test_hold_recommendation(self):
        """Middle scores should yield HOLD."""
        result = _build_fallback_recommendation(
            {"S1": {"score": 5.0}},
            {"S1": {"score": 5.0}},
            {"S1": {"score": 5.0}},
        )
        assert result["recommendation"] == "HOLD"
        logger.info("test_hold_recommendation passed")

    def test_multiple_stocks(self):
        result = _build_fallback_recommendation(
            {"S1": {"score": 8.0}, "S2": {"score": 3.0}},
            {"S1": {"score": 7.0}, "S2": {"score": 4.0}},
            {"S1": {"score": 7.0}, "S2": {"score": 3.5}},
        )
        assert "S1" in result["stock_verdicts"]
        assert "S2" in result["stock_verdicts"]
        assert result["stock_verdicts"]["S1"]["recommendation"] == "BUY"
        assert result["stock_verdicts"]["S2"]["recommendation"] == "SELL"
        logger.info("test_multiple_stocks passed")

    def test_missing_scores_default_to_five(self):
        result = _build_fallback_recommendation(
            {"S1": {}},  # No score
            {"S1": {}},
            {"S1": {}},
        )
        assert result["recommendation"] == "HOLD"  # 5.0 avg → HOLD
        logger.info("test_missing_scores_default_to_five passed")


# ── Full Aggregation Tests ─────────────────────────────────────────


class TestAggregateAnalysis:
    @patch("backend.agents.master_agent._configure_genai")
    def test_single_stock_success(self, mock_genai):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = MOCK_LLM_RESPONSE
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = aggregate_analysis(
            stocks=["RELIANCE.NS"],
            analysis_type="single",
            fundamental_results=MOCK_FUNDAMENTAL,
            technical_results=MOCK_TECHNICAL,
            sentiment_results=MOCK_SENTIMENT,
        )

        assert result["recommendation"] == "BUY"
        assert "reasoning" in result
        assert "RELIANCE.NS" in result["stock_verdicts"]
        mock_model.generate_content.assert_called_once()
        logger.info("test_single_stock_success passed")

    @patch("backend.agents.master_agent._configure_genai")
    def test_comparison_success(self, mock_genai):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = MOCK_COMPARE_LLM_RESPONSE
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = aggregate_analysis(
            stocks=["TATAMOTORS.NS", "M&M.NS"],
            analysis_type="compare",
            fundamental_results=MOCK_COMPARE_FUNDAMENTAL,
            technical_results=MOCK_COMPARE_TECHNICAL,
            sentiment_results=MOCK_COMPARE_SENTIMENT,
        )

        assert result["recommendation"] == "BUY"
        assert "TATAMOTORS.NS" in result["stock_verdicts"]
        assert "M&M.NS" in result["stock_verdicts"]
        assert result["stock_verdicts"]["M&M.NS"]["recommendation"] == "HOLD"
        logger.info("test_comparison_success passed")

    @patch("backend.agents.master_agent._configure_genai")
    def test_llm_failure_uses_fallback(self, mock_genai):
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API quota")
        mock_genai.return_value = mock_model

        result = aggregate_analysis(
            stocks=["RELIANCE.NS"],
            analysis_type="single",
            fundamental_results=MOCK_FUNDAMENTAL,
            technical_results=MOCK_TECHNICAL,
            sentiment_results=MOCK_SENTIMENT,
        )

        assert result["recommendation"] in ("BUY", "HOLD", "SELL")
        assert "Fallback" in result["reasoning"]
        assert "RELIANCE.NS" in result["stock_verdicts"]
        logger.info("test_llm_failure_uses_fallback passed")

    @patch("backend.agents.master_agent._configure_genai")
    def test_invalid_recommendation_defaults_to_hold(self, mock_genai):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "recommendation": "MAYBE",  # Invalid!
            "reasoning": "Not sure",
            "stock_verdicts": {},
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = aggregate_analysis(
            stocks=["X.NS"],
            analysis_type="single",
            fundamental_results={"X.NS": {"score": 5.0}},
            technical_results={"X.NS": {"score": 5.0}},
            sentiment_results={"X.NS": {"score": 5.0}},
        )

        assert result["recommendation"] == "HOLD"  # Defaults on invalid
        logger.info("test_invalid_recommendation_defaults_to_hold passed")
