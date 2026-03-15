# AI Market Analyst — Build TODO

Comprehensive task breakdown derived from [architecture.md](file:///Users/anubhav100rao/development/market_analyst/docs/architecture.md).

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
  ├── docs/
  ├── tests/
  ```
- [x] **P0-4** Add `.env.example` with required env vars (API keys, model config)
- [x] **P0-5** Create `README.md` with setup instructions
- [x] **P0-6** Add `.gitignore` (Python defaults, .env, __pycache__)

---

## Phase 1 · Data Models & State
- [x] **P1-1** Define `MarketState` (TypedDict) in `backend/models/state.py` — fields: `query`, `stocks`, `fundamental_result`, `technical_result`, `sentiment_result`, `final_decision`
- [x] **P1-2** Define Pydantic request/response models for API endpoints (AnalyzeStockRequest, CompareStocksRequest, PortfolioRequest, AnalysisResponse)
- [x] **P1-3** Write unit tests for model validation

---

## Phase 2 · Tools Layer
- [x] **P2-1** Implement `backend/tools/yahoo_finance_tool.py`
  - [x] Fetch stock price history (configurable period)
  - [x] Fetch financial statements (income, balance sheet, cash flow)
  - [x] Fetch key ratios (PE, market cap, profit margin, debt)
  - [x] Error handling for invalid tickers
- [x] **P2-2** Implement `backend/tools/duckduckgo_tool.py`
  - [x] News search for a given stock/company
  - [x] Return structured results (title, snippet, url, date)
  - [x] Rate limiting / error handling
- [x] **P2-3** Write unit tests for tools (mock external API calls)

---

## Phase 3 · Specialized Agents

### 3A — Fundamental Analyst Agent
- [x] **P3A-1** Create `backend/agents/fundamental_agent.py`
- [x] **P3A-2** Implement LLM prompt for fundamental analysis (revenue, PE, earnings growth, market cap, debt, profit margin)
- [x] **P3A-3** Wire up Yahoo Finance tools
- [x] **P3A-4** Return structured output with fundamental score (X/10)
- [x] **P3A-5** Unit tests with mocked LLM + mocked tools

### 3B — Technical Analyst Agent
- [x] **P3B-1** Create `backend/agents/technical_agent.py`
- [x] **P3B-2** Implement indicator calculations (RSI, MACD, MA50, MA200, trend detection) using pandas-ta
- [x] **P3B-3** Implement LLM prompt for interpretation of indicators
- [x] **P3B-4** Return structured output with technical score (X/10)
- [x] **P3B-5** Unit tests with mocked LLM + sample price data

### 3C — Sentiment Analyst Agent
- [x] **P3C-1** Create `backend/agents/sentiment_agent.py`
- [x] **P3C-2** Implement LLM prompt for sentiment classification of news
- [x] **P3C-3** Wire up DuckDuckGo tool
- [x] **P3C-4** Return structured output with sentiment score (X/10)
- [x] **P3C-5** Unit tests with mocked LLM + mocked search results

### 3D — Master Analyst (Aggregator) Agent
- [x] **P3D-1** Create `backend/agents/master_agent.py`
- [x] **P3D-2** Implement aggregation logic (combine fundamental, technical, sentiment scores)
- [x] **P3D-3** Implement LLM prompt for final recommendation (Buy / Hold / Sell + reasoning)
- [x] **P3D-4** Support comparison mode (Stock A vs Stock B)
- [x] **P3D-5** Unit tests with sample agent outputs

---

## Phase 4 · LangGraph Orchestration
- [x] **P4-1** Create `backend/workflows/market_graph.py`
- [x] **P4-2** Define StateGraph with nodes: `fundamental`, `technical`, `sentiment`, `aggregator`
- [x] **P4-3** Wire edges: START → [fundamental, technical, sentiment] (parallel fan-out)
- [x] **P4-4** Wire edges: [fundamental, technical, sentiment] → aggregator (fan-in)
- [x] **P4-5** Add intent analyzer node at entry point (parse query → extract stock names, analysis type)
- [x] **P4-6** Support single stock analysis, comparison, and portfolio workflows
- [x] **P4-7** Integration tests for full graph execution (mocked LLM + mocked tools)

---

## Phase 5 · FastAPI Backend
- [x] **P5-1** Create `backend/api/fastapi_server.py`
- [x] **P5-2** `POST /analyze_stock` endpoint
- [x] **P5-3** `POST /compare_stocks` endpoint
- [x] **P5-4** `POST /portfolio_analysis` endpoint
- [x] **P5-5** `POST /chat` (free-form query → full pipeline)
- [x] **P5-6** Streaming response support (SSE or chunked JSON)
- [x] **P5-7** Error handling middleware, CORS
- [x] **P5-8** API tests (TestClient, mock workflow layer)

---

## Phase 6 · Streamlit Frontend
- [x] **P6-1** Create `frontend/streamlit_app.py`
- [x] **P6-2** Chat interface (text input → display streamed analysis)
- [x] **P6-3** Stock/portfolio input panel (sidebar)
- [x] **P6-4** Display multi-dimensional analysis results (cards / expandable sections)
- [x] **P6-5** Basic stock price chart (line chart from price history)
- [x] **P6-6** Wire Streamlit → FastAPI backend
- [x] **P6-7** Manual UI testing

---

## Phase 7 · Integration & E2E Testing
- [ ] **P7-1** End-to-end test: single stock query through full pipeline
- [ ] **P7-2** End-to-end test: stock comparison flow
- [ ] **P7-3** End-to-end test: portfolio analysis flow
- [ ] **P7-4** Test error scenarios (invalid ticker, API failures, timeout)
- [ ] **P7-5** Performance test: verify parallel agent execution

---

## Phase 8 · DevOps & Documentation
- [ ] **P8-1** Create `Dockerfile` for backend
- [ ] **P8-2** Create `docker-compose.yml` (backend + frontend services)
- [ ] **P8-3** Add `Makefile` with common commands (install, dev, test, lint, docker-build)
- [ ] **P8-4** Update `README.md` with full setup, usage, and architecture overview
- [ ] **P8-5** Add API documentation (auto-gen via FastAPI /docs)

---

## Phase 9 · Future Enhancements (from §11)
- [ ] **P9-1** Vector database for news memory (e.g. ChromaDB)
- [ ] **P9-2** LLM reasoning chains
- [ ] **P9-3** Event-driven updates (real-time market triggers)
- [ ] **P9-4** Portfolio risk modeling
- [ ] **P9-5** Backtesting engine

---

> **Recommended build order**: P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8
> Phase 9 is stretch / post-MVP.

| Phase | Tasks | Estimated Effort |
|-------|-------|-----------------|
| P0 Scaffolding | 6 | ~1 hr |
| P1 Models | 3 | ~1 hr |
| P2 Tools | 3 | ~2 hrs |
| P3 Agents | 20 | ~6 hrs |
| P4 Orchestration | 7 | ~3 hrs |
| P5 API | 8 | ~3 hrs |
| P6 Frontend | 7 | ~4 hrs |
| P7 E2E Testing | 5 | ~2 hrs |
| P8 DevOps | 5 | ~2 hrs |
| **Total** | **64 tasks** | **~24 hrs** |
