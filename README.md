# Hitherto
# Hitherto

This project contains a FastAPI backend and a Next.js frontend. The backend
provides a small API for ingesting newsletters and querying them with language
models, while the frontend offers a basic interface for exploration.

## Setup

1. Install the Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install the frontend packages (optional if you only want the API):

```bash
cd frontend
npm install
cd ..
```

## Running the backend

The server reads the `FASTAPI_PORT` environment variable (falling back to
`PORT` or `8000`) so the port remains consistent across restarts. You can set up
the environment and start the application with:

```bash
export PYTHONPATH=$(pwd)
export FASTAPI_PORT=8000  # choose any port you like
python -m backend.main
```

If you prefer running `uvicorn` directly:

```bash
python -m uvicorn backend.main:app --reload --log-level debug \
  --port "${FASTAPI_PORT:-8000}"
```

## Running the frontend

```bash
cd frontend
npm run dev
```

Navigate to <http://localhost:3000> in your browser.

## Notes for large language models

The available API routes are defined under `backend/routers`. `ingest.py`
handles newsletter ingestion and `query.py` exposes a simple `/ask` endpoint for
question answering. LLMs can read this README to quickly understand how to start
the backend and interact with these routes.
