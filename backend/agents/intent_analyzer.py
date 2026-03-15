"""
Intent Analyzer – Parses user queries to extract stocks and analysis type.

This is the entry node in the LangGraph workflow. It determines:
  - Which stocks should be analyzed
  - What type of analysis to perform (single/compare/portfolio)
"""

from __future__ import annotations

import json
import logging
from typing import Any

import google.generativeai as genai

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("market_analyst.agents.intent_analyzer")

# ── Prompt Template ────────────────────────────────────────────────

INTENT_PROMPT = """You are a query parser for a stock market analysis system. Extract the user's intent from their query.

**User query:** "{query}"

Determine:
1. Which stock ticker(s) are being asked about (use NSE format with .NS suffix, e.g. RELIANCE.NS, TATAMOTORS.NS, INFY.NS)
2. The type of analysis requested

Common Indian stock mappings:
- Reliance / RIL → RELIANCE.NS
- Tata Motors → TATAMOTORS.NS
- Mahindra / M&M → M&M.NS
- Infosys → INFY.NS
- TCS → TCS.NS
- HDFC Bank → HDFCBANK.NS
- ICICI Bank → ICICIBANK.NS
- Wipro → WIPRO.NS
- Bharti Airtel / Airtel → BHARTIARTL.NS
- SBI / State Bank → SBIN.NS
- ITC → ITC.NS
- Bajaj Finance → BAJFINANCE.NS
- HUL / Hindustan Unilever → HINDUNILVR.NS
- Asian Paints → ASIANPAINT.NS
- Maruti / Maruti Suzuki → MARUTI.NS

Respond in the following JSON format ONLY (no markdown, no extra text):
{{
    "stocks": ["<TICKER1.NS>", "<TICKER2.NS>"],
    "analysis_type": "<single|compare|portfolio>",
    "parsed_query": "<cleaned version of what the user is asking>"
}}

Rules:
- "single" = one stock analysis
- "compare" = exactly two stocks compared head-to-head
- "portfolio" = three or more stocks analyzed together
- If you cannot identify any stocks, return an empty list
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
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def analyze_intent(query: str) -> dict[str, Any]:
    """
    Parse a user query to extract stocks and analysis type.

    Args:
        query: Natural-language market question

    Returns:
        dict with stocks (list), analysis_type (str), parsed_query (str)
    """
    logger.info("Analyzing intent for query: %r", query)

    try:
        model = _configure_genai()
        prompt = INTENT_PROMPT.format(query=query)

        logger.info("Calling Gemini for intent analysis")
        response = model.generate_content(prompt)
        raw_text = response.text
        logger.info("Intent analysis response received (%d chars)", len(raw_text))

        result = _parse_llm_response(raw_text)

        # Validate and normalize
        stocks = list(result.get("stocks", []))
        analysis_type = result.get("analysis_type", "single")

        # Auto-correct analysis type based on stock count
        if len(stocks) == 0:
            analysis_type = "single"
        elif len(stocks) == 1:
            analysis_type = "single"
        elif len(stocks) == 2:
            analysis_type = "compare"
        elif len(stocks) >= 3:
            analysis_type = "portfolio"

        parsed = {
            "stocks": stocks,
            "analysis_type": analysis_type,
            "parsed_query": result.get("parsed_query", query),
        }

        logger.info(
            "Intent parsed: stocks=%s, type=%s",
            parsed["stocks"], parsed["analysis_type"],
        )
        return parsed

    except Exception as e:
        logger.error("Intent analysis failed: %s", e)
        return {
            "stocks": [],
            "analysis_type": "single",
            "parsed_query": query,
        }


def analyze_intent_from_request(
    stocks: list[str],
    analysis_type: str,
    query: str = "",
) -> dict[str, Any]:
    """
    Build intent from explicit API request parameters (no LLM call needed).

    Used by typed endpoints like POST /analyze_stock, POST /compare_stocks.
    """
    logger.info(
        "Intent from request: stocks=%s, type=%s, query=%r",
        stocks, analysis_type, query,
    )
    return {
        "stocks": stocks,
        "analysis_type": analysis_type,
        "parsed_query": query or f"Analyze {', '.join(stocks)}",
    }
