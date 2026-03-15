# AI Market Analyst – High Level Architecture

## 1. System Overview

The system answers questions like:

* *How is Reliance doing?*
* *How is my portfolio performing?*
* *Compare Tata Motors vs Mahindra & Mahindra*

It works by orchestrating **multiple specialized agents** that analyze the market from different perspectives.

Agents run **in parallel**, and a **Master Analyst Agent** compiles the final answer.

---

# 2. High-Level System Architecture

```
                ┌──────────────────────────┐
                │        Streamlit UI      │
                │  (chat + portfolio view)│
                └─────────────┬────────────┘
                              │
                              │ REST / WebSocket
                              ▼
                     ┌────────────────┐
                     │   FastAPI API  │
                     │ Query Gateway  │
                     └───────┬────────┘
                             │
                             │
                    ┌────────▼─────────┐
                    │   LangGraph      │
                    │  Orchestration   │
                    │  (Master Agent)  │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼───────────────────┐
          │                  │                   │
          ▼                  ▼                   ▼

 ┌──────────────┐   ┌────────────────┐   ┌────────────────┐
 │ Fundamental  │   │ Technical      │   │ Sentiment      │
 │ Analyst      │   │ Analyst        │   │ Analyst        │
 │ Agent        │   │ Agent          │   │ Agent          │
 └──────┬───────┘   └───────┬────────┘   └───────┬────────┘
        │                   │                    │
        ▼                   ▼                    ▼

┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
│ Yahoo Finance│   │ Yahoo Finance│   │ DuckDuckGo       │
│ Financials   │   │ Price Data   │   │ News Search      │
└──────────────┘   └──────────────┘   └──────────────────┘


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

# 3.1 Streamlit UI

Purpose:

User interaction.

Features:

* Ask questions
* Show charts
* Show portfolio performance
* Display AI recommendation

Example UI components:

```
Chat Interface

User:
"Compare Tata Motors and Mahindra"

AI:
Fundamental analysis
Technical analysis
Sentiment analysis
Final recommendation
```

Portfolio input:

```
Portfolio

Tata Motors
Infosys
Mahindra
Reliance
```

---

# 3.2 FastAPI Backend

Acts as **API gateway**.

Responsibilities:

* Accept user queries
* Call LangGraph workflow
* Return streaming responses

Endpoints:

```
POST /analyze_stock
POST /portfolio_analysis
POST /compare_stocks
POST /chat
```

Example request:

```json
{
 "query": "Compare Tata Motors and Mahindra"
}
```

---

# 3.3 LangGraph Orchestration Layer

This is the **heart of the system**.

LangGraph manages:

* agent coordination
* state passing
* parallel execution
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
   Agent       Agent      Agent
      \         |        /
       \        |       /
        ▼       ▼      ▼
        Result Aggregator
               │
               ▼
             END
```

LangGraph state example:

```python
class MarketState(TypedDict):
    query: str
    stocks: list[str]
    fundamental_result: dict
    technical_result: dict
    sentiment_result: dict
    final_decision: str
```

---

# 4. Agent Design

Each agent is a **specialized expert**.

---

# 4.1 Fundamental Analyst Agent

Goal:

Analyze company fundamentals.

Data Source:

Yahoo Finance.

Metrics:

* Revenue
* PE ratio
* Earnings growth
* Market cap
* Debt
* Profit margin

Example output:

```
Reliance Industries

PE Ratio: 24
Revenue growth: 8%
Debt: moderate
Profit margin: 11%

Fundamental Score: 7/10
```

Tools used:

```
YahooFinanceTool
FinancialStatementsTool
```

---

# 4.2 Technical Analyst Agent

Goal:

Analyze **price movement and indicators**.

Data:

Yahoo Finance historical price.

Indicators:

* RSI
* Moving averages
* MACD
* Trend direction

Example output:

```
Tata Motors

RSI: 62
Trend: bullish
MA50 > MA200

Technical Score: 8/10
```

Libraries:

```
pandas
ta-lib / pandas-ta
```

---

# 4.3 Sentiment Analyst Agent

Goal:

Understand **market sentiment**.

Sources:

* News
* Web search

Tools:

```
DuckDuckGo Search
News scraping
```

Example:

```
Latest news sentiment

Positive:
EV expansion news

Negative:
Supply chain concerns

Sentiment score: 6/10
```

---

# 4.4 Master Analyst Agent

This agent combines everything.

Input:

```
fundamental score
technical score
sentiment score
```

Output:

```
Overall rating
Buy / Hold / Sell
Reasoning
```

Example:

```
Tata Motors vs Mahindra

Fundamental:
Mahindra stronger balance sheet

Technical:
Tata Motors stronger trend

Sentiment:
Both neutral

Final recommendation:
BUY Tata Motors (short term)
HOLD Mahindra
```

---

# 5. Tools Layer

Agents interact with tools.

---

## Yahoo Finance Tool

Fetch:

```
stock price
financial statements
market cap
ratios
```

Example:

```python
import yfinance as yf

ticker = yf.Ticker("RELIANCE.NS")
data = ticker.history(period="1y")
```

---

## DuckDuckGo Tool

For news search.

Example queries:

```
Reliance Industries news
Tata Motors EV news
Mahindra stock outlook
```

Libraries:

```
duckduckgo-search
```

---

# 6. Portfolio Analysis Flow

User input:

```
Portfolio

Tata Motors
Infosys
Reliance
```

Workflow:

```
For each stock:

run agents in parallel
↓

collect results
↓

aggregate portfolio risk
↓

final report
```

Output:

```
Portfolio health: GOOD

Best performer:
Tata Motors

Risk:
Infosys slowing growth

Recommendation:
Reduce Infosys exposure
```

---

# 7. LangGraph Execution Flow

Example pseudo-code:

```python
workflow = StateGraph(MarketState)

workflow.add_node("fundamental", fundamental_agent)
workflow.add_node("technical", technical_agent)
workflow.add_node("sentiment", sentiment_agent)
workflow.add_node("aggregator", master_agent)

workflow.add_edge("start", "fundamental")
workflow.add_edge("start", "technical")
workflow.add_edge("start", "sentiment")

workflow.add_edge("fundamental", "aggregator")
workflow.add_edge("technical", "aggregator")
workflow.add_edge("sentiment", "aggregator")

workflow.set_entry_point("start")
workflow.set_finish_point("aggregator")
```

---

# 8. Suggested Project Folder Structure

```
market-analyst-ai
│
├── backend
│   ├── api
│   │   └── fastapi_server.py
│
│   ├── agents
│   │   ├── fundamental_agent.py
│   │   ├── technical_agent.py
│   │   ├── sentiment_agent.py
│   │   └── master_agent.py
│
│   ├── tools
│   │   ├── yahoo_finance_tool.py
│   │   └── duckduckgo_tool.py
│
│   ├── workflows
│   │   └── market_graph.py
│
│   └── models
│       └── state.py
│
├── frontend
│   └── streamlit_app.py
│
├── requirements.txt
└── README.md
```

---

# 9. Example User Query Flow

User asks:

```
Compare Tata Motors and Mahindra
```

Flow:

```
Streamlit
 ↓
FastAPI
 ↓
LangGraph
 ↓
Agents run in parallel

Fundamental
Technical
Sentiment

 ↓
Master agent aggregates
 ↓
Final response returned
```

---

# 10. Example Final Response

```
Comparison: Tata Motors vs Mahindra

Fundamental Analysis
Mahindra has stronger margins.

Technical Analysis
Tata Motors showing strong bullish momentum.

Sentiment
Both neutral in news sentiment.

Final Verdict

Short Term: BUY Tata Motors
Long Term: HOLD Mahindra
```

---

# 11. Future Enhancements

You can make this **very powerful** later.

Add:

* **Vector database for news memory**
* **LLM reasoning chains**
* **event-driven updates**
* **portfolio risk modeling**
* **backtesting engine**
