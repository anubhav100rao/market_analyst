"""
Sentiment Analyst Agent – Analyzes market sentiment from news.

Uses DuckDuckGo tool to gather recent news, then calls Gemini
to classify sentiment and produce a structured assessment.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import google.generativeai as genai

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.tools.duckduckgo_tool import DuckDuckGoTool

logger = logging.getLogger("market_analyst.agents.sentiment")

# ── Prompt Template ────────────────────────────────────────────────

SENTIMENT_PROMPT = """You are a senior market sentiment analyst. Analyze the following news articles about a stock and assess overall market sentiment.

**Stock:** {ticker}

**Recent News Articles:**
{news_json}

Provide your analysis in the following JSON format ONLY (no markdown, no extra text):
{{
    "positive_signals": ["<list of positive factors from the news>"],
    "negative_signals": ["<list of negative factors from the news>"],
    "score": <sentiment score from 0 to 10, where 0=extremely negative, 5=neutral, 10=extremely positive>,
    "summary": "<2-3 sentence summary of market sentiment>"
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


def analyze_sentiment(ticker: str, max_news: int = 10) -> dict[str, Any]:
    """
    Run sentiment analysis for a single stock ticker.

    Args:
        ticker: Stock symbol, e.g. "RELIANCE.NS"
        max_news: Maximum number of news articles to search

    Returns:
        SentimentResult dict with signals and score.
    """
    logger.info("Starting sentiment analysis for %s (max_news=%d)", ticker, max_news)

    # 1. Build search query from ticker
    #    Convert "RELIANCE.NS" → "Reliance Industries stock news"
    search_query = f"{ticker.replace('.NS', '').replace('.BO', '')} stock news India"
    logger.info("Search query: %r", search_query)

    # 2. Fetch news
    news_result = DuckDuckGoTool.search_news(search_query, max_results=max_news)
    articles = news_result.get("results", [])

    if not articles:
        logger.warning("No news found for %s, returning neutral sentiment", ticker)
        return {
            "positive_signals": [],
            "negative_signals": [],
            "score": 5.0,
            "summary": f"No recent news found for {ticker}. Defaulting to neutral sentiment.",
        }

    logger.info("Found %d news articles for %s", len(articles), ticker)

    # 3. Build prompt with article summaries
    news_for_prompt = []
    for i, article in enumerate(articles, 1):
        news_for_prompt.append({
            "index": i,
            "title": article.get("title", ""),
            "snippet": article.get("snippet", ""),
            "source": article.get("source", ""),
            "date": article.get("date", ""),
        })

    prompt = SENTIMENT_PROMPT.format(
        ticker=ticker,
        news_json=json.dumps(news_for_prompt, indent=2),
    )
    logger.debug("Sentiment prompt for %s: %s", ticker, prompt[:200])

    # 4. Call LLM
    try:
        model = _configure_genai()
        logger.info("Calling Gemini for sentiment analysis of %s", ticker)
        response = model.generate_content(prompt)
        raw_text = response.text
        logger.info("Gemini response received for %s (%d chars)", ticker, len(raw_text))

        result = _parse_llm_response(raw_text)

        # Ensure correct types
        result["positive_signals"] = list(result.get("positive_signals", []))
        result["negative_signals"] = list(result.get("negative_signals", []))
        result["score"] = max(0.0, min(10.0, float(result.get("score", 5.0))))

        logger.info(
            "Sentiment analysis complete for %s: score=%.1f, +signals=%d, -signals=%d",
            ticker, result["score"],
            len(result["positive_signals"]),
            len(result["negative_signals"]),
        )
        return result

    except Exception as e:
        logger.error("LLM call failed for sentiment analysis of %s: %s", ticker, e)
        return {
            "positive_signals": [],
            "negative_signals": [],
            "score": 5.0,
            "summary": f"LLM sentiment analysis failed for {ticker}. News was retrieved but not analyzed.",
        }
