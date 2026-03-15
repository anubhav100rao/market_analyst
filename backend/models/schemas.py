"""
Pydantic request / response schemas for the FastAPI endpoints.

Validation, serialisation, and OpenAPI docs are all driven by these models.
"""

from __future__ import annotations

import logging
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger("market_analyst.models.schemas")


# ── Enums ──────────────────────────────────────────────────────────


class Recommendation(str, Enum):
    """Possible final recommendations."""

    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class AnalysisType(str, Enum):
    """Types of analysis the system supports."""

    SINGLE = "single"
    COMPARE = "compare"
    PORTFOLIO = "portfolio"


# ── Requests ───────────────────────────────────────────────────────


class AnalyzeStockRequest(BaseModel):
    """POST /analyze_stock"""

    stock: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Stock ticker symbol, e.g. 'RELIANCE.NS'",
        examples=["RELIANCE.NS", "TCS.NS"],
    )


class CompareStocksRequest(BaseModel):
    """POST /compare_stocks"""

    stock_a: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="First stock ticker",
        examples=["TATAMOTORS.NS"],
    )
    stock_b: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Second stock ticker",
        examples=["M&M.NS"],
    )


class PortfolioRequest(BaseModel):
    """POST /portfolio_analysis"""

    stocks: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of stock tickers in the portfolio",
        examples=[["RELIANCE.NS", "TCS.NS", "INFY.NS"]],
    )


class ChatRequest(BaseModel):
    """POST /chat – free-form query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural-language market question",
        examples=["Compare Tata Motors and Mahindra"],
    )


# ── Sub-responses ──────────────────────────────────────────────────


class FundamentalAnalysis(BaseModel):
    """Fundamental analysis section of the response."""

    revenue: str = ""
    pe_ratio: float | None = None
    earnings_growth: str = ""
    market_cap: str = ""
    debt: str = ""
    profit_margin: str = ""
    score: float = Field(0.0, ge=0, le=10)
    summary: str = ""


class TechnicalAnalysis(BaseModel):
    """Technical analysis section of the response."""

    rsi: float | None = None
    macd: str = ""
    ma50: float | None = None
    ma200: float | None = None
    trend: str = ""
    score: float = Field(0.0, ge=0, le=10)
    summary: str = ""


class SentimentAnalysis(BaseModel):
    """Sentiment analysis section of the response."""

    positive_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)
    score: float = Field(0.0, ge=0, le=10)
    summary: str = ""


class StockAnalysis(BaseModel):
    """Combined analysis for one stock."""

    stock: str
    fundamental: FundamentalAnalysis = Field(default_factory=FundamentalAnalysis)
    technical: TechnicalAnalysis = Field(default_factory=TechnicalAnalysis)
    sentiment: SentimentAnalysis = Field(default_factory=SentimentAnalysis)


# ── Top-level response ────────────────────────────────────────────


class AnalysisResponse(BaseModel):
    """Unified response returned by all analysis endpoints."""

    analysis_type: AnalysisType
    stocks: list[StockAnalysis] = Field(default_factory=list)
    recommendation: Recommendation = Recommendation.HOLD
    reasoning: str = ""


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
    detail: str = ""


logger.info("Pydantic schemas loaded")
