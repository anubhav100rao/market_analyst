"""
Yahoo Finance Tool – Fetches stock data from Yahoo Finance.

Provides:
  - Price history (configurable period)
  - Financial statements (income, balance sheet, cash flow)
  - Key ratios (PE, market cap, profit margin, debt)
"""

from __future__ import annotations

import logging
from typing import Any

import yfinance as yf

from backend.tools.sqlite_mcp_tool import SQLiteMCPTool

logger = logging.getLogger("market_analyst.tools.yahoo_finance")


class YahooFinanceTool:
    """Wrapper around yfinance for structured stock data retrieval."""

    # ── Price History ──────────────────────────────────────────────

    @staticmethod
    async def get_price_history(
        ticker: str,
        period: str = "1y",
    ) -> dict[str, Any]:
        """
        Fetch historical price data for a ticker.

        Args:
            ticker: Stock symbol, e.g. "RELIANCE.NS"
            period: Data period – "1mo", "3mo", "6mo", "1y", "5y", "max"

        Returns:
            dict with keys: ticker, period, data (list of OHLCV dicts), count
        """
        logger.info("Fetching price history for %s, period=%s", ticker, period)
        cache_key = f"{ticker}_{period}"
        cached = await SQLiteMCPTool.get_cache("yahoo_finance_history", cache_key)
        if cached:
            return cached

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)

            if hist.empty:
                logger.warning("No price data returned for %s", ticker)
                return {
                    "ticker": ticker,
                    "period": period,
                    "data": [],
                    "count": 0,
                    "error": f"No price data found for ticker '{ticker}'",
                }

            records = []
            for date, row in hist.iterrows():
                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]),
                })

            logger.info(
                "Retrieved %d price records for %s", len(records), ticker
            )
            result = {
                "ticker": ticker,
                "period": period,
                "data": records,
                "count": len(records),
            }
            await SQLiteMCPTool.set_cache("yahoo_finance_history", cache_key, result)
            return result

        except Exception as e:
            logger.error("Error fetching price history for %s: %s", ticker, e)
            return {
                "ticker": ticker,
                "period": period,
                "data": [],
                "count": 0,
                "error": str(e),
            }

    # ── Financial Statements ──────────────────────────────────────

    @staticmethod
    async def get_financial_statements(ticker: str) -> dict[str, Any]:
        """
        Fetch income statement, balance sheet, and cash flow.

        Returns:
            dict with keys: ticker, income_statement, balance_sheet, cash_flow
            Each value is a list of dicts (one per period).
        """
        logger.info("Fetching financial statements for %s", ticker)
        
        cached = await SQLiteMCPTool.get_cache("yahoo_finance_financials", ticker)
        if cached:
            return cached

        try:
            stock = yf.Ticker(ticker)

            def _df_to_records(df) -> list[dict]:
                if df is None or df.empty:
                    return []
                result = []
                for col in df.columns:
                    period_data = {"period": col.strftime("%Y-%m-%d")}
                    for idx in df.index:
                        val = df.loc[idx, col]
                        period_data[str(idx)] = (
                            float(val) if val is not None and str(val) != "nan" else None
                        )
                    result.append(period_data)
                return result

            income = _df_to_records(stock.income_stmt)
            balance = _df_to_records(stock.balance_sheet)
            cashflow = _df_to_records(stock.cashflow)

            logger.info(
                "Financial statements for %s: income=%d, balance=%d, cashflow=%d periods",
                ticker, len(income), len(balance), len(cashflow),
            )

            result = {
                "ticker": ticker,
                "income_statement": income,
                "balance_sheet": balance,
                "cash_flow": cashflow,
            }
            await SQLiteMCPTool.set_cache("yahoo_finance_financials", ticker, result)
            return result

        except Exception as e:
            logger.error("Error fetching financials for %s: %s", ticker, e)
            return {
                "ticker": ticker,
                "income_statement": [],
                "balance_sheet": [],
                "cash_flow": [],
                "error": str(e),
            }

    # ── Key Ratios ────────────────────────────────────────────────

    @staticmethod
    async def get_key_ratios(ticker: str) -> dict[str, Any]:
        """
        Fetch key financial ratios and metrics.

        Returns dict with: ticker, pe_ratio, market_cap, profit_margin,
                           debt_to_equity, revenue, earnings_growth
        """
        logger.info("Fetching key ratios for %s", ticker)
        
        cached = await SQLiteMCPTool.get_cache("yahoo_finance_ratios", ticker)
        if cached:
            return cached

        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}

            ratios = {
                "ticker": ticker,
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "market_cap": info.get("marketCap"),
                "profit_margin": info.get("profitMargins"),
                "debt_to_equity": info.get("debtToEquity"),
                "revenue": info.get("totalRevenue"),
                "earnings_growth": info.get("earningsGrowth"),
                "revenue_growth": info.get("revenueGrowth"),
                "current_price": info.get("currentPrice"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "company_name": info.get("longName", info.get("shortName", ticker)),
            }

            logger.info(
                "Key ratios for %s: PE=%.2f, MarketCap=%s",
                ticker,
                ratios["pe_ratio"] or 0,
                ratios["market_cap"],
            )
            await SQLiteMCPTool.set_cache("yahoo_finance_ratios", ticker, ratios)
            return ratios

        except Exception as e:
            logger.error("Error fetching key ratios for %s: %s", ticker, e)
            return {
                "ticker": ticker,
                "pe_ratio": None,
                "forward_pe": None,
                "market_cap": None,
                "profit_margin": None,
                "debt_to_equity": None,
                "revenue": None,
                "earnings_growth": None,
                "revenue_growth": None,
                "current_price": None,
                "fifty_two_week_high": None,
                "fifty_two_week_low": None,
                "company_name": ticker,
                "error": str(e),
            }
