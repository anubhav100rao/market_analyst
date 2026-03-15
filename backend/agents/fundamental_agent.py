"""
Fundamental Analyst Agent – Analyzes company financials.

Uses Yahoo Finance tools to fetch financial data, then calls Gemini
to produce a structured fundamental analysis with a score (0–10).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import google.generativeai as genai

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.tools.yahoo_finance_tool import YahooFinanceTool

logger = logging.getLogger("market_analyst.agents.fundamental")

# ── Prompt Template ────────────────────────────────────────────────

FUNDAMENTAL_PROMPT = """You are a senior fundamental analyst. Analyze the following financial data and provide a structured assessment.

**Stock:** {ticker}

**Key Financial Ratios:**
{ratios_json}

**Financial Statements (summary):**
{financials_json}

Provide your analysis in the following JSON format ONLY (no markdown, no extra text):
{{
    "revenue": "<revenue figure as string>",
    "pe_ratio": <PE ratio as number or null>,
    "earnings_growth": "<earnings growth as string>",
    "market_cap": "<market cap as string>",
    "debt": "<debt assessment: low/moderate/high>",
    "profit_margin": "<profit margin as string>",
    "score": <score from 0 to 10 as number>,
    "summary": "<2-3 sentence summary of fundamental health>"
}}
"""


def _configure_genai() -> genai.GenerativeModel:
    """Configure and return a Gemini model instance."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    logger.info("Gemini model configured: %s", GEMINI_MODEL)
    return model


def _parse_llm_response(text: str) -> dict[str, Any]:
    """Parse LLM JSON response, handling potential markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (``` markers)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def analyze_fundamental(ticker: str) -> dict[str, Any]:
    """
    Run fundamental analysis for a single stock ticker.

    Args:
        ticker: Stock symbol, e.g. "RELIANCE.NS"

    Returns:
        FundamentalResult dict with score and analysis fields.
    """
    logger.info("Starting fundamental analysis for %s", ticker)

    # 1. Fetch data via tools
    logger.info("Fetching key ratios for %s", ticker)
    ratios = YahooFinanceTool.get_key_ratios(ticker)

    logger.info("Fetching financial statements for %s", ticker)
    financials = YahooFinanceTool.get_financial_statements(ticker)

    # 2. Check for data errors
    if "error" in ratios and "error" in financials:
        logger.error("Failed to fetch any data for %s", ticker)
        return {
            "revenue": "N/A",
            "pe_ratio": None,
            "earnings_growth": "N/A",
            "market_cap": "N/A",
            "debt": "N/A",
            "profit_margin": "N/A",
            "score": 0.0,
            "summary": f"Unable to analyze {ticker}: data unavailable.",
        }

    # 3. Build prompt
    prompt = FUNDAMENTAL_PROMPT.format(
        ticker=ticker,
        ratios_json=json.dumps(ratios, indent=2, default=str),
        financials_json=json.dumps(
            {
                "income_statement_periods": len(financials.get("income_statement", [])),
                "balance_sheet_periods": len(financials.get("balance_sheet", [])),
                "cash_flow_periods": len(financials.get("cash_flow", [])),
                "latest_income": financials.get("income_statement", [{}])[0] if financials.get("income_statement") else {},
            },
            indent=2,
            default=str,
        ),
    )
    logger.debug("Fundamental prompt for %s: %s", ticker, prompt[:200])

    # 4. Call LLM
    try:
        model = _configure_genai()
        logger.info("Calling Gemini for fundamental analysis of %s", ticker)
        response = model.generate_content(prompt)
        raw_text = response.text
        logger.info("Gemini response received for %s (%d chars)", ticker, len(raw_text))

        result = _parse_llm_response(raw_text)

        # Clamp score to [0, 10]
        result["score"] = max(0.0, min(10.0, float(result.get("score", 0))))

        logger.info(
            "Fundamental analysis complete for %s: score=%.1f",
            ticker, result["score"],
        )
        return result

    except Exception as e:
        logger.error("LLM call failed for fundamental analysis of %s: %s", ticker, e)
        return {
            "revenue": ratios.get("revenue", "N/A"),
            "pe_ratio": ratios.get("pe_ratio"),
            "earnings_growth": str(ratios.get("earnings_growth", "N/A")),
            "market_cap": str(ratios.get("market_cap", "N/A")),
            "debt": "N/A",
            "profit_margin": str(ratios.get("profit_margin", "N/A")),
            "score": 5.0,
            "summary": f"LLM analysis failed for {ticker}. Raw data provided.",
        }
