"""
Unit tests for backend.models.schemas – Pydantic request/response models.

All tests are pure Python, no LLM or API calls required.
"""

import logging

import pytest
from pydantic import ValidationError

from backend.models.schemas import (
    AnalysisResponse,
    AnalysisType,
    AnalyzeStockRequest,
    ChatRequest,
    CompareStocksRequest,
    ErrorResponse,
    FundamentalAnalysis,
    PortfolioRequest,
    Recommendation,
    SentimentAnalysis,
    StockAnalysis,
    TechnicalAnalysis,
)

logger = logging.getLogger("market_analyst.tests.test_schemas")


# ── Request model tests ───────────────────────────────────────────


class TestAnalyzeStockRequest:
    def test_valid(self):
        req = AnalyzeStockRequest(stock="RELIANCE.NS")
        assert req.stock == "RELIANCE.NS"
        logger.info("Valid AnalyzeStockRequest created")

    def test_empty_stock_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeStockRequest(stock="")
        assert "String should have at least 1 character" in str(exc_info.value)
        logger.info("Empty stock correctly rejected")

    def test_too_long_stock_rejected(self):
        with pytest.raises(ValidationError):
            AnalyzeStockRequest(stock="A" * 21)
        logger.info("Overly long stock ticker rejected")

    def test_missing_stock_rejected(self):
        with pytest.raises(ValidationError):
            AnalyzeStockRequest()  # type: ignore[call-arg]
        logger.info("Missing stock field rejected")


class TestCompareStocksRequest:
    def test_valid(self):
        req = CompareStocksRequest(stock_a="TATAMOTORS.NS", stock_b="M&M.NS")
        assert req.stock_a == "TATAMOTORS.NS"
        assert req.stock_b == "M&M.NS"
        logger.info("Valid CompareStocksRequest created")

    def test_empty_stock_a_rejected(self):
        with pytest.raises(ValidationError):
            CompareStocksRequest(stock_a="", stock_b="INFY.NS")
        logger.info("Empty stock_a rejected")

    def test_missing_stock_b_rejected(self):
        with pytest.raises(ValidationError):
            CompareStocksRequest(stock_a="TCS.NS")  # type: ignore[call-arg]
        logger.info("Missing stock_b rejected")


class TestPortfolioRequest:
    def test_valid(self):
        req = PortfolioRequest(stocks=["RELIANCE.NS", "TCS.NS", "INFY.NS"])
        assert len(req.stocks) == 3
        logger.info("Valid PortfolioRequest created")

    def test_empty_list_rejected(self):
        with pytest.raises(ValidationError):
            PortfolioRequest(stocks=[])
        logger.info("Empty portfolio rejected")

    def test_single_stock_portfolio(self):
        req = PortfolioRequest(stocks=["RELIANCE.NS"])
        assert len(req.stocks) == 1
        logger.info("Single-stock portfolio accepted")

    def test_too_many_stocks_rejected(self):
        with pytest.raises(ValidationError):
            PortfolioRequest(stocks=["S"] * 21)
        logger.info("Portfolio with >20 stocks rejected")


class TestChatRequest:
    def test_valid(self):
        req = ChatRequest(query="Compare Tata Motors and Mahindra")
        assert "Tata Motors" in req.query
        logger.info("Valid ChatRequest created")

    def test_empty_query_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(query="")
        logger.info("Empty query rejected")

    def test_too_long_query_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(query="x" * 501)
        logger.info("Overly long query rejected")


# ── Sub-model tests ───────────────────────────────────────────────


class TestFundamentalAnalysis:
    def test_defaults(self):
        fa = FundamentalAnalysis()
        assert fa.score == 0.0
        assert fa.pe_ratio is None
        assert fa.summary == ""
        logger.info("FundamentalAnalysis defaults OK")

    def test_score_bounds(self):
        fa = FundamentalAnalysis(score=10.0)
        assert fa.score == 10.0
        with pytest.raises(ValidationError):
            FundamentalAnalysis(score=11.0)
        with pytest.raises(ValidationError):
            FundamentalAnalysis(score=-1.0)
        logger.info("FundamentalAnalysis score bounds enforced")

    def test_full_creation(self):
        fa = FundamentalAnalysis(
            revenue="₹2.5T",
            pe_ratio=24.0,
            earnings_growth="8%",
            market_cap="₹18T",
            debt="moderate",
            profit_margin="11%",
            score=7.0,
            summary="Strong fundamentals",
        )
        assert fa.pe_ratio == 24.0
        assert fa.score == 7.0
        logger.info("Full FundamentalAnalysis created")


class TestTechnicalAnalysis:
    def test_defaults(self):
        ta = TechnicalAnalysis()
        assert ta.rsi is None
        assert ta.trend == ""
        assert ta.score == 0.0
        logger.info("TechnicalAnalysis defaults OK")

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            TechnicalAnalysis(score=10.5)
        logger.info("TechnicalAnalysis score bounds enforced")


class TestSentimentAnalysis:
    def test_defaults(self):
        sa = SentimentAnalysis()
        assert sa.positive_signals == []
        assert sa.negative_signals == []
        assert sa.score == 0.0
        logger.info("SentimentAnalysis defaults OK")

    def test_with_signals(self):
        sa = SentimentAnalysis(
            positive_signals=["EV expansion", "Record sales"],
            negative_signals=["Supply chain issues"],
            score=6.5,
            summary="Mildly positive",
        )
        assert len(sa.positive_signals) == 2
        assert len(sa.negative_signals) == 1
        logger.info("SentimentAnalysis with signals OK")


# ── Composite model tests ─────────────────────────────────────────


class TestStockAnalysis:
    def test_minimal(self):
        sa = StockAnalysis(stock="RELIANCE.NS")
        assert sa.stock == "RELIANCE.NS"
        assert sa.fundamental.score == 0.0
        assert sa.technical.score == 0.0
        assert sa.sentiment.score == 0.0
        logger.info("Minimal StockAnalysis OK")

    def test_full(self):
        sa = StockAnalysis(
            stock="TCS.NS",
            fundamental=FundamentalAnalysis(score=7.0, summary="Good"),
            technical=TechnicalAnalysis(score=8.0, trend="bullish"),
            sentiment=SentimentAnalysis(score=6.0, summary="Neutral"),
        )
        assert sa.fundamental.score == 7.0
        assert sa.technical.trend == "bullish"
        logger.info("Full StockAnalysis OK")


class TestAnalysisResponse:
    def test_defaults(self):
        resp = AnalysisResponse(analysis_type=AnalysisType.SINGLE)
        assert resp.recommendation == Recommendation.HOLD
        assert resp.stocks == []
        assert resp.reasoning == ""
        logger.info("AnalysisResponse defaults OK")

    def test_full_response(self):
        resp = AnalysisResponse(
            analysis_type=AnalysisType.COMPARE,
            stocks=[
                StockAnalysis(
                    stock="TATAMOTORS.NS",
                    fundamental=FundamentalAnalysis(score=6.0),
                    technical=TechnicalAnalysis(score=8.0),
                    sentiment=SentimentAnalysis(score=5.0),
                ),
                StockAnalysis(
                    stock="M&M.NS",
                    fundamental=FundamentalAnalysis(score=7.5),
                    technical=TechnicalAnalysis(score=6.0),
                    sentiment=SentimentAnalysis(score=6.0),
                ),
            ],
            recommendation=Recommendation.BUY,
            reasoning="Tata Motors has stronger technical momentum",
        )
        assert len(resp.stocks) == 2
        assert resp.recommendation == Recommendation.BUY
        assert resp.analysis_type == AnalysisType.COMPARE
        logger.info("Full AnalysisResponse OK")

    def test_serialization_roundtrip(self):
        """Model can be serialized to dict/JSON and back."""
        resp = AnalysisResponse(
            analysis_type=AnalysisType.SINGLE,
            stocks=[StockAnalysis(stock="INFY.NS")],
            recommendation=Recommendation.HOLD,
            reasoning="Awaiting quarterly results",
        )
        data = resp.model_dump()
        restored = AnalysisResponse(**data)
        assert restored.stocks[0].stock == "INFY.NS"
        assert restored.recommendation == Recommendation.HOLD
        logger.info("Serialization roundtrip OK")


class TestErrorResponse:
    def test_creation(self):
        err = ErrorResponse(error="Invalid ticker", detail="FOOBAR is not a valid NSE ticker")
        assert err.error == "Invalid ticker"
        assert "FOOBAR" in err.detail
        logger.info("ErrorResponse creation OK")

    def test_minimal(self):
        err = ErrorResponse(error="Server error")
        assert err.detail == ""
        logger.info("Minimal ErrorResponse OK")


# ── Enum tests ─────────────────────────────────────────────────────


class TestEnums:
    def test_recommendation_values(self):
        assert Recommendation.BUY.value == "BUY"
        assert Recommendation.HOLD.value == "HOLD"
        assert Recommendation.SELL.value == "SELL"
        logger.info("Recommendation enum values OK")

    def test_analysis_type_values(self):
        assert AnalysisType.SINGLE.value == "single"
        assert AnalysisType.COMPARE.value == "compare"
        assert AnalysisType.PORTFOLIO.value == "portfolio"
        logger.info("AnalysisType enum values OK")
