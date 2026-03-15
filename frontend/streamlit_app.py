"""
Streamlit Frontend – AI Market Analyst UI.

Features:
  - Chat interface for free-form market questions
  - Single stock analysis
  - Stock comparison
  - Portfolio analysis panel
  - Results display with scores and charts
"""

from __future__ import annotations

import logging

import requests
import streamlit as st

logger = logging.getLogger("market_analyst.frontend")

# ── Config ────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000"

# ── Page Config ───────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Market Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .score-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
        border: 1px solid #0f3460;
    }
    .score-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .buy { color: #00e676; }
    .sell { color: #ff5252; }
    .hold { color: #ffd740; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── API Helpers ───────────────────────────────────────────────────


def call_api(endpoint: str, payload: dict) -> dict | None:
    """Call the FastAPI backend and return JSON response."""
    url = f"{API_BASE_URL}{endpoint}"
    logger.info("Calling API: %s %s", url, payload)
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        logger.info("API response received: %d bytes", len(str(data)))
        return data
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Make sure the API is running on port 8000.")
        logger.error("Connection error to %s", url)
        return None
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. Analysis may take longer for multiple stocks.")
        logger.error("Timeout calling %s", url)
        return None
    except Exception as e:
        st.error(f"❌ API error: {e}")
        logger.error("API error: %s", e)
        return None


# ── Display Functions ─────────────────────────────────────────────


def display_score(label: str, score: float, max_score: float = 10.0):
    """Display a score as a progress bar with value."""
    color = "buy" if score >= 7 else "hold" if score >= 4 else "sell"
    st.markdown(f"""
    <div class="score-card">
        <div style="font-size: 0.9rem; color: #aaa;">{label}</div>
        <div class="score-value {color}">{score:.1f}<span style="font-size: 1rem; color: #666;">/{max_score:.0f}</span></div>
    </div>
    """, unsafe_allow_html=True)


def display_recommendation(rec: str, reasoning: str):
    """Display the final recommendation prominently."""
    color_map = {"BUY": "buy", "SELL": "sell", "HOLD": "hold"}
    emoji_map = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}

    css_class = color_map.get(rec, "hold")
    emoji = emoji_map.get(rec, "🟡")

    st.markdown(f"""
    <div class="score-card" style="text-align: center;">
        <div style="font-size: 1rem; color: #aaa;">Final Recommendation</div>
        <div style="font-size: 3rem; font-weight: 800;" class="{css_class}">{emoji} {rec}</div>
    </div>
    """, unsafe_allow_html=True)

    if reasoning:
        st.info(f"**Reasoning:** {reasoning}")


def display_stock_analysis(stock_data: dict):
    """Display detailed analysis for one stock."""
    ticker = stock_data.get("stock", "Unknown")
    st.subheader(f"📊 {ticker}")

    fundamental = stock_data.get("fundamental", {})
    technical = stock_data.get("technical", {})
    sentiment = stock_data.get("sentiment", {})

    # Score cards in 3 columns
    c1, c2, c3 = st.columns(3)
    with c1:
        display_score("Fundamental", fundamental.get("score", 0))
    with c2:
        display_score("Technical", technical.get("score", 0))
    with c3:
        display_score("Sentiment", sentiment.get("score", 0))

    # Detailed tabs
    tab1, tab2, tab3 = st.tabs(["📋 Fundamental", "📈 Technical", "📰 Sentiment"])

    with tab1:
        if fundamental.get("summary"):
            st.write(fundamental["summary"])
        col1, col2 = st.columns(2)
        with col1:
            if fundamental.get("pe_ratio"):
                st.metric("PE Ratio", f"{fundamental['pe_ratio']:.1f}")
            if fundamental.get("revenue"):
                st.metric("Revenue", fundamental["revenue"])
            if fundamental.get("market_cap"):
                st.metric("Market Cap", fundamental["market_cap"])
        with col2:
            if fundamental.get("earnings_growth"):
                st.metric("Earnings Growth", fundamental["earnings_growth"])
            if fundamental.get("profit_margin"):
                st.metric("Profit Margin", fundamental["profit_margin"])
            if fundamental.get("debt"):
                st.metric("Debt Level", fundamental["debt"])

    with tab2:
        if technical.get("summary"):
            st.write(technical["summary"])
        col1, col2 = st.columns(2)
        with col1:
            if technical.get("rsi") is not None:
                st.metric("RSI", f"{technical['rsi']:.1f}")
            if technical.get("trend"):
                trend_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}
                st.metric("Trend", f"{trend_emoji.get(technical['trend'], '')} {technical['trend'].title()}")
        with col2:
            if technical.get("ma50") is not None:
                st.metric("MA50", f"{technical['ma50']:.2f}")
            if technical.get("ma200") is not None:
                st.metric("MA200", f"{technical['ma200']:.2f}")
            if technical.get("macd"):
                st.metric("MACD", technical["macd"])

    with tab3:
        if sentiment.get("summary"):
            st.write(sentiment["summary"])
        pos = sentiment.get("positive_signals", [])
        neg = sentiment.get("negative_signals", [])
        if pos:
            st.success("**Positive Signals:**")
            for s in pos:
                st.write(f"  ✅ {s}")
        if neg:
            st.error("**Negative Signals:**")
            for s in neg:
                st.write(f"  ⚠️ {s}")
        if not pos and not neg:
            st.info("No significant signals detected.")


def display_results(data: dict):
    """Display full analysis results."""
    if not data:
        return

    # Recommendation banner
    display_recommendation(
        data.get("recommendation", "HOLD"),
        data.get("reasoning", ""),
    )

    st.divider()

    # Per-stock analysis
    stocks = data.get("stocks", [])
    for stock_data in stocks:
        display_stock_analysis(stock_data)
        st.divider()


# ── Sidebar ───────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="main-header">AI Market Analyst</div>', unsafe_allow_html=True)
    st.caption("Multi-agent AI system for Indian stock market analysis")

    st.divider()

    mode = st.radio(
        "Analysis Mode",
        ["💬 Chat", "📊 Single Stock", "⚖️ Compare Stocks", "📁 Portfolio"],
        index=0,
    )

    st.divider()

    st.markdown("### 🛠️ Settings")
    api_url = st.text_input("API URL", value=API_BASE_URL)
    if api_url != API_BASE_URL:
        API_BASE_URL = api_url

    st.divider()
    st.caption("Built with LangGraph + Gemini + FastAPI")


# ── Main Content ──────────────────────────────────────────────────

st.markdown('<div class="main-header">📈 AI Market Analyst</div>', unsafe_allow_html=True)

if mode == "💬 Chat":
    st.markdown("### Ask any market question")

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and isinstance(msg["content"], dict):
                display_results(msg["content"])
            else:
                st.write(msg["content"])

    # Chat input
    if prompt := st.chat_input("e.g. How is Reliance doing?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🔍 Analyzing..."):
                data = call_api("/chat", {"query": prompt})
                if data:
                    display_results(data)
                    st.session_state.messages.append({"role": "assistant", "content": data})
                else:
                    st.warning("Could not get analysis. Check backend connection.")

elif mode == "📊 Single Stock":
    st.markdown("### Analyze a Single Stock")

    ticker = st.text_input(
        "Stock Ticker",
        placeholder="e.g. RELIANCE.NS",
        help="Use NSE format: RELIANCE.NS, TCS.NS, INFY.NS",
    )

    if st.button("🔍 Analyze", type="primary", disabled=not ticker):
        with st.spinner(f"Analyzing {ticker}..."):
            data = call_api("/analyze_stock", {"stock": ticker})
            if data:
                display_results(data)

elif mode == "⚖️ Compare Stocks":
    st.markdown("### Compare Two Stocks")

    col1, col2 = st.columns(2)
    with col1:
        stock_a = st.text_input("Stock A", placeholder="e.g. TATAMOTORS.NS")
    with col2:
        stock_b = st.text_input("Stock B", placeholder="e.g. M&M.NS")

    if st.button("⚖️ Compare", type="primary", disabled=not (stock_a and stock_b)):
        with st.spinner(f"Comparing {stock_a} vs {stock_b}..."):
            data = call_api("/compare_stocks", {"stock_a": stock_a, "stock_b": stock_b})
            if data:
                display_results(data)

elif mode == "📁 Portfolio":
    st.markdown("### Portfolio Analysis")

    st.markdown("Enter your portfolio stocks (one per line):")
    portfolio_text = st.text_area(
        "Stocks",
        placeholder="RELIANCE.NS\nTCS.NS\nINFY.NS\nHDFCBANK.NS",
        height=150,
        label_visibility="collapsed",
    )

    stocks = [s.strip() for s in portfolio_text.split("\n") if s.strip()]

    if stocks:
        st.caption(f"📊 {len(stocks)} stocks in portfolio")

    if st.button("📁 Analyze Portfolio", type="primary", disabled=not stocks):
        with st.spinner(f"Analyzing {len(stocks)} stocks..."):
            data = call_api("/portfolio_analysis", {"stocks": stocks})
            if data:
                display_results(data)
