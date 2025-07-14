# Agent Guide for Hitherto Repository

This document explains the layout of the project and the quickest way for automation agents (or humans) to get the system running.

## Structure

- **backend/** – FastAPI application
  - `main.py` bootstraps the server and registers API routes from `routers/`.
  - `routers/` exposes endpoints for newsletter ingestion (`ingest.py`), querying (`query.py`) and stock data (`stocks.py`).
  - `services/` implements Gmail ingestion, text chunking, token counting and vector embedding. Logging is enabled throughout these modules.
  - `models.py`, `database.py` and `schemas.py` define the ORM models and Pydantic response classes.
  - `tests/` holds unit tests (run with `pytest -q`).
  - `llm/` and `redis.py` are placeholders for future extensions.

- **frontend/** – Next.js application using the App Router.
  - `components/` contains UI elements such as the newsletter table.
  - `app/actions/` and `hooks/` wrap API requests and React Query helpers.
  - The Analytics page exposes a lightweight notebook interface (the former
    variables panel has been removed).

- **debug_tools/** – Helper scripts for manual Gmail API debugging.
- **scripts/** – Utility shell scripts such as `clean_pycache.sh`.
- **db/** – Contains the local FAISS vector index in `faiss_store/`.
- **SystemPrompt.txt** – Default system prompt used for LLM summaries.
- **credentials.json**, **token.json** and **.env** store OAuth and database secrets.

## Quick initialization

1. *(Optional)* create and activate a Python virtual environment:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install frontend packages:
   ```bash
   cd frontend && npm install && cd ..
   ```
4. Ensure the following configuration files exist:
   - `.env` with variables like `DATABASE_URL`, `GMAIL_SCOPE`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and `REDIRECT_URI`.
   - `credentials.json` downloaded from Google Cloud for OAuth.
   - `token.json` will be generated automatically after completing the OAuth flow.
5. Run the test suite to confirm the environment:
   ```bash
   pytest -q
   ```
6. Start the backend server:
   ```bash
   export PYTHONPATH=$(pwd)
   python -m uvicorn backend.main:app --reload --log-level debug \
     --port "${FASTAPI_PORT:-8000}"
   ```
7. Start the frontend in a separate terminal:
   ```bash
   cd frontend && npm run dev
   ```

## Secrets

`credentials.json`, `token.json` and `.env` contain sensitive OAuth tokens and database credentials. Keep these files private and avoid committing new secrets to version control.

## Development cleanup

Python bytecode is disabled via the `.envrc` file which sets `PYTHONDONTWRITEBYTECODE=1`. If any `__pycache__` directories appear, run `scripts/clean_pycache.sh`.
