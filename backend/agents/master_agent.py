"""
Master Analyst (Aggregator) Agent – Combines all analysis dimensions.

Takes results from Fundamental, Technical, and Sentiment agents,
then calls Gemini to produce a final recommendation (Buy/Hold/Sell).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import google.generativeai as genai

from backend.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("market_analyst.agents.master")

# ── Prompt Template (Single / Portfolio) ───────────────────────────

MASTER_PROMPT = """You are a senior market strategist and chief investment officer. You are given analysis from three specialized analysts for the following stock(s).

**Analysis Type:** {analysis_type}

**Stocks being analyzed:** {stocks}

**Fundamental Analysis:**
{fundamental_json}

**Technical Analysis:**
{technical_json}

**Sentiment Analysis:**
{sentiment_json}

Based on ALL the above analysis, provide your final investment recommendation.

Respond in the following JSON format ONLY (no markdown, no extra text):
{{
    "recommendation": "<BUY|HOLD|SELL>",
    "reasoning": "<detailed 3-5 sentence reasoning combining all dimensions>",
    "stock_verdicts": {{
        "<ticker>": {{
            "recommendation": "<BUY|HOLD|SELL>",
            "confidence": <confidence 0-10>,
            "one_liner": "<one sentence verdict>"
        }}
    }}
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
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def _build_fallback_recommendation(
    fundamental_results: dict,
    technical_results: dict,
    sentiment_results: dict,
) -> dict[str, Any]:
    """Build a simple rule-based recommendation when LLM fails."""
    logger.info("Building fallback recommendation from raw scores")

    scores = []
    for stock in set(
        list(fundamental_results.keys())
        + list(technical_results.keys())
        + list(sentiment_results.keys())
    ):
        f_score = fundamental_results.get(stock, {}).get("score", 5.0)
        t_score = technical_results.get(stock, {}).get("score", 5.0)
        s_score = sentiment_results.get(stock, {}).get("score", 5.0)
        avg = (f_score + t_score + s_score) / 3
        scores.append((stock, avg))

    overall_avg = sum(s for _, s in scores) / len(scores) if scores else 5.0

    if overall_avg >= 7.0:
        rec = "BUY"
    elif overall_avg <= 4.0:
        rec = "SELL"
    else:
        rec = "HOLD"

    stock_verdicts = {}
    for stock, avg in scores:
        if avg >= 7.0:
            sv_rec = "BUY"
        elif avg <= 4.0:
            sv_rec = "SELL"
        else:
            sv_rec = "HOLD"
        stock_verdicts[stock] = {
            "recommendation": sv_rec,
            "confidence": round(avg, 1),
            "one_liner": f"Average score: {avg:.1f}/10",
        }

    return {
        "recommendation": rec,
        "reasoning": f"Fallback recommendation based on average scores. Overall average: {overall_avg:.1f}/10.",
        "stock_verdicts": stock_verdicts,
    }


def aggregate_analysis(
    stocks: list[str],
    analysis_type: str,
    fundamental_results: dict[str, dict],
    technical_results: dict[str, dict],
    sentiment_results: dict[str, dict],
) -> dict[str, Any]:
    """
    Combine analyses from all agents and produce a final recommendation.

    Args:
        stocks: List of stock tickers analyzed
        analysis_type: "single", "compare", or "portfolio"
        fundamental_results: Maps ticker → FundamentalResult
        technical_results: Maps ticker → TechnicalResult
        sentiment_results: Maps ticker → SentimentResult

    Returns:
        dict with recommendation, reasoning, and per-stock verdicts.
    """
    logger.info(
        "Aggregating analysis: type=%s, stocks=%s",
        analysis_type, stocks,
    )

    # 1. Build prompt
    prompt = MASTER_PROMPT.format(
        analysis_type=analysis_type,
        stocks=", ".join(stocks),
        fundamental_json=json.dumps(fundamental_results, indent=2, default=str),
        technical_json=json.dumps(technical_results, indent=2, default=str),
        sentiment_json=json.dumps(sentiment_results, indent=2, default=str),
    )
    logger.debug("Master prompt: %s", prompt[:200])

    # 2. Call LLM
    try:
        model = _configure_genai()
        logger.info("Calling Gemini for master aggregation")
        response = model.generate_content(prompt)
        raw_text = response.text
        logger.info("Gemini response received (%d chars)", len(raw_text))

        result = _parse_llm_response(raw_text)

        # Validate recommendation
        rec = result.get("recommendation", "HOLD").upper()
        if rec not in ("BUY", "HOLD", "SELL"):
            logger.warning("Invalid recommendation %r, defaulting to HOLD", rec)
            rec = "HOLD"
        result["recommendation"] = rec

        logger.info(
            "Master analysis complete: recommendation=%s",
            result["recommendation"],
        )
        return result

    except Exception as e:
        logger.error("LLM call failed for master aggregation: %s", e)
        return _build_fallback_recommendation(
            fundamental_results, technical_results, sentiment_results
        )
