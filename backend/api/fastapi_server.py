"""
FastAPI Backend – API Gateway for the AI Market Analyst.

Provides REST endpoints for stock analysis, comparison, portfolio review,
and free-form chat. Wires into the LangGraph orchestration layer.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import logger as root_logger
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
from backend.workflows.market_graph import (
    run_analysis,
    run_compare_stocks,
    run_portfolio_analysis,
    run_single_stock_analysis,
)
from backend.tools.sqlite_mcp_tool import SQLiteMCPTool

logger = logging.getLogger("market_analyst.api.server")


# ── Lifespan ──────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI server starting up")
    await SQLiteMCPTool.initialize()
    yield
    await SQLiteMCPTool.shutdown()
    logger.info("FastAPI server shutting down")


# ── App Setup ─────────────────────────────────────────────────────


app = FastAPI(
    title="AI Market Analyst",
    description="Multi-agent AI system for stock market analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS – allow Streamlit and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Error Handling ────────────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
        ).model_dump(),
    )


# ── Helper: Convert graph result → AnalysisResponse ──────────────


def _build_response(result: dict, analysis_type: AnalysisType) -> AnalysisResponse:
    """Convert raw LangGraph output into a structured AnalysisResponse."""
    logger.info("Building response from graph result")

    stocks_analysis = []
    stock_list = result.get("stocks", [])
    fundamental_all = result.get("fundamental_result", {})
    technical_all = result.get("technical_result", {})
    sentiment_all = result.get("sentiment_result", {})

    for ticker in stock_list:
        f_data = fundamental_all.get(ticker, {})
        t_data = technical_all.get(ticker, {})
        s_data = sentiment_all.get(ticker, {})

        stocks_analysis.append(
            StockAnalysis(
                stock=ticker,
                fundamental=FundamentalAnalysis(
                    revenue=str(f_data.get("revenue", "")),
                    pe_ratio=f_data.get("pe_ratio"),
                    earnings_growth=str(f_data.get("earnings_growth", "")),
                    market_cap=str(f_data.get("market_cap", "")),
                    debt=str(f_data.get("debt", "")),
                    profit_margin=str(f_data.get("profit_margin", "")),
                    score=float(f_data.get("score", 0)),
                    summary=str(f_data.get("summary", "")),
                ),
                technical=TechnicalAnalysis(
                    rsi=t_data.get("rsi"),
                    macd=str(t_data.get("macd", "")),
                    ma50=t_data.get("ma50"),
                    ma200=t_data.get("ma200"),
                    trend=str(t_data.get("trend", "")),
                    score=float(t_data.get("score", 0)),
                    summary=str(t_data.get("summary", "")),
                ),
                sentiment=SentimentAnalysis(
                    positive_signals=list(s_data.get("positive_signals", [])),
                    negative_signals=list(s_data.get("negative_signals", [])),
                    score=float(s_data.get("score", 0)),
                    summary=str(s_data.get("summary", "")),
                ),
            )
        )

    rec_str = result.get("recommendation", "HOLD").upper()
    try:
        recommendation = Recommendation(rec_str)
    except ValueError:
        recommendation = Recommendation.HOLD

    response = AnalysisResponse(
        analysis_type=analysis_type,
        stocks=stocks_analysis,
        recommendation=recommendation,
        reasoning=result.get("reasoning", ""),
    )

    logger.info("Response built: type=%s, stocks=%d, rec=%s",
                analysis_type.value, len(stocks_analysis), recommendation.value)
    return response


# ── Endpoints ─────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "healthy", "service": "market-analyst-ai"}


@app.post("/analyze_stock", response_model=AnalysisResponse)
async def analyze_stock(request: AnalyzeStockRequest):
    """Analyze a single stock."""
    logger.info("POST /analyze_stock – ticker=%s", request.stock)

    try:
        result = await run_single_stock_analysis(request.stock)
        return _build_response(result, AnalysisType.SINGLE)
    except Exception as e:
        logger.error("Error analyzing stock %s: %s", request.stock, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare_stocks", response_model=AnalysisResponse)
async def compare_stocks(request: CompareStocksRequest):
    """Compare two stocks head-to-head."""
    logger.info("POST /compare_stocks – %s vs %s", request.stock_a, request.stock_b)

    try:
        result = await run_compare_stocks(request.stock_a, request.stock_b)
        return _build_response(result, AnalysisType.COMPARE)
    except Exception as e:
        logger.error("Error comparing stocks: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio_analysis", response_model=AnalysisResponse)
async def portfolio_analysis(request: PortfolioRequest):
    """Analyze a portfolio of stocks."""
    logger.info("POST /portfolio_analysis – stocks=%s", request.stocks)

    try:
        result = await run_portfolio_analysis(request.stocks)
        return _build_response(result, AnalysisType.PORTFOLIO)
    except Exception as e:
        logger.error("Error analyzing portfolio: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=AnalysisResponse)
async def chat(request: ChatRequest):
    """Free-form market question."""
    logger.info("POST /chat – query=%r", request.query)

    try:
        result = await run_analysis(request.query)

        # Determine type from result
        analysis_type_str = result.get("analysis_type", "single")
        try:
            analysis_type = AnalysisType(analysis_type_str)
        except ValueError:
            analysis_type = AnalysisType.SINGLE

        return _build_response(result, analysis_type)
    except Exception as e:
        logger.error("Error processing chat: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
