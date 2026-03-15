"""
Unit tests for backend.api.fastapi_server.

All LangGraph workflow calls are MOCKED – no real API/LLM calls are made.
Uses FastAPI TestClient for endpoint testing.
"""

import json
import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.api.fastapi_server import app, _build_response
from backend.models.schemas import AnalysisType

logger = logging.getLogger("market_analyst.tests.test_fastapi")

client = TestClient(app)


# ── Mock workflow results ─────────────────────────────────────────

MOCK_SINGLE_RESULT = {
    "query": "Analyze RELIANCE.NS",
    "stocks": ["RELIANCE.NS"],
    "analysis_type": "single",
    "fundamental_result": {
        "RELIANCE.NS": {
            "revenue": "₹2.5T",
            "pe_ratio": 24.5,
            "earnings_growth": "8%",
            "market_cap": "₹18T",
            "debt": "moderate",
            "profit_margin": "11%",
            "score": 7.0,
            "summary": "Strong fundamentals",
        },
    },
    "technical_result": {
        "RELIANCE.NS": {
            "rsi": 62.0,
            "macd": "bullish crossover",
            "ma50": 2400.0,
            "ma200": 2300.0,
            "trend": "bullish",
            "score": 8.0,
            "summary": "Strong momentum",
        },
    },
    "sentiment_result": {
        "RELIANCE.NS": {
            "positive_signals": ["Strong Q3"],
            "negative_signals": ["Oil pressure"],
            "score": 6.0,
            "summary": "Mildly positive",
        },
    },
    "recommendation": "BUY",
    "reasoning": "Strong across all dimensions",
}

MOCK_COMPARE_RESULT = {
    "query": "Compare TATAMOTORS.NS and M&M.NS",
    "stocks": ["TATAMOTORS.NS", "M&M.NS"],
    "analysis_type": "compare",
    "fundamental_result": {
        "TATAMOTORS.NS": {"score": 6.0, "summary": "Average"},
        "M&M.NS": {"score": 7.5, "summary": "Strong"},
    },
    "technical_result": {
        "TATAMOTORS.NS": {"score": 8.0, "trend": "bullish"},
        "M&M.NS": {"score": 6.0, "trend": "neutral"},
    },
    "sentiment_result": {
        "TATAMOTORS.NS": {"score": 5.5, "positive_signals": [], "negative_signals": []},
        "M&M.NS": {"score": 6.0, "positive_signals": ["SUV demand"], "negative_signals": []},
    },
    "recommendation": "BUY",
    "reasoning": "Tata Motors stronger technically",
}

MOCK_PORTFOLIO_RESULT = {
    "query": "Portfolio",
    "stocks": ["RELIANCE.NS", "TCS.NS", "INFY.NS"],
    "analysis_type": "portfolio",
    "fundamental_result": {
        "RELIANCE.NS": {"score": 7.0},
        "TCS.NS": {"score": 8.0},
        "INFY.NS": {"score": 6.0},
    },
    "technical_result": {
        "RELIANCE.NS": {"score": 7.5},
        "TCS.NS": {"score": 7.0},
        "INFY.NS": {"score": 5.0},
    },
    "sentiment_result": {
        "RELIANCE.NS": {"score": 6.0, "positive_signals": [], "negative_signals": []},
        "TCS.NS": {"score": 7.0, "positive_signals": [], "negative_signals": []},
        "INFY.NS": {"score": 5.0, "positive_signals": [], "negative_signals": []},
    },
    "recommendation": "HOLD",
    "reasoning": "Mixed signals across portfolio",
}


# ── Health Check ──────────────────────────────────────────────────


class TestHealthCheck:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        logger.info("test_health passed")


# ── POST /analyze_stock ──────────────────────────────────────────


class TestAnalyzeStock:
    @patch("backend.api.fastapi_server.run_single_stock_analysis")
    def test_success(self, mock_run):
        mock_run.return_value = MOCK_SINGLE_RESULT

        response = client.post("/analyze_stock", json={"stock": "RELIANCE.NS"})

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "single"
        assert len(data["stocks"]) == 1
        assert data["stocks"][0]["stock"] == "RELIANCE.NS"
        assert data["recommendation"] == "BUY"
        assert data["stocks"][0]["fundamental"]["score"] == 7.0
        assert data["stocks"][0]["technical"]["trend"] == "bullish"
        mock_run.assert_called_once_with("RELIANCE.NS")
        logger.info("test_success passed")

    def test_empty_stock_rejected(self):
        response = client.post("/analyze_stock", json={"stock": ""})
        assert response.status_code == 422
        logger.info("test_empty_stock_rejected passed")

    def test_missing_body(self):
        response = client.post("/analyze_stock", json={})
        assert response.status_code == 422
        logger.info("test_missing_body passed")

    @patch("backend.api.fastapi_server.run_single_stock_analysis")
    def test_workflow_error(self, mock_run):
        mock_run.side_effect = Exception("Workflow failed")

        response = client.post("/analyze_stock", json={"stock": "BAD.NS"})
        assert response.status_code == 500
        logger.info("test_workflow_error passed")


# ── POST /compare_stocks ─────────────────────────────────────────


class TestCompareStocks:
    @patch("backend.api.fastapi_server.run_compare_stocks")
    def test_success(self, mock_run):
        mock_run.return_value = MOCK_COMPARE_RESULT

        response = client.post("/compare_stocks", json={
            "stock_a": "TATAMOTORS.NS",
            "stock_b": "M&M.NS",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "compare"
        assert len(data["stocks"]) == 2
        mock_run.assert_called_once_with("TATAMOTORS.NS", "M&M.NS")
        logger.info("test_success passed")

    def test_missing_stock_b(self):
        response = client.post("/compare_stocks", json={"stock_a": "TCS.NS"})
        assert response.status_code == 422
        logger.info("test_missing_stock_b passed")


# ── POST /portfolio_analysis ─────────────────────────────────────


class TestPortfolioAnalysis:
    @patch("backend.api.fastapi_server.run_portfolio_analysis")
    def test_success(self, mock_run):
        mock_run.return_value = MOCK_PORTFOLIO_RESULT

        response = client.post("/portfolio_analysis", json={
            "stocks": ["RELIANCE.NS", "TCS.NS", "INFY.NS"],
        })

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "portfolio"
        assert len(data["stocks"]) == 3
        assert data["recommendation"] == "HOLD"
        logger.info("test_success passed")

    def test_empty_portfolio_rejected(self):
        response = client.post("/portfolio_analysis", json={"stocks": []})
        assert response.status_code == 422
        logger.info("test_empty_portfolio_rejected passed")


# ── POST /parse_intent ────────────────────────────────────────────


class TestParseIntent:
    @patch("backend.api.fastapi_server.parse_intent_cached")
    def test_success(self, mock_parse):
        mock_parse.return_value = {
            "stocks": ["RELIANCE.NS"],
            "analysis_type": "single",
            "parsed_query": "Analyze Reliance",
        }

        response = client.post("/parse_intent", json={
            "query": "How is Reliance doing?",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["stocks"] == ["RELIANCE.NS"]
        assert data["analysis_type"] == "single"
        assert data["parsed_query"] == "Analyze Reliance"
        mock_parse.assert_called_once_with("How is Reliance doing?")
        logger.info("test_success passed")

    @patch("backend.api.fastapi_server.parse_intent_cached")
    def test_compare_intent(self, mock_parse):
        mock_parse.return_value = {
            "stocks": ["TCS.NS", "INFY.NS"],
            "analysis_type": "compare",
            "parsed_query": "Compare TCS and Infosys",
        }

        response = client.post("/parse_intent", json={
            "query": "Compare TCS and Infosys",
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["stocks"]) == 2
        assert data["analysis_type"] == "compare"
        logger.info("test_compare_intent passed")

    @patch("backend.api.fastapi_server.parse_intent_cached")
    def test_no_stocks_detected(self, mock_parse):
        mock_parse.return_value = {
            "stocks": [],
            "analysis_type": "single",
            "parsed_query": "What is the market like?",
        }

        response = client.post("/parse_intent", json={
            "query": "What is the market like?",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["stocks"] == []
        logger.info("test_no_stocks_detected passed")

    def test_empty_query_rejected(self):
        response = client.post("/parse_intent", json={"query": ""})
        assert response.status_code == 422
        logger.info("test_empty_query_rejected passed")


# ── POST /chat ────────────────────────────────────────────────────


class TestChat:
    @patch("backend.api.fastapi_server.run_analysis")
    def test_success(self, mock_run):
        mock_run.return_value = MOCK_SINGLE_RESULT

        response = client.post("/chat", json={
            "query": "How is Reliance doing?",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"] == "BUY"
        mock_run.assert_called_once_with("How is Reliance doing?")
        logger.info("test_success passed")

    def test_empty_query_rejected(self):
        response = client.post("/chat", json={"query": ""})
        assert response.status_code == 422
        logger.info("test_empty_query_rejected passed")


# ── Response Builder ──────────────────────────────────────────────


class TestBuildResponse:
    def test_single_stock(self):
        response = _build_response(MOCK_SINGLE_RESULT, AnalysisType.SINGLE)

        assert response.analysis_type == AnalysisType.SINGLE
        assert len(response.stocks) == 1
        assert response.recommendation.value == "BUY"
        assert response.stocks[0].fundamental.score == 7.0
        logger.info("test_single_stock passed")

    def test_empty_result(self):
        response = _build_response(
            {"stocks": [], "recommendation": "HOLD", "reasoning": ""},
            AnalysisType.SINGLE,
        )
        assert len(response.stocks) == 0
        assert response.recommendation.value == "HOLD"
        logger.info("test_empty_result passed")

    def test_invalid_recommendation_defaults(self):
        result = {**MOCK_SINGLE_RESULT, "recommendation": "MAYBE"}
        response = _build_response(result, AnalysisType.SINGLE)

        assert response.recommendation == Recommendation.HOLD
        logger.info("test_invalid_recommendation_defaults passed")


from backend.models.schemas import Recommendation
