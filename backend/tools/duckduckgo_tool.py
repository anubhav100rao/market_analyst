"""
DuckDuckGo Search Tool – Fetches news and web search results.

Provides:
  - News search for a given company/stock
  - Structured results (title, snippet, url, date)
  - Basic rate-limit / error handling
"""

from __future__ import annotations

import logging
import time
from typing import Any

from duckduckgo_search import DDGS

logger = logging.getLogger("market_analyst.tools.duckduckgo")

# Simple rate-limit: minimum seconds between requests
_MIN_REQUEST_INTERVAL = 1.0
_last_request_time: float = 0.0


class DuckDuckGoTool:
    """Wrapper around duckduckgo-search for structured news retrieval."""

    # ── News Search ───────────────────────────────────────────────

    @staticmethod
    def search_news(
        query: str,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """
        Search for recent news articles related to a query.

        Args:
            query: Search query, e.g. "Reliance Industries stock news"
            max_results: Maximum number of results to return (default 10)

        Returns:
            dict with keys: query, results (list of article dicts), count
        """
        global _last_request_time

        logger.info("Searching news: query=%r, max_results=%d", query, max_results)

        try:
            # Rate limiting
            elapsed = time.time() - _last_request_time
            if elapsed < _MIN_REQUEST_INTERVAL:
                wait = _MIN_REQUEST_INTERVAL - elapsed
                logger.debug("Rate limiting: sleeping %.2fs", wait)
                time.sleep(wait)

            _last_request_time = time.time()

            with DDGS() as ddgs:
                raw_results = list(ddgs.news(query, max_results=max_results))

            articles = []
            for item in raw_results:
                articles.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("body", ""),
                    "url": item.get("url", ""),
                    "date": item.get("date", ""),
                    "source": item.get("source", ""),
                })

            logger.info("Found %d news articles for %r", len(articles), query)
            return {
                "query": query,
                "results": articles,
                "count": len(articles),
            }

        except Exception as e:
            logger.error("Error searching news for %r: %s", query, e)
            return {
                "query": query,
                "results": [],
                "count": 0,
                "error": str(e),
            }

    # ── Web Search ────────────────────────────────────────────────

    @staticmethod
    def search_web(
        query: str,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """
        General web search for broader context.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            dict with keys: query, results (list of result dicts), count
        """
        global _last_request_time

        logger.info("Web search: query=%r, max_results=%d", query, max_results)

        try:
            elapsed = time.time() - _last_request_time
            if elapsed < _MIN_REQUEST_INTERVAL:
                wait = _MIN_REQUEST_INTERVAL - elapsed
                logger.debug("Rate limiting: sleeping %.2fs", wait)
                time.sleep(wait)

            _last_request_time = time.time()

            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))

            results = []
            for item in raw_results:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("body", ""),
                    "url": item.get("href", ""),
                })

            logger.info("Found %d web results for %r", len(results), query)
            return {
                "query": query,
                "results": results,
                "count": len(results),
            }

        except Exception as e:
            logger.error("Error in web search for %r: %s", query, e)
            return {
                "query": query,
                "results": [],
                "count": 0,
                "error": str(e),
            }
