# AI Market Analyst — Build TODO

Comprehensive task breakdown derived from [architecture.md](./architecture.md).

---

## Phase 0 · Project Scaffolding & Config
- [x] **P0-1** Initialize Python project (pyproject.toml or setup.py)
- [x] **P0-2** Create `requirements.txt` with all dependencies (fastapi, uvicorn, streamlit, langgraph, langchain, yfinance, pandas-ta, duckduckgo-search, pydantic, python-dotenv)
- [x] **P0-3** Create folder structure per §8 of architecture doc:
  ```
  market-analyst-ai/
  ├── backend/
  │   ├── api/
  │   ├── agents/
  │   ├── tools/
  │   ├── workflows/
  │   └── models/
  ├── frontend/
  ├── react-directory/
  ├── docs/
  ├── tests/
  ```
- [x] **P0-4** Add `.env.example` with required env vars (API keys, model config)
- [x] **P0-5** Create `README.md` with setup instructions
- [x] **P0-6** Add `.gitignore` (Python defaults, .env, __pycache__)

---

## Phase 1 · Data Models & State
- [x] **P1-1** Define `MarketGraphState` (TypedDict) in `backend/models/state.py` — fields: `query`, `stocks`, `analysis_type`, `fundamental_result`, `technical_result`, `sentiment_result`, `final_decision`, `recommendation`, `reasoning`, `stock_verdicts`
- [x] **P1-2** Define Pydantic request/response models in `backend/models/schemas.py` (AnalyzeStockRequest, CompareStocksRequest, PortfolioRequest, ChatRequest, AnalysisResponse, IntentResponse, ErrorResponse)
- [x] **P1-3** Write unit tests for model validation (`tests/test_state.py`, `tests/test_schemas.py`)

---

## Phase 2 · Tools Layer
- [x] **P2-1** Implement `backend/tools/yahoo_finance_tool.py`
  - [x] Fetch stock price history (configurable period)
  - [x] Fetch financial statements (income, balance sheet, cash flow)
  - [x] Fetch key ratios (PE, market cap, profit margin, debt)
  - [x] Error handling for invalid tickers
  - [x] SQLite MCP caching (indefinite TTL)
- [x] **P2-2** Implement `backend/tools/duckduckgo_tool.py`
  - [x] News search for a given stock/company
  - [x] Web search
  - [x] Return structured results (title, snippet, url, date)
  - [x] Rate limiting (1s between requests)
  - [x] SQLite MCP caching (1 hour TTL)
- [x] **P2-3** Implement `backend/tools/sqlite_mcp_tool.py`
  - [x] MCP client wrapper for SQLite caching
  - [x] `api_cache` table with tool_name, cache_key, response_data, created_at
  - [x] `get_cache()` with configurable max_age
  - [x] `set_cache()` with INSERT OR UPDATE
  - [x] Async lifecycle (initialize / shutdown)
- [x] **P2-4** Write unit tests for tools (mock external API calls) — `tests/test_yahoo_finance.py`, `tests/test_duckduckgo.py`, `tests/test_sqlite_mcp.py`

---

## Phase 3 · Specialized Agents

### 3A — Intent Analyzer Agent
- [x] **P3A-1** Create `backend/agents/intent_analyzer.py`
- [x] **P3A-2** Implement Gemini prompt for stock/intent extraction from natural language
- [x] **P3A-3** Indian stock ticker mapping (common names → NSE `.NS` format)
- [x] **P3A-4** Auto-correct analysis_type based on stock count (1=single, 2=compare, 3+=portfolio)
- [x] **P3A-5** `analyze_intent_from_request()` for typed endpoints (no LLM needed)
- [x] **P3A-6** Unit tests with mocked Gemini — `tests/test_intent_analyzer.py`

### 3B — Fundamental Analyst Agent
- [x] **P3B-1** Create `backend/agents/fundamental_agent.py`
- [x] **P3B-2** Implement LLM prompt for fundamental analysis (revenue, PE, earnings growth, market cap, debt, profit margin)
- [x] **P3B-3** Wire up Yahoo Finance tools (key ratios + financial statements)
- [x] **P3B-4** Return structured output with fundamental score (0–10)
- [x] **P3B-5** Fallback: score 5.0 with raw data defaults on LLM failure
- [x] **P3B-6** Unit tests with mocked LLM + mocked tools — `tests/test_fundamental_agent.py`

### 3C — Technical Analyst Agent
- [x] **P3C-1** Create `backend/agents/technical_agent.py`
- [x] **P3C-2** Implement indicator calculations (RSI-14, MACD 12/26/9, MA50, MA200, trend detection) in pure Python
- [x] **P3C-3** Implement LLM prompt for interpretation of indicators
- [x] **P3C-4** Return structured output with technical score (0–10)
- [x] **P3C-5** Fallback: score 5.0 with calculated indicators on LLM failure
- [x] **P3C-6** Unit tests with mocked LLM + sample price data — `tests/test_technical_agent.py`

### 3D — Sentiment Analyst Agent
- [x] **P3D-1** Create `backend/agents/sentiment_agent.py`
- [x] **P3D-2** Implement LLM prompt for sentiment classification of news articles
- [x] **P3D-3** Wire up DuckDuckGo news search tool
- [x] **P3D-4** Return structured output with sentiment score (0–10) + positive/negative signals
- [x] **P3D-5** Fallback: neutral (score 5.0, empty signals) on no news
- [x] **P3D-6** Unit tests with mocked LLM + mocked search results — `tests/test_sentiment_agent.py`

### 3E — Master Analyst (Aggregator) Agent
- [x] **P3E-1** Create `backend/agents/master_agent.py`
- [x] **P3E-2** Implement aggregation logic (combine fundamental, technical, sentiment scores)
- [x] **P3E-3** Implement LLM prompt for final recommendation (BUY / HOLD / SELL + reasoning)
- [x] **P3E-4** Support comparison mode (Stock A vs Stock B) and portfolio mode
- [x] **P3E-5** Per-stock verdicts with confidence scores
- [x] **P3E-6** Fallback: rule-based recommendation (avg >= 7 → BUY, <= 4 → SELL, else HOLD)
- [x] **P3E-7** Unit tests with sample agent outputs — `tests/test_master_agent.py`

---

## Phase 4 · LangGraph Orchestration
- [x] **P4-1** Create `backend/workflows/market_graph.py`
- [x] **P4-2** Define StateGraph with nodes: `intent`, `fundamental`, `technical`, `sentiment`, `aggregator`
- [x] **P4-3** Wire edges: intent → [fundamental, technical, sentiment] (parallel fan-out)
- [x] **P4-4** Wire edges: [fundamental, technical, sentiment] → aggregator (fan-in)
- [x] **P4-5** Intent node skips LLM when stocks/analysis_type pre-set (from typed endpoints)
- [x] **P4-6** Support single stock analysis, comparison, and portfolio workflows
- [x] **P4-7** Two-level caching layer:
  - [x] Level 1 — Intent cache (`parse_intent_cached`, 24h TTL, key: normalized query)
  - [x] Level 2 — Graph cache (`_check_and_run_graph`, 24h TTL, key: `{type}_{sorted_tickers}`)
- [x] **P4-8** Entry points: `run_analysis()`, `run_single_stock_analysis()`, `run_compare_stocks()`, `run_portfolio_analysis()`
- [x] **P4-9** Integration tests for full graph execution (mocked LLM + mocked tools) — `tests/test_market_graph.py`

---

## Phase 5 · FastAPI Backend
- [x] **P5-1** Create `backend/api/fastapi_server.py`
- [x] **P5-2** `GET /health` endpoint
- [x] **P5-3** `POST /parse_intent` endpoint (cached intent extraction, returns IntentResponse)
- [x] **P5-4** `POST /chat` endpoint (free-form query → full pipeline)
- [x] **P5-5** `POST /analyze_stock` endpoint (typed single stock)
- [x] **P5-6** `POST /compare_stocks` endpoint (typed two-stock comparison)
- [x] **P5-7** `POST /portfolio_analysis` endpoint (typed multi-stock portfolio)
- [x] **P5-8** `_build_response()` helper: convert LangGraph output → AnalysisResponse
- [x] **P5-9** Error handling middleware (global exception → ErrorResponse)
- [x] **P5-10** CORS middleware (all origins)
- [x] **P5-11** Lifespan management (SQLiteMCPTool init/shutdown)
- [x] **P5-12** API tests (TestClient, mock workflow layer) — `tests/test_fastapi.py`

---

## Phase 6 · Streamlit Frontend
- [x] **P6-1** Create `frontend/streamlit_app.py`
- [x] **P6-2** **Unified single chat input** (no mode switching)
- [x] **P6-3** Call `/parse_intent` first to show intent badges (detected stocks + analysis type)
- [x] **P6-4** Call `/chat` for full analysis pipeline
- [x] **P6-5** Display multi-dimensional analysis results (cards / expandable sections)
- [x] **P6-6** Display recommendation banner (color-coded BUY/HOLD/SELL)
- [x] **P6-7** Session-state chat history
- [x] **P6-8** Wire Streamlit → FastAPI backend
- [x] **P6-9** Manual UI testing

---

## Phase 6B · React Frontend
- [x] **P6B-1** Initialize React 19 + TypeScript + Vite project (`react-directory/`)
- [x] **P6B-2** Define TypeScript interfaces matching backend schemas (`types.ts`) — including `IntentResponse`
- [x] **P6B-3** Implement axios API client (`api.ts`) — `parseIntent`, `chat`, `analyzeStock`, `compareStocks`, `portfolioAnalysis`
- [x] **P6B-4** Implement `ChatPanel.tsx` — **unified single query box**
  - [x] Two-step flow: `/parse_intent` → show intent badges → `/chat` → show results
  - [x] Loading stages: "Understanding your query..." → "Running analysis..."
  - [x] `IntentBadges` component (analysis type in purple, stock tickers in green)
- [x] **P6B-5** Implement `StockCard.tsx` — analysis result cards (fundamental / technical / sentiment panels with color-coded scores)
- [x] **P6B-6** Implement `Sidebar.tsx` — branding + usage hints (no mode navigation)
- [x] **P6B-7** Implement `App.tsx` — single-view layout (Sidebar + ChatPanel only)
- [x] **P6B-8** Error handling utility (`error.ts`) — axios error detail extraction
- [x] **P6B-9** Dark theme CSS with glass-morphism (`index.css`)
- [x] **P6B-10** Unit tests: App integration test, API mock test, error utility test (Vitest + Testing Library)

---

## Phase 7 · Integration & E2E Testing
- [ ] **P7-1** End-to-end test: single stock query through full pipeline
- [ ] **P7-2** End-to-end test: stock comparison flow
- [ ] **P7-3** End-to-end test: portfolio analysis flow
- [ ] **P7-4** Test error scenarios (invalid ticker, API failures, timeout)
- [ ] **P7-5** Performance test: verify parallel agent execution
- [ ] **P7-6** Test cache hit/miss scenarios end-to-end
- [ ] **P7-7** Test React ↔ FastAPI integration

---

## Phase 8 · DevOps & Documentation
- [x] **P8-1** Add `Makefile` with common commands (install, dev, test, lint, docker-build)
- [ ] **P8-2** Create `Dockerfile` for backend
- [ ] **P8-3** Create `docker-compose.yml` (backend + Streamlit + React services)
- [x] **P8-4** Update architecture.md with full system documentation
- [x] **P8-5** API documentation (auto-gen via FastAPI /docs)
- [ ] **P8-6** Update `README.md` with full setup, usage, and architecture overview

---

## Phase 9 · Future Enhancements (from §13)
- [ ] **P9-1** Vector database for news memory (e.g. ChromaDB)
- [ ] **P9-2** LLM reasoning chains
- [ ] **P9-3** Event-driven updates (real-time market triggers)
- [ ] **P9-4** Portfolio risk modeling
- [ ] **P9-5** Backtesting engine

---

> **Recommended build order**: P0 → P1 → P2 → P3 → P4 → P5 → P6 → P6B → P7 → P8
> Phase 9 is stretch / post-MVP.

| Phase | Tasks | Status | Estimated Effort |
|-------|-------|--------|-----------------|
| P0 Scaffolding | 6 | Done | ~1 hr |
| P1 Models | 3 | Done | ~1 hr |
| P2 Tools | 4 | Done | ~3 hrs |
| P3 Agents | 30 | Done | ~8 hrs |
| P4 Orchestration | 9 | Done | ~4 hrs |
| P5 API | 12 | Done | ~3 hrs |
| P6 Streamlit | 9 | Done | ~4 hrs |
| P6B React | 10 | Done | ~4 hrs |
| P7 E2E Testing | 7 | Open | ~3 hrs |
| P8 DevOps | 6 | Partial | ~2 hrs |
| **Total** | **96 tasks** | **79 done** | **~33 hrs** |
