# Agent Guide for Hitherto Repository

This document explains the layout of the project and the quickest way for automation agents (or humans) to get the system running.

## LLM Reasoning Orientation

Hitherto is an ever-evolving framework built around large language models as the core reasoning engine. Every module focuses on supplying structured context so an LLM—invoked via API key—can reason about decisions according to the module's role. When extending the system, prioritize providing clear information for the LLM to interpret and act upon rather than encoding heavy logic directly in code.

## Structure

- **backend/** – FastAPI application
  - `main.py` bootstraps the server and registers API routes from `routers/`.
  - `routers/` exposes endpoints for newsletter ingestion (`ingest.py`), querying (`query.py`) and stock data (`stocks.py`).
  - `services/` implements Gmail ingestion, text chunking, token counting and vector embedding. Logging is enabled throughout these modules.
  - `env.py` loads `.env` and provides configuration values to other modules.
  - `models.py`, `database.py` and `schemas.py` define the ORM models and Pydantic response classes.
  - `tests/` holds unit tests (run with `pytest -q`).
  - `llm/` and `redis.py` are placeholders for future extensions.

- **frontend/** – Next.js application using the App Router.
  - `components/` contains UI elements such as the newsletter table and re-exports them via `index.ts` so they can be imported from `@/components`.
  - `app/actions/` and `hooks/` wrap API requests and React Query helpers. Hooks are re-exported through `index.ts` and imported from `@/hooks`.

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
   - `.env` listing all backend variables read by `backend/env.py`.
   - `credentials.json` downloaded from Google Cloud for OAuth.
   - `token.json` will be generated automatically after completing the OAuth flow.

### Required environment variables

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Database connection string |
| `FASTAPI_PORT` | Port for FastAPI server |
| `GMAIL_SCOPE` | OAuth scopes for Gmail access |
| `MODEL_IN_USE` | Default LLM model name |
| `HF_MODEL_DIR` | Optional path for offline HuggingFace models |

Example `.env` snippet:

```env
DATABASE_URL=sqlite:///db/hitherto.db
FASTAPI_PORT=8000
GMAIL_SCOPE=https://www.googleapis.com/auth/gmail.modify
MODEL_IN_USE=gpt-3.5-turbo
```
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

## Important modules

- `backend/main.py` – entry point configuring the FastAPI application and routes.
- `backend/routers/ingest.py` – Gmail ingestion endpoint.
- `backend/routers/query.py` – question-answering endpoint.
- `backend/routers/stocks.py` – simple stock information routes.
- `backend/services/email_service.py` – functions for pulling email from Gmail.
- `backend/services/chunking.py` – text chunking helpers.
- `backend/services/vector.py` – embedding generation and vector store logic.
- `backend/services/token_counter.py` – counts tokens for splitting text.
- `backend/tests/` – unit tests run with `pytest -q`.
- `frontend/src/app/` – Next.js routes used by the UI.
- `frontend/src/components/` – shared React components.
- `frontend/src/hooks/` – React hooks wrapping API calls.
## Agents directory

The `agents/` folder hosts resources for LLM-based modules.

- `agents/modules/` — one markdown per doctrine module summarizing roles and version differences.
- `agents/legacy/` — archived prompt files and earlier agent artifacts.

Refer to `agents/README.md` for details.
