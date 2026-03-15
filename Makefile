.PHONY: install dev-backend dev-frontend dev-streamlit dev test lint docker-build

install:
	pip3 install --break-system-packages -r requirements.txt
	cd react-directory && npm install

dev-backend:
	python3 -m uvicorn backend.api.fastapi_server:app --reload --port 8000

dev-frontend:
	cd react-directory && npm run dev

dev-streamlit:
	streamlit run frontend/streamlit_app.py --server.port 8501

dev:
	# Run both in parallel using a simple bash trick or just use two terminals.
	# Standard dev command runs backend in background and frontend in foreground
	python3 -m uvicorn backend.api.fastapi_server:app --reload --port 8000 & \
	cd react-directory && npm run dev

test:
	pytest tests/
	cd react-directory && npm run test

lint:
	flake8 backend/ tests/
	cd react-directory && npm run lint

docker-build:
	docker build -t market-analyst-ai .
