"""
Unit tests for backend.agents.fundamental_agent.

All Yahoo Finance + Gemini calls are MOCKED – no real API calls are made.
"""

import json
import logging
from unittest.mock import MagicMock, patch

from backend.agents.fundamental_agent import analyze_fundamental, _parse_llm_response

logger = logging.getLogger("market_analyst.tests.test_fundamental_agent")


# ── Mock Data ──────────────────────────────────────────────────────


MOCK_RATIOS = {
    "ticker": "RELIANCE.NS",
    "pe_ratio": 24.5,
    "forward_pe": 20.0,
    "market_cap": 18000000000000,
    "profit_margin": 0.11,
    "debt_to_equity": 45.0,
    "revenue": 2500000000000,
    "earnings_growth": 0.08,
    "revenue_growth": 0.12,
    "current_price": 2450.0,
    "company_name": "Reliance Industries Limited",
}

MOCK_FINANCIALS = {
    "ticker": "RELIANCE.NS",
    "income_statement": [{"period": "2023-03-31", "Total Revenue": 5000000}],
    "balance_sheet": [{"period": "2023-03-31", "Total Assets": 10000000}],
    "cash_flow": [{"period": "2023-03-31", "Operating Cash Flow": 800000}],
}

MOCK_LLM_RESPONSE = json.dumps({
    "revenue": "₹2.5T",
    "pe_ratio": 24.5,
    "earnings_growth": "8%",
    "market_cap": "₹18T",
    "debt": "moderate",
    "profit_margin": "11%",
    "score": 7.5,
    "summary": "Reliance has strong revenue and moderate debt levels.",
})


# ── Tests ──────────────────────────────────────────────────────────


class TestParseLlmResponse:
    def test_plain_json(self):
        result = _parse_llm_response('{"score": 7.0}')
        assert result["score"] == 7.0
        logger.info("test_plain_json passed")

    def test_json_with_code_fences(self):
        text = "```json\n{\"score\": 8.0}\n```"
        result = _parse_llm_response(text)
        assert result["score"] == 8.0
        logger.info("test_json_with_code_fences passed")

    def test_json_with_plain_fences(self):
        text = "```\n{\"score\": 6.0}\n```"
        result = _parse_llm_response(text)
        assert result["score"] == 6.0
        logger.info("test_json_with_plain_fences passed")


class TestAnalyzeFundamental:
    @patch("backend.agents.fundamental_agent._configure_genai")
    @patch("backend.agents.fundamental_agent.YahooFinanceTool.get_financial_statements")
    @patch("backend.agents.fundamental_agent.YahooFinanceTool.get_key_ratios")
    def test_success(self, mock_ratios, mock_financials, mock_genai):
        mock_ratios.return_value = MOCK_RATIOS
        mock_financials.return_value = MOCK_FINANCIALS

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = MOCK_LLM_RESPONSE
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_fundamental("RELIANCE.NS")

        assert result["score"] == 7.5
        assert result["pe_ratio"] == 24.5
        assert result["debt"] == "moderate"
        assert "Reliance" in result["summary"]

        mock_ratios.assert_called_once_with("RELIANCE.NS")
        mock_financials.assert_called_once_with("RELIANCE.NS")
        mock_model.generate_content.assert_called_once()
        logger.info("test_success passed – full fundamental analysis flow")

    @patch("backend.agents.fundamental_agent._configure_genai")
    @patch("backend.agents.fundamental_agent.YahooFinanceTool.get_financial_statements")
    @patch("backend.agents.fundamental_agent.YahooFinanceTool.get_key_ratios")
    def test_both_tool_failures(self, mock_ratios, mock_financials, mock_genai):
        mock_ratios.return_value = {"ticker": "BAD.NS", "error": "Not found"}
        mock_financials.return_value = {"ticker": "BAD.NS", "error": "Not found", "income_statement": [], "balance_sheet": [], "cash_flow": []}

        result = analyze_fundamental("BAD.NS")

        assert result["score"] == 0.0
        assert "unavailable" in result["summary"].lower() or "unable" in result["summary"].lower()
        mock_genai.assert_not_called()  # LLM should NOT be called
        logger.info("test_both_tool_failures passed – no LLM call when data unavailable")

    @patch("backend.agents.fundamental_agent._configure_genai")
    @patch("backend.agents.fundamental_agent.YahooFinanceTool.get_financial_statements")
    @patch("backend.agents.fundamental_agent.YahooFinanceTool.get_key_ratios")
    def test_llm_failure_fallback(self, mock_ratios, mock_financials, mock_genai):
        mock_ratios.return_value = MOCK_RATIOS
        mock_financials.return_value = MOCK_FINANCIALS

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Gemini API error")
        mock_genai.return_value = mock_model

        result = analyze_fundamental("RELIANCE.NS")

        # Should fall back to raw data
        assert result["score"] == 5.0
        assert "failed" in result["summary"].lower()
        assert result["pe_ratio"] == 24.5  # From raw ratios
        logger.info("test_llm_failure_fallback passed – graceful degradation")

    @patch("backend.agents.fundamental_agent._configure_genai")
    @patch("backend.agents.fundamental_agent.YahooFinanceTool.get_financial_statements")
    @patch("backend.agents.fundamental_agent.YahooFinanceTool.get_key_ratios")
    def test_score_clamped(self, mock_ratios, mock_financials, mock_genai):
        """Score is clamped to [0, 10] even if LLM returns out-of-range."""
        mock_ratios.return_value = MOCK_RATIOS
        mock_financials.return_value = MOCK_FINANCIALS

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "revenue": "₹2.5T", "pe_ratio": 24.5, "earnings_growth": "8%",
            "market_cap": "₹18T", "debt": "low", "profit_margin": "11%",
            "score": 15.0,  # Out of range!
            "summary": "Excellent",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_fundamental("RELIANCE.NS")

        assert result["score"] == 10.0  # Clamped to max
        logger.info("test_score_clamped passed – out-of-range score clamped to 10")
