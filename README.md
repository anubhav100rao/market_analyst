# AI Market Analyst

AI-powered multi-agent system for stock market analysis. Uses specialized agents (Fundamental, Technical, Sentiment) orchestrated via LangGraph, with a FastAPI backend and Streamlit frontend.

## Quick Start

```bash
# 1. Clone & enter the project
cd market-analyst-ai

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 5. Run tests
pytest

# 6. Start the backend
uvicorn backend.api.fastapi_server:app --reload

# 7. Start the frontend (in another terminal)
streamlit run frontend/streamlit_app.py
```

## Project Structure

```
market-analyst-ai/
├── backend/
│   ├── api/              # FastAPI endpoints
│   ├── agents/           # Specialized analyst agents
│   ├── tools/            # Yahoo Finance, DuckDuckGo integrations
│   ├── workflows/        # LangGraph orchestration
│   ├── models/           # State & Pydantic schemas
│   └── config.py         # Logging & env config
├── frontend/             # Streamlit UI
├── tests/                # Unit & integration tests
├── docs/                 # Architecture & planning docs
├── requirements.txt
└── pyproject.toml
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system design.

## License

MIT
