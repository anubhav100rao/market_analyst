"""
Unit tests for backend.tools.yahoo_finance_tool.

All external yfinance calls are MOCKED – no real API calls are made.
"""

import logging
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from backend.tools.yahoo_finance_tool import YahooFinanceTool

logger = logging.getLogger("market_analyst.tests.test_yahoo_finance")


# ── Helpers ────────────────────────────────────────────────────────


def _make_price_dataframe() -> pd.DataFrame:
    """Create a realistic price history DataFrame."""
    dates = pd.date_range("2024-01-01", periods=5, freq="B")
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "High": [105.0, 106.0, 107.0, 108.0, 109.0],
            "Low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "Close": [104.0, 105.0, 106.0, 107.0, 108.0],
            "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
        },
        index=dates,
    )


def _make_financial_dataframe() -> pd.DataFrame:
    """Create a realistic financial statement DataFrame."""
    dates = pd.to_datetime(["2023-03-31", "2022-03-31"])
    return pd.DataFrame(
        {
            dates[0]: [5000000, 3000000, 2000000],
            dates[1]: [4500000, 2800000, 1700000],
        },
        index=["Total Revenue", "Cost Of Revenue", "Gross Profit"],
    )


def _make_stock_info() -> dict:
    """Create a realistic stock info dict."""
    return {
        "trailingPE": 24.5,
        "forwardPE": 20.0,
        "marketCap": 18000000000000,
        "profitMargins": 0.11,
        "debtToEquity": 45.0,
        "totalRevenue": 2500000000000,
        "earningsGrowth": 0.08,
        "revenueGrowth": 0.12,
        "currentPrice": 2450.0,
        "fiftyTwoWeekHigh": 2800.0,
        "fiftyTwoWeekLow": 2100.0,
        "longName": "Reliance Industries Limited",
    }


# ── Price History Tests ────────────────────────────────────────────


class TestGetPriceHistory:
    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_success(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _make_price_dataframe()
        mock_ticker_cls.return_value = mock_ticker

        result = YahooFinanceTool.get_price_history("RELIANCE.NS", period="1y")

        assert result["ticker"] == "RELIANCE.NS"
        assert result["period"] == "1y"
        assert result["count"] == 5
        assert len(result["data"]) == 5
        assert "error" not in result

        # Verify OHLCV structure
        first = result["data"][0]
        assert "date" in first
        assert "open" in first
        assert "high" in first
        assert "low" in first
        assert "close" in first
        assert "volume" in first
        assert first["close"] == 104.0

        mock_ticker_cls.assert_called_once_with("RELIANCE.NS")
        mock_ticker.history.assert_called_once_with(period="1y")
        logger.info("test_success passed – price history returned correctly")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_empty_data(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_ticker

        result = YahooFinanceTool.get_price_history("INVALID.NS")

        assert result["count"] == 0
        assert result["data"] == []
        assert "error" in result
        assert "No price data" in result["error"]
        logger.info("test_empty_data passed – empty data handled gracefully")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_exception_handling(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("Network timeout")

        result = YahooFinanceTool.get_price_history("RELIANCE.NS")

        assert result["count"] == 0
        assert result["data"] == []
        assert "error" in result
        assert "Network timeout" in result["error"]
        logger.info("test_exception_handling passed – exception caught cleanly")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_custom_period(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = _make_price_dataframe()
        mock_ticker_cls.return_value = mock_ticker

        YahooFinanceTool.get_price_history("TCS.NS", period="3mo")

        mock_ticker.history.assert_called_once_with(period="3mo")
        logger.info("test_custom_period passed – period forwarded correctly")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_values_rounded(self, mock_ticker_cls):
        """Prices should be rounded to 2 decimal places."""
        dates = pd.date_range("2024-01-01", periods=1, freq="B")
        df = pd.DataFrame(
            {"Open": [100.123456], "High": [105.999], "Low": [99.001], "Close": [104.555], "Volume": [1000]},
            index=dates,
        )
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = df
        mock_ticker_cls.return_value = mock_ticker

        result = YahooFinanceTool.get_price_history("X.NS")
        rec = result["data"][0]
        assert rec["open"] == 100.12
        assert rec["high"] == 106.0
        assert rec["low"] == 99.0
        assert rec["close"] == 104.56
        logger.info("test_values_rounded passed")


# ── Financial Statements Tests ─────────────────────────────────────


class TestGetFinancialStatements:
    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_success(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.income_stmt = _make_financial_dataframe()
        mock_ticker.balance_sheet = _make_financial_dataframe()
        mock_ticker.cashflow = _make_financial_dataframe()
        mock_ticker_cls.return_value = mock_ticker

        result = YahooFinanceTool.get_financial_statements("RELIANCE.NS")

        assert result["ticker"] == "RELIANCE.NS"
        assert len(result["income_statement"]) == 2
        assert len(result["balance_sheet"]) == 2
        assert len(result["cash_flow"]) == 2
        assert "error" not in result

        # Each period should have a "period" key
        assert "period" in result["income_statement"][0]
        logger.info("test_success passed – financial statements parsed correctly")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_empty_statements(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.income_stmt = pd.DataFrame()
        mock_ticker.balance_sheet = pd.DataFrame()
        mock_ticker.cashflow = pd.DataFrame()
        mock_ticker_cls.return_value = mock_ticker

        result = YahooFinanceTool.get_financial_statements("INVALID.NS")

        assert result["income_statement"] == []
        assert result["balance_sheet"] == []
        assert result["cash_flow"] == []
        logger.info("test_empty_statements passed")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_exception_handling(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("API error")

        result = YahooFinanceTool.get_financial_statements("RELIANCE.NS")

        assert "error" in result
        assert "API error" in result["error"]
        assert result["income_statement"] == []
        logger.info("test_exception_handling passed")


# ── Key Ratios Tests ──────────────────────────────────────────────


class TestGetKeyRatios:
    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_success(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = _make_stock_info()
        mock_ticker_cls.return_value = mock_ticker

        result = YahooFinanceTool.get_key_ratios("RELIANCE.NS")

        assert result["ticker"] == "RELIANCE.NS"
        assert result["pe_ratio"] == 24.5
        assert result["forward_pe"] == 20.0
        assert result["market_cap"] == 18000000000000
        assert result["profit_margin"] == 0.11
        assert result["debt_to_equity"] == 45.0
        assert result["company_name"] == "Reliance Industries Limited"
        assert "error" not in result
        logger.info("test_success passed – key ratios extracted correctly")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_missing_fields(self, mock_ticker_cls):
        """Gracefully handles when some info fields are missing."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"currentPrice": 100.0}  # minimal info
        mock_ticker_cls.return_value = mock_ticker

        result = YahooFinanceTool.get_key_ratios("TCS.NS")

        assert result["ticker"] == "TCS.NS"
        assert result["current_price"] == 100.0
        assert result["pe_ratio"] is None
        assert result["market_cap"] is None
        logger.info("test_missing_fields passed – None used for absent keys")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_empty_info(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        mock_ticker_cls.return_value = mock_ticker

        result = YahooFinanceTool.get_key_ratios("X.NS")

        assert result["pe_ratio"] is None
        assert result["company_name"] == "X.NS"  # fallback to ticker
        logger.info("test_empty_info passed")

    @patch("backend.tools.yahoo_finance_tool.yf.Ticker")
    def test_exception_handling(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("Ticker not found")

        result = YahooFinanceTool.get_key_ratios("INVALID")

        assert "error" in result
        assert result["pe_ratio"] is None
        assert result["company_name"] == "INVALID"
        logger.info("test_exception_handling passed")
