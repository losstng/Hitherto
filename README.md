# Hitherto

Hitherto is a small research environment built around a FastAPI backend and a Next.js frontend. The backend ingests Gmail newsletters, vectorizes them for semantic search and exposes a minimal API, while the frontend offers a simple interface for browsing and querying the stored text.

## Quick start

1. *(Optional)* create and activate a virtual environment:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```
2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install frontend packages:
   ```bash
   cd frontend && npm install && cd ..
   ```
4. Provide configuration files:
   - `.env` defines all backend settings and is loaded by `backend/env.py`.
   - `credentials.json` holds the Google OAuth client information.
   - `token.json` will be created after completing the OAuth flow.
5. Start the API server:
   ```bash
   export PYTHONPATH=$(pwd)
   python -m uvicorn backend.main:app --reload --log-level debug \
     --port "${FASTAPI_PORT:-8000}"
   ```
6. In another terminal, launch the frontend:
   ```bash
   cd frontend && npm run dev
   ```

Visit <http://localhost:3000> to use the app.

### Codex lightweight setup

For workflows that only require the pieces used by Codex, install the trimmed
dependency lists instead of the full ones:

- Backend: `pip install -r codex_requirements.txt`
- Frontend: use `frontend/codex_package.json` when installing npm packages.

These files omit machine learning, statistics and notebook dependencies for a
lighter environment.

## Repository layout

- **backend/** – FastAPI service with routers under `routers/` and helpers in `services/`.
- **frontend/** – Next.js application.
  Components and hooks are re-exported via index files and should be imported from `@/components` and `@/hooks`.
- **debug_tools/** – Gmail API debugging helpers.
- **scripts/** – Utility shell commands such as `clean_pycache.sh`.
- **db/** – Local FAISS index stored in `faiss_store/`.
- **SystemPrompt.txt** – Prompt text used for LLM summaries.
- `credentials.json`, `token.json` and `.env` contain sensitive credentials.

## Embedding model cache

The `sentence-transformers/all-MiniLM-L6-v2` model is used for embeddings. If running offline, set `HF_MODEL_DIR` to a directory containing the downloaded model so the services load it from disk.

## Testing

Run the unit tests from the repository root:

```bash
pytest -q
```

## Price email notifier

A background thread in the backend periodically emails current stock
prices through Gmail. Set the recipient, optional tickers and interval
in seconds before launching the server:

```bash
export PRICE_EMAIL_RECIPIENT="you@example.com"
export PRICE_EMAIL_TICKERS="TSLA,MSFT"   # optional
export PRICE_EMAIL_INTERVAL=300           # optional
```

When the FastAPI app starts, a thread sends price updates every
`PRICE_EMAIL_INTERVAL` seconds (default 300) until the server stops. The
module can also be run directly via `python -m backend.services.price_email`.
It requires a Gmail OAuth token with send permission (`gmail.send`).

## API notes

The API routes are implemented in `backend/routers`. `ingest.py` handles newsletter ingestion and `query.py` exposes a simple `/ask` endpoint for question answering. Additional stock-related routes live in `stocks.py`.

## API Checklist

- [ ] **APIs Connect** – verify if Gmail or other providers are connected or disconnected
- [ ] **Reload Bloomberg** – scan and load entries into the database; optional category comes from the frontend
- [ ] **Category Selection** – query the database using existing category attributes
- **Gmail Entries**
  - [ ] **Extract** – parse email text and store it in the database
  - [ ] **Vector** – chunk and vectorize text for retrieval
  - [ ] **Text** – return the raw extracted text
  - [ ] **Select** – to be finished

### Key modules

- `backend/main.py` bootstraps the FastAPI app.
- `backend/routers/ingest.py` ingests Gmail newsletters.
- `backend/routers/query.py` serves the `/ask` endpoint.
- `backend/services/email_service.py` talks to Gmail.
- `backend/services/vector.py` manages embeddings and the FAISS index.
- `backend/services/chunking.py` and `token_counter.py` split text for vectors.
- `frontend/src/app/` contains Next.js routes.
- `frontend/src/components/` holds React components.
- `frontend/src/hooks/` wraps API calls for React Query.
