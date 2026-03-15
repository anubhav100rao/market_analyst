# AI Market Analyst – High Level Architecture

## 1. System Overview

The system answers questions like:

* *How is Reliance doing?*
* *How is my portfolio performing?*
* *Compare Tata Motors vs Mahindra & Mahindra*

Users type **one natural-language query** into a **unified chat box**. The **Intent Analyzer** (powered by Gemini) extracts stock tickers and analysis type automatically — no mode-switching required.

It works by orchestrating **multiple specialized agents** that analyze the market from different perspectives.

Agents run **in parallel**, and a **Master Analyst Agent** compiles the final answer.

---

# 2. High-Level System Architecture

```
  ┌─────────────────────┐    ┌──────────────────────────┐
  │   React Frontend    │    │     Streamlit Frontend   │
  │ (unified chat box)  │    │   (unified chat box)     │
  └─────────┬───────────┘    └────────────┬─────────────┘
            │                             │
            │          REST (JSON)        │
            └──────────┬──────────────────┘
                       ▼
              ┌────────────────┐
              │   FastAPI API  │
              │ Query Gateway  │
              │                │
              │ /parse_intent  │◄── Intent Analyzer (cached)
              │ /chat          │◄── Full pipeline
              │ /analyze_stock │
              │ /compare_stocks│
              │ /portfolio     │
              └───────┬────────┘
                      │
             ┌────────▼─────────┐
             │    Two-Level     │
             │   Cache Layer    │
             │  (SQLite MCP)    │
             └────────┬─────────┘
                      │ cache miss
             ┌────────▼─────────┐
             │   LangGraph      │
             │  Orchestration   │
             └────────┬─────────┘
                      │
   ┌──────────────────┼───────────────────┐
   │                  │                   │
   ▼                  ▼                   ▼

┌──────────────┐ ┌────────────────┐ ┌────────────────┐
│ Fundamental  │ │ Technical      │ │ Sentiment      │
│ Analyst      │ │ Analyst        │ │ Analyst        │
│ Agent        │ │ Agent          │ │ Agent          │
└──────┬───────┘ └───────┬────────┘ └───────┬────────┘
       │                 │                  │
       ▼                 ▼                  ▼

┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│ Yahoo Finance│ │ Yahoo Finance│ │ DuckDuckGo       │
│ Financials   │ │ Price Data   │ │ News Search      │
└──────────────┘ └──────────────┘ └──────────────────┘


          ▼
  ┌────────────────┐
  │ Master Analyst │
  │ Aggregator     │
  └────────────────┘

          ▼
     Final Report
```

---

# 3. Core Components

---

# 3.1 Frontend Layer (React + Streamlit)

The project ships **two frontends** — a React SPA and a Streamlit app — both offering the same **unified single-query experience**.

## 3.1.1 React Frontend (`react-directory/`)

Built with React 19, TypeScript, Vite, Framer Motion, and Lucide icons.

Key characteristics:

* **Single query box** — user types natural language, no mode selection needed
* Calls `POST /parse_intent` first to show intent badges (detected stocks + analysis type)
* Then calls `POST /chat` for the full analysis pipeline
* Results displayed as StockCards with fundamental / technical / sentiment panels
* Dark theme with glass-morphism styling
* Comprehensive test suite (Vitest + Testing Library)

```
react-directory/
├── src/
│   ├── components/
│   │   ├── Sidebar.tsx        (branding + usage hints)
│   │   ├── ChatPanel.tsx      (unified query + intent badges + results)
│   │   └── StockCard.tsx      (analysis result cards)
│   ├── App.tsx                (layout shell)
│   ├── api.ts                 (axios client: parseIntent, chat, analyzeStock, ...)
│   ├── types.ts               (TypeScript interfaces incl. IntentResponse)
│   ├── error.ts               (error extraction utility)
│   ├── index.css              (CSS variables, glass-panel, dark theme)
│   ├── App.test.tsx           (integration tests)
│   ├── api.test.ts            (API mock tests)
│   └── error.test.ts          (error utility tests)
├── package.json
└── vite.config.ts
```

## 3.1.2 Streamlit Frontend (`frontend/streamlit_app.py`)

* **Single chat input** — same unified experience as React
* Calls `/parse_intent` then `/chat` sequentially
* Displays intent badges, recommendation banner, per-stock analysis cards
* Session-state chat history

---

# 3.2 FastAPI Backend

Acts as **API gateway** between frontends and the LangGraph pipeline.

Responsibilities:

* Accept user queries (natural language or typed parameters)
* Parse intent (cached) and route to correct workflow
* Execute LangGraph pipeline (with two-level caching)
* Return structured JSON responses

Endpoints:

```
GET  /health            — health check
POST /parse_intent      — extract stocks + analysis_type from query (cached, no full analysis)
POST /chat              — free-form query → full pipeline
POST /analyze_stock     — typed single stock analysis
POST /compare_stocks    — typed two-stock comparison
POST /portfolio_analysis — typed multi-stock portfolio
```

Example — unified flow:

```
1. Frontend calls POST /parse_intent  { "query": "Compare TCS and Infosys" }
   → { "stocks": ["TCS.NS", "INFY.NS"], "analysis_type": "compare", "parsed_query": "..." }

2. Frontend calls POST /chat  { "query": "Compare TCS and Infosys" }
   → Full AnalysisResponse with recommendation, reasoning, per-stock breakdowns
```

---

# 3.3 Intent Analyzer (`backend/agents/intent_analyzer.py`)

The intent analyzer is the **entry point** for all free-form queries.

Function: `analyze_intent(query: str) -> dict`

Responsibilities:

* Parse natural language to extract Indian stock tickers (NSE `.NS` format)
* Detect analysis type: `single` (1 stock), `compare` (2 stocks), `portfolio` (3+ stocks)
* Auto-correct analysis type based on stock count
* Return `{ stocks, analysis_type, parsed_query }`

Stock mapping examples:

```
"Reliance"       → RELIANCE.NS
"TCS"            → TCS.NS
"Infosys"        → INFY.NS
"HDFC Bank"      → HDFCBANK.NS
"Tata Motors"    → TATAMOTORS.NS
```

---

# 3.4 LangGraph Orchestration Layer

This is the **heart of the system**.

LangGraph manages:

* agent coordination
* state passing
* parallel execution (fan-out / fan-in)
* result aggregation

Graph structure:

```
            START
              │
              ▼
        Intent Analyzer
              │
      ┌───────┼────────┐
      ▼       ▼        ▼

Fundamental Technical Sentiment
   Agent       Agent      Agent      (parallel)
      \         |        /
       \        |       /
        ▼       ▼      ▼
        Result Aggregator
               │
               ▼
             END
```

LangGraph state:

```python
class MarketGraphState(TypedDict):
    query: str
    stocks: list[str]
    analysis_type: str               # single | compare | portfolio
    fundamental_result: dict         # ticker → FundamentalResult
    technical_result: dict           # ticker → TechnicalResult
    sentiment_result: dict           # ticker → SentimentResult
    final_decision: str
    recommendation: str              # BUY | HOLD | SELL
    reasoning: str
    stock_verdicts: dict             # per-stock recommendation + confidence
```

---

# 4. Agent Design

Each agent is a **specialized expert** powered by Gemini LLM.

---

# 4.1 Fundamental Analyst Agent

Goal: Analyze company fundamentals.

Data Source: Yahoo Finance (key ratios + financial statements).

Metrics:

* Revenue
* PE ratio
* Earnings growth
* Market cap
* Debt level (low / moderate / high)
* Profit margin

Output:

```json
{
  "revenue": "₹2.5T",
  "pe_ratio": 24.5,
  "earnings_growth": "8%",
  "market_cap": "₹17.2T",
  "debt": "moderate",
  "profit_margin": "11%",
  "score": 7.0,
  "summary": "Strong fundamentals with moderate debt..."
}
```

Fallback: If LLM fails, returns score 5.0 with raw data defaults.

---

# 4.2 Technical Analyst Agent

Goal: Analyze **price movement and indicators**.

Data: Yahoo Finance 1-year price history.

Indicators (calculated in Python, no external TA library needed):

* RSI (14-period)
* MACD (12/26/9 EMA)
* MA50 (50-day moving average)
* MA200 (200-day moving average)
* Trend detection (bullish / bearish / neutral)

Output:

```json
{
  "rsi": 62.0,
  "macd": "bullish crossover",
  "ma50": 2450.0,
  "ma200": 2280.0,
  "trend": "bullish",
  "score": 8.0,
  "summary": "Strong bullish momentum..."
}
```

Trend rules:
* Bullish: price > MA50 > MA200
* Bearish: price < MA50 < MA200
* Neutral: otherwise

---

# 4.3 Sentiment Analyst Agent

Goal: Understand **market sentiment** from recent news.

Sources: DuckDuckGo news search (up to 10 articles).

Output:

```json
{
  "positive_signals": ["EV expansion news", "strong quarterly results"],
  "negative_signals": ["supply chain concerns"],
  "score": 6.0,
  "summary": "Moderately positive sentiment driven by..."
}
```

Score scale: 0 = very bearish, 5 = neutral, 10 = very bullish.

---

# 4.4 Master Analyst (Aggregator) Agent

This agent combines all three analyses into a final recommendation.

Input: fundamental + technical + sentiment results for all stocks.

Output:

```json
{
  "recommendation": "BUY",
  "reasoning": "Strong fundamentals with bullish technical momentum...",
  "stock_verdicts": {
    "TATAMOTORS.NS": {
      "recommendation": "BUY",
      "confidence": 8.0,
      "one_liner": "Strong momentum with improving fundamentals"
    }
  }
}
```

Fallback: If LLM fails, uses rule-based scoring:
* Average of all three scores >= 7.0 → BUY
* Average <= 4.0 → SELL
* Otherwise → HOLD

---

# 5. Tools Layer

Agents interact with data tools. All tools use **SQLite MCP caching**.

---

## 5.1 Yahoo Finance Tool (`backend/tools/yahoo_finance_tool.py`)

Static methods with async caching:

* `get_price_history(ticker, period)` — OHLCV data (cache: indefinite)
* `get_financial_statements(ticker)` — income, balance sheet, cash flow (cache: indefinite)
* `get_key_ratios(ticker)` — PE, market cap, margins, debt (cache: indefinite)

---

## 5.2 DuckDuckGo Tool (`backend/tools/duckduckgo_tool.py`)

Static methods with rate limiting (1s between requests):

* `search_news(query, max_results)` — recent news (cache: 1 hour)
* `search_web(query, max_results)` — web results (cache: 1 hour)

---

## 5.3 SQLite MCP Cache (`backend/tools/sqlite_mcp_tool.py`)

Persistent caching layer using MCP (Model Context Protocol) with SQLite.

Database: `market_analysis.db`

Schema:

```sql
CREATE TABLE api_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    response_data TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(tool_name, cache_key)
)
```

Tool names and their cache TTLs:

| Tool Name | Cache Key Format | TTL |
|-----------|-----------------|-----|
| `intent_analysis` | `{query_normalized}` | 24 hours |
| `market_graph` | `{type}_{sorted_tickers}` | 24 hours |
| `yahoo_finance_history` | `{ticker}_{period}` | Indefinite |
| `yahoo_finance_financials` | `{ticker}` | Indefinite |
| `yahoo_finance_ratios` | `{ticker}` | Indefinite |
| `duckduckgo` | `news_{max}_{query}` | 1 hour |

---

# 6. Two-Level Cache Strategy

The caching layer is critical for performance and cost reduction:

```
User Query
    │
    ▼
Level 1: Intent Cache (24h TTL)
    │
    ├── HIT  → return cached intent
    ├── MISS → call Gemini for intent parsing
    │
    ▼
Level 2: Graph Cache (24h TTL)
    │
    ├── HIT  → return cached full result (skip all agents)
    ├── MISS → run full LangGraph pipeline
    │           ├── Tool-level caches (Yahoo Finance, DuckDuckGo)
    │           └── Store result in graph cache
    │
    ▼
AnalysisResponse
```

Cache key examples:

```
Intent:  "compare tcs and infosys"
Graph:   "compare_INFY.NS_TCS.NS"
Yahoo:   "TCS.NS_1y"
News:    "news_10_TCS stock news India"
```

---

# 7. Portfolio Analysis Flow

User input (natural language):

```
"Analyze Reliance, TCS, and Infosys"
```

Intent analyzer detects 3 stocks → `analysis_type: "portfolio"`

Workflow:

```
For each stock:
  run [fundamental, technical, sentiment] agents in parallel
    ↓
collect all results
    ↓
aggregate portfolio-level recommendation
    ↓
final report with per-stock verdicts
```

---

# 8. Project Folder Structure

```
market-analyst-ai/
│
├── backend/
│   ├── api/
│   │   └── fastapi_server.py       # FastAPI gateway (6 endpoints)
│   │
│   ├── agents/
│   │   ├── intent_analyzer.py      # Query → stocks + analysis_type
│   │   ├── fundamental_agent.py    # Financial analysis via Gemini
│   │   ├── technical_agent.py      # Price/indicator analysis
│   │   ├── sentiment_agent.py      # News sentiment analysis
│   │   └── master_agent.py         # Final recommendation aggregator
│   │
│   ├── tools/
│   │   ├── yahoo_finance_tool.py   # Stock data (cached)
│   │   ├── duckduckgo_tool.py      # News search (cached, rate-limited)
│   │   └── sqlite_mcp_tool.py      # SQLite MCP cache layer
│   │
│   ├── workflows/
│   │   └── market_graph.py         # LangGraph orchestration + caching
│   │
│   ├── models/
│   │   ├── state.py                # TypedDict state definitions
│   │   └── schemas.py              # Pydantic request/response models
│   │
│   └── config.py                   # Env vars, logging setup
│
├── frontend/
│   └── streamlit_app.py            # Streamlit unified chat UI
│
├── react-directory/                # React unified chat UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   └── StockCard.tsx
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
│
├── tests/                          # 12 test files (pytest, mocked)
│   ├── test_fastapi.py
│   ├── test_market_graph.py
│   ├── test_intent_analyzer.py
│   ├── test_fundamental_agent.py
│   ├── test_technical_agent.py
│   ├── test_sentiment_agent.py
│   ├── test_master_agent.py
│   ├── test_yahoo_finance.py
│   ├── test_duckduckgo.py
│   ├── test_sqlite_mcp.py
│   ├── test_state.py
│   └── test_schemas.py
│
├── docs/
│   ├── architecture.md             # This file
│   ├── todo.md                     # Build task tracker
│   └── rules.md                    # Development rules
│
├── requirements.txt
├── Makefile
├── .env / .env.example
└── market_analysis.db              # SQLite cache database
```

---

# 9. Example User Query Flow

User types (in React or Streamlit):

```
"Compare Tata Motors and Mahindra"
```

Full flow:

```
React / Streamlit
 ↓
POST /parse_intent  →  { stocks: ["TATAMOTORS.NS", "M&M.NS"], analysis_type: "compare" }
 ↓
UI shows intent badges: [Stock Comparison] [TATAMOTORS.NS] [M&M.NS]
 ↓
POST /chat
 ↓
FastAPI → parse_intent_cached (Level 1 cache check)
 ↓
_check_and_run_graph (Level 2 cache check)
 ↓
Cache MISS → LangGraph pipeline:
  intent_node (skip — already parsed)
    ↓
  [fundamental_node, technical_node, sentiment_node]  (parallel)
    ↓
  aggregator_node
 ↓
Cache result → return AnalysisResponse
 ↓
UI displays: Verdict + StockCards
```

---

# 10. Example Final Response

```json
{
  "analysis_type": "compare",
  "recommendation": "BUY",
  "reasoning": "Tata Motors shows stronger technical momentum with bullish MACD crossover...",
  "stocks": [
    {
      "stock": "TATAMOTORS.NS",
      "fundamental": { "pe_ratio": 18.5, "score": 7.0, "summary": "..." },
      "technical": { "rsi": 62, "trend": "bullish", "score": 8.0, "summary": "..." },
      "sentiment": { "positive_signals": ["EV expansion"], "score": 6.0, "summary": "..." }
    },
    {
      "stock": "M&M.NS",
      "fundamental": { "pe_ratio": 22.0, "score": 7.5, "summary": "..." },
      "technical": { "rsi": 55, "trend": "neutral", "score": 6.0, "summary": "..." },
      "sentiment": { "positive_signals": ["SUV demand"], "score": 6.5, "summary": "..." }
    }
  ]
}
```

---

# 11. Configuration

Environment variables (`.env`):

```
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.1-flash-lite-preview
LOG_FILE=dump.log
LOG_LEVEL=INFO
```

Logging:

* File handler: `dump.log` (append, UTF-8)
* Console handler: stdout
* Format: `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`

---

# 12. Testing Strategy

* **All external API calls are mocked** (Gemini, Yahoo Finance, DuckDuckGo) — per `docs/rules.md`
* Backend: 12 pytest test files covering every layer
* React: 3 Vitest test files (integration, API mocking, error handling)
* FastAPI: TestClient-based endpoint tests
* LangGraph: Full pipeline integration tests with mocked agents

---

# 13. Future Enhancements

* **Vector database for news memory** (ChromaDB)
* **LLM reasoning chains**
* **Event-driven updates** (real-time market triggers)
* **Portfolio risk modeling**
* **Backtesting engine**
