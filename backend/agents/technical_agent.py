"""
Technical Analyst Agent – Analyzes price movement and indicators.

Uses Yahoo Finance price history + pandas-ta for indicator calculations,
then calls Gemini to interpret the technical picture.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import google.generativeai as genai
import pandas as pd

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.tools.yahoo_finance_tool import YahooFinanceTool

logger = logging.getLogger("market_analyst.agents.technical")

# ── Prompt Template ────────────────────────────────────────────────

TECHNICAL_PROMPT = """You are a senior technical analyst. Analyze the following technical indicators and price data.

**Stock:** {ticker}

**Technical Indicators:**
{indicators_json}

**Recent Price Action (last 10 days):**
{recent_prices_json}

Provide your analysis in the following JSON format ONLY (no markdown, no extra text):
{{
    "rsi": <RSI value as number or null>,
    "macd": "<MACD assessment as string>",
    "ma50": <50-day MA as number or null>,
    "ma200": <200-day MA as number or null>,
    "trend": "<bullish|bearish|neutral>",
    "score": <score from 0 to 10 as number>,
    "summary": "<2-3 sentence summary of technical outlook>"
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


def _calculate_indicators(price_data: list[dict]) -> dict[str, Any]:
    """
    Calculate technical indicators from OHLCV price data.

    Computes RSI, MACD, MA50, MA200 using pandas operations.
    Falls back gracefully if pandas-ta is not installed.
    """
    logger.info("Calculating technical indicators from %d price records", len(price_data))

    if not price_data:
        logger.warning("No price data to calculate indicators")
        return {"rsi": None, "macd": None, "ma50": None, "ma200": None, "trend": "neutral"}

    df = pd.DataFrame(price_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    indicators: dict[str, Any] = {}

    # Moving Averages
    if len(df) >= 50:
        indicators["ma50"] = round(float(df["close"].rolling(50).mean().iloc[-1]), 2)
    else:
        indicators["ma50"] = round(float(df["close"].mean()), 2)

    if len(df) >= 200:
        indicators["ma200"] = round(float(df["close"].rolling(200).mean().iloc[-1]), 2)
    else:
        indicators["ma200"] = None

    # RSI (14-period)
    try:
        delta = df["close"].diff()
        avg_gain = delta.clip(lower=0).rolling(14).mean()
        avg_loss = (-delta.clip(upper=0)).rolling(14).mean()

        last_gain = avg_gain.iloc[-1] if not avg_gain.empty else 0
        last_loss = avg_loss.iloc[-1] if not avg_loss.empty else 0

        if pd.isna(last_gain) or pd.isna(last_loss):
            indicators["rsi"] = None
        elif last_loss == 0:
            indicators["rsi"] = 100.0  # No losses → fully bullish
        elif last_gain == 0:
            indicators["rsi"] = 0.0  # No gains → fully bearish
        else:
            rs = last_gain / last_loss
            indicators["rsi"] = round(100 - (100 / (1 + rs)), 2)
    except Exception as e:
        logger.warning("RSI calculation failed: %s", e)
        indicators["rsi"] = None

    # MACD (12, 26, 9)
    try:
        ema12 = df["close"].ewm(span=12).mean()
        ema26 = df["close"].ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        macd_val = float(macd_line.iloc[-1])
        signal_val = float(signal_line.iloc[-1])

        if macd_val > signal_val:
            indicators["macd"] = "bullish crossover"
        elif macd_val < signal_val:
            indicators["macd"] = "bearish crossover"
        else:
            indicators["macd"] = "neutral"
    except Exception as e:
        logger.warning("MACD calculation failed: %s", e)
        indicators["macd"] = "unavailable"

    # Trend detection
    current_price = float(df["close"].iloc[-1])
    ma50 = indicators.get("ma50")
    ma200 = indicators.get("ma200")

    if ma50 and ma200:
        if ma50 > ma200 and current_price > ma50:
            indicators["trend"] = "bullish"
        elif ma50 < ma200 and current_price < ma50:
            indicators["trend"] = "bearish"
        else:
            indicators["trend"] = "neutral"
    elif ma50:
        indicators["trend"] = "bullish" if current_price > ma50 else "bearish"
    else:
        indicators["trend"] = "neutral"

    indicators["current_price"] = current_price
    logger.info("Indicators calculated: RSI=%.2f, trend=%s", indicators.get("rsi") or 0, indicators["trend"])
    return indicators


async def analyze_technical(ticker: str, period: str = "1y") -> dict[str, Any]:
    """
    Run technical analysis for a single stock ticker.

    Args:
        ticker: Stock symbol, e.g. "TATAMOTORS.NS"
        period: Price history period (default "1y")

    Returns:
        TechnicalResult dict with indicators and score.
    """
    logger.info("Starting technical analysis for %s (period=%s)", ticker, period)

    # 1. Fetch price data
    price_result = await YahooFinanceTool.get_price_history(ticker, period=period)
    price_data = price_result.get("data", [])

    if not price_data:
        logger.error("No price data for %s, cannot perform technical analysis", ticker)
        return {
            "rsi": None,
            "macd": "unavailable",
            "ma50": None,
            "ma200": None,
            "trend": "neutral",
            "score": 0.0,
            "summary": f"Unable to analyze {ticker}: no price data available.",
        }

    # 2. Calculate indicators
    indicators = _calculate_indicators(price_data)

    # 3. Get recent prices for context
    recent_prices = price_data[-10:] if len(price_data) >= 10 else price_data

    # 4. Build prompt
    prompt = TECHNICAL_PROMPT.format(
        ticker=ticker,
        indicators_json=json.dumps(indicators, indent=2, default=str),
        recent_prices_json=json.dumps(recent_prices, indent=2, default=str),
    )
    logger.debug("Technical prompt for %s: %s", ticker, prompt[:200])

    # 5. Call LLM
    try:
        model = _configure_genai()
        logger.info("Calling Gemini for technical analysis of %s", ticker)
        response = model.generate_content(prompt)
        raw_text = response.text
        logger.info("Gemini response received for %s (%d chars)", ticker, len(raw_text))

        result = _parse_llm_response(raw_text)
        result["score"] = max(0.0, min(10.0, float(result.get("score", 0))))

        logger.info(
            "Technical analysis complete for %s: score=%.1f, trend=%s",
            ticker, result["score"], result.get("trend", "unknown"),
        )
        return result

    except Exception as e:
        logger.error("LLM call failed for technical analysis of %s: %s", ticker, e)
        return {
            "rsi": indicators.get("rsi"),
            "macd": indicators.get("macd", "unavailable"),
            "ma50": indicators.get("ma50"),
            "ma200": indicators.get("ma200"),
            "trend": indicators.get("trend", "neutral"),
            "score": 5.0,
            "summary": f"LLM analysis failed for {ticker}. Indicators computed from raw data.",
        }
