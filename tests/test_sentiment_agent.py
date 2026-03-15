"""
Unit tests for backend.agents.sentiment_agent.

All DuckDuckGo + Gemini calls are MOCKED – no real API calls are made.
"""

import json
import logging
from unittest.mock import MagicMock, patch

from backend.agents.sentiment_agent import analyze_sentiment

logger = logging.getLogger("market_analyst.tests.test_sentiment_agent")


# ── Mock Data ──────────────────────────────────────────────────────


MOCK_NEWS_RESULT = {
    "query": "Reliance stock news India",
    "count": 3,
    "results": [
        {
            "title": "Reliance Q3 Results Beat Estimates",
            "snippet": "Reliance reported strong quarterly numbers.",
            "url": "https://example.com/1",
            "date": "2024-01-15",
            "source": "Economic Times",
        },
        {
            "title": "Reliance EV Battery Expansion",
            "snippet": "New investments in EV infrastructure.",
            "url": "https://example.com/2",
            "date": "2024-01-14",
            "source": "Mint",
        },
        {
            "title": "Oil Prices Pressure Reliance Margins",
            "snippet": "Rising crude impacts refining segment.",
            "url": "https://example.com/3",
            "date": "2024-01-13",
            "source": "Business Standard",
        },
    ],
}

MOCK_LLM_RESPONSE = json.dumps({
    "positive_signals": ["Strong Q3 results", "EV expansion plans"],
    "negative_signals": ["Oil price pressure on margins"],
    "score": 6.5,
    "summary": "Mildly positive sentiment driven by strong results and EV expansion, offset by oil pressure.",
})


# ── Tests ──────────────────────────────────────────────────────────


class TestAnalyzeSentiment:
    @patch("backend.agents.sentiment_agent._configure_genai")
    @patch("backend.agents.sentiment_agent.DuckDuckGoTool.search_news")
    def test_success(self, mock_news, mock_genai):
        mock_news.return_value = MOCK_NEWS_RESULT

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = MOCK_LLM_RESPONSE
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_sentiment("RELIANCE.NS")

        assert result["score"] == 6.5
        assert len(result["positive_signals"]) == 2
        assert len(result["negative_signals"]) == 1
        assert "sentiment" in result["summary"].lower()

        # Should strip .NS from search query
        call_args = mock_news.call_args
        assert ".NS" not in call_args[0][0]
        mock_model.generate_content.assert_called_once()
        logger.info("test_success passed – full sentiment analysis flow")

    @patch("backend.agents.sentiment_agent._configure_genai")
    @patch("backend.agents.sentiment_agent.DuckDuckGoTool.search_news")
    def test_no_news_found(self, mock_news, mock_genai):
        mock_news.return_value = {"query": "test", "count": 0, "results": []}

        result = analyze_sentiment("UNKNOWN.NS")

        assert result["score"] == 5.0  # Neutral default
        assert result["positive_signals"] == []
        assert result["negative_signals"] == []
        assert "neutral" in result["summary"].lower() or "no recent news" in result["summary"].lower()
        mock_genai.assert_not_called()  # No LLM call when no news
        logger.info("test_no_news_found passed – neutral on missing news")

    @patch("backend.agents.sentiment_agent._configure_genai")
    @patch("backend.agents.sentiment_agent.DuckDuckGoTool.search_news")
    def test_llm_failure(self, mock_news, mock_genai):
        mock_news.return_value = MOCK_NEWS_RESULT

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Gemini quota exceeded")
        mock_genai.return_value = mock_model

        result = analyze_sentiment("RELIANCE.NS")

        assert result["score"] == 5.0
        assert "failed" in result["summary"].lower()
        assert result["positive_signals"] == []
        logger.info("test_llm_failure passed – graceful fallback on Gemini error")

    @patch("backend.agents.sentiment_agent._configure_genai")
    @patch("backend.agents.sentiment_agent.DuckDuckGoTool.search_news")
    def test_score_clamped(self, mock_news, mock_genai):
        mock_news.return_value = MOCK_NEWS_RESULT

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "positive_signals": ["Everything great"],
            "negative_signals": [],
            "score": 12.0,  # Out of range
            "summary": "Extremely positive",
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        result = analyze_sentiment("X.NS")

        assert result["score"] == 10.0  # Clamped
        logger.info("test_score_clamped passed")

    @patch("backend.agents.sentiment_agent._configure_genai")
    @patch("backend.agents.sentiment_agent.DuckDuckGoTool.search_news")
    def test_custom_max_news(self, mock_news, mock_genai):
        mock_news.return_value = MOCK_NEWS_RESULT

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = MOCK_LLM_RESPONSE
        mock_model.generate_content.return_value = mock_response
        mock_genai.return_value = mock_model

        analyze_sentiment("TCS.NS", max_news=5)

        mock_news.assert_called_once()
        assert mock_news.call_args[1]["max_results"] == 5 or mock_news.call_args[0][1] == 5
        logger.info("test_custom_max_news passed")

    @patch("backend.agents.sentiment_agent._configure_genai")
    @patch("backend.agents.sentiment_agent.DuckDuckGoTool.search_news")
    def test_ticker_cleaning(self, mock_news, mock_genai):
        """Verifies .NS and .BO suffixes are stripped from search queries."""
        mock_news.return_value = {"query": "test", "count": 0, "results": []}

        analyze_sentiment("RELIANCE.BO")

        query = mock_news.call_args[0][0]
        assert ".BO" not in query
        assert "RELIANCE" in query
        logger.info("test_ticker_cleaning passed – .BO stripped from query")
