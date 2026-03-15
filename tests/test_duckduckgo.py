"""
Unit tests for backend.tools.duckduckgo_tool.

All DuckDuckGo API calls are MOCKED – no real network requests are made.
"""

import logging
from unittest.mock import MagicMock, patch

from backend.tools.duckduckgo_tool import DuckDuckGoTool

logger = logging.getLogger("market_analyst.tests.test_duckduckgo")


# ── Helpers ────────────────────────────────────────────────────────


def _make_news_results() -> list[dict]:
    """Create sample DDGS news results."""
    return [
        {
            "title": "Reliance Q3 Results Beat Estimates",
            "body": "Reliance Industries reported strong quarterly numbers...",
            "url": "https://example.com/reliance-q3",
            "date": "2024-01-15",
            "source": "Economic Times",
        },
        {
            "title": "Reliance Expands EV Plans",
            "body": "The conglomerate announced new EV battery investments...",
            "url": "https://example.com/reliance-ev",
            "date": "2024-01-14",
            "source": "Mint",
        },
        {
            "title": "Oil Prices Impact Reliance Margins",
            "body": "Rising crude oil prices may affect refining margins...",
            "url": "https://example.com/reliance-oil",
            "date": "2024-01-13",
            "source": "Business Standard",
        },
    ]


def _make_web_results() -> list[dict]:
    """Create sample DDGS web search results."""
    return [
        {
            "title": "Reliance Industries - Wikipedia",
            "body": "Reliance Industries Limited is an Indian conglomerate...",
            "href": "https://en.wikipedia.org/wiki/Reliance_Industries",
        },
        {
            "title": "RELIANCE.NS Stock Price - Yahoo Finance",
            "body": "View the latest Reliance Industries stock price...",
            "href": "https://finance.yahoo.com/quote/RELIANCE.NS",
        },
    ]


# ── News Search Tests ─────────────────────────────────────────────


class TestSearchNews:
    @patch("backend.tools.duckduckgo_tool.DDGS")
    def test_success(self, mock_ddgs_cls):
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.news.return_value = _make_news_results()
        mock_ddgs_cls.return_value = mock_ddgs

        result = DuckDuckGoTool.search_news("Reliance Industries news")

        assert result["query"] == "Reliance Industries news"
        assert result["count"] == 3
        assert len(result["results"]) == 3
        assert "error" not in result

        # Verify article structure
        article = result["results"][0]
        assert article["title"] == "Reliance Q3 Results Beat Estimates"
        assert article["source"] == "Economic Times"
        assert "snippet" in article
        assert "url" in article
        assert "date" in article

        mock_ddgs.news.assert_called_once_with(
            "Reliance Industries news", max_results=10
        )
        logger.info("test_success passed – news results parsed correctly")

    @patch("backend.tools.duckduckgo_tool.DDGS")
    def test_custom_max_results(self, mock_ddgs_cls):
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.news.return_value = _make_news_results()[:1]
        mock_ddgs_cls.return_value = mock_ddgs

        result = DuckDuckGoTool.search_news("TCS news", max_results=1)

        assert result["count"] == 1
        mock_ddgs.news.assert_called_once_with("TCS news", max_results=1)
        logger.info("test_custom_max_results passed")

    @patch("backend.tools.duckduckgo_tool.DDGS")
    def test_empty_results(self, mock_ddgs_cls):
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.news.return_value = []
        mock_ddgs_cls.return_value = mock_ddgs

        result = DuckDuckGoTool.search_news("obscure unknown company xyz")

        assert result["count"] == 0
        assert result["results"] == []
        assert "error" not in result
        logger.info("test_empty_results passed – empty set handled")

    @patch("backend.tools.duckduckgo_tool.DDGS")
    def test_exception_handling(self, mock_ddgs_cls):
        mock_ddgs_cls.side_effect = Exception("Rate limit exceeded")

        result = DuckDuckGoTool.search_news("any query")

        assert result["count"] == 0
        assert result["results"] == []
        assert "error" in result
        assert "Rate limit exceeded" in result["error"]
        logger.info("test_exception_handling passed – exception caught")

    @patch("backend.tools.duckduckgo_tool.DDGS")
    def test_missing_fields_in_results(self, mock_ddgs_cls):
        """Handles results where some fields are missing."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.news.return_value = [{"title": "Only Title"}]
        mock_ddgs_cls.return_value = mock_ddgs

        result = DuckDuckGoTool.search_news("partial data")

        assert result["count"] == 1
        article = result["results"][0]
        assert article["title"] == "Only Title"
        assert article["snippet"] == ""
        assert article["url"] == ""
        assert article["date"] == ""
        assert article["source"] == ""
        logger.info("test_missing_fields_in_results passed – defaults applied")


# ── Web Search Tests ──────────────────────────────────────────────


class TestSearchWeb:
    @patch("backend.tools.duckduckgo_tool.DDGS")
    def test_success(self, mock_ddgs_cls):
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = _make_web_results()
        mock_ddgs_cls.return_value = mock_ddgs

        result = DuckDuckGoTool.search_web("Reliance Industries")

        assert result["query"] == "Reliance Industries"
        assert result["count"] == 2
        assert len(result["results"]) == 2
        assert "error" not in result

        item = result["results"][0]
        assert item["title"] == "Reliance Industries - Wikipedia"
        assert "snippet" in item
        assert "url" in item

        mock_ddgs.text.assert_called_once_with(
            "Reliance Industries", max_results=10
        )
        logger.info("test_success passed – web results parsed correctly")

    @patch("backend.tools.duckduckgo_tool.DDGS")
    def test_empty_results(self, mock_ddgs_cls):
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = []
        mock_ddgs_cls.return_value = mock_ddgs

        result = DuckDuckGoTool.search_web("zzzznonexistent")

        assert result["count"] == 0
        assert result["results"] == []
        logger.info("test_empty_results passed")

    @patch("backend.tools.duckduckgo_tool.DDGS")
    def test_exception_handling(self, mock_ddgs_cls):
        mock_ddgs_cls.side_effect = Exception("Connection refused")

        result = DuckDuckGoTool.search_web("anything")

        assert "error" in result
        assert result["count"] == 0
        logger.info("test_exception_handling passed")
