"""
Unit tests for backend.agents.intent_analyzer.

All Gemini calls are MOCKED – no real API calls are made.
"""

import json
import logging
from unittest.mock import MagicMock, patch

from backend.agents.intent_analyzer import (
    analyze_intent,
    analyze_intent_from_request,
)

logger = logging.getLogger("market_analyst.tests.test_intent_analyzer")


# ── Tests ──────────────────────────────────────────────────────────


class TestAnalyzeIntent:
    @patch("backend.agents.intent_analyzer._configure_genai")
    def test_single_stock_query(self, mock_genai):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "single",
            "parsed_query": "Analyze Reliance Industries",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_intent("How is Reliance doing?")

        assert result["stocks"] == ["RELIANCE.NS"]
        assert result["analysis_type"] == "single"
        assert "Reliance" in result["parsed_query"]
        logger.info("test_single_stock_query passed")

    @patch("backend.agents.intent_analyzer._configure_genai")
    def test_compare_query(self, mock_genai):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "stocks": ["TATAMOTORS.NS", "M&M.NS"],
            "analysis_type": "compare",
            "parsed_query": "Compare Tata Motors vs Mahindra",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_intent("Compare Tata Motors and Mahindra")

        assert len(result["stocks"]) == 2
        assert result["analysis_type"] == "compare"
        logger.info("test_compare_query passed")

    @patch("backend.agents.intent_analyzer._configure_genai")
    def test_portfolio_query(self, mock_genai):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "stocks": ["RELIANCE.NS", "TCS.NS", "INFY.NS"],
            "analysis_type": "portfolio",
            "parsed_query": "Analyze portfolio",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_intent("How is my portfolio of Reliance, TCS, Infosys?")

        assert len(result["stocks"]) == 3
        assert result["analysis_type"] == "portfolio"
        logger.info("test_portfolio_query passed")

    @patch("backend.agents.intent_analyzer._configure_genai")
    def test_auto_corrects_type_single(self, mock_genai):
        """If LLM returns 'compare' but only 1 stock, auto-correct to 'single'."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "compare",  # Wrong!
            "parsed_query": "Reliance",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_intent("Reliance")

        assert result["analysis_type"] == "single"  # Auto-corrected
        logger.info("test_auto_corrects_type_single passed")

    @patch("backend.agents.intent_analyzer._configure_genai")
    def test_auto_corrects_type_portfolio(self, mock_genai):
        """If LLM returns 'single' but 3+ stocks, auto-correct to 'portfolio'."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "stocks": ["A.NS", "B.NS", "C.NS"],
            "analysis_type": "single",
            "parsed_query": "Multiple stocks",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_intent("How are A, B, C?")

        assert result["analysis_type"] == "portfolio"
        logger.info("test_auto_corrects_type_portfolio passed")

    @patch("backend.agents.intent_analyzer._configure_genai")
    def test_llm_failure_returns_defaults(self, mock_genai):
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API error")
        mock_genai.return_value = mock_model

        result = analyze_intent("Whatever query")

        assert result["stocks"] == []
        assert result["analysis_type"] == "single"
        assert result["parsed_query"] == "Whatever query"
        logger.info("test_llm_failure_returns_defaults passed")

    @patch("backend.agents.intent_analyzer._configure_genai")
    def test_no_stocks_found(self, mock_genai):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "stocks": [],
            "analysis_type": "single",
            "parsed_query": "What is the market doing?",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_intent("What is the market doing?")

        assert result["stocks"] == []
        assert result["analysis_type"] == "single"
        logger.info("test_no_stocks_found passed")


class TestAnalyzeIntentFromRequest:
    def test_single_stock(self):
        result = analyze_intent_from_request(
            stocks=["RELIANCE.NS"],
            analysis_type="single",
        )
        assert result["stocks"] == ["RELIANCE.NS"]
        assert result["analysis_type"] == "single"
        assert "RELIANCE.NS" in result["parsed_query"]
        logger.info("test_single_stock passed")

    def test_comparison(self):
        result = analyze_intent_from_request(
            stocks=["TATAMOTORS.NS", "M&M.NS"],
            analysis_type="compare",
            query="Compare them",
        )
        assert result["analysis_type"] == "compare"
        assert result["parsed_query"] == "Compare them"
        logger.info("test_comparison passed")

    def test_portfolio(self):
        result = analyze_intent_from_request(
            stocks=["A.NS", "B.NS", "C.NS"],
            analysis_type="portfolio",
        )
        assert result["analysis_type"] == "portfolio"
        assert len(result["stocks"]) == 3
        logger.info("test_portfolio passed")
