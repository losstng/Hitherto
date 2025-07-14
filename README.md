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
   - `.env` defines `DATABASE_URL`, `GMAIL_SCOPE`, and other OAuth details.
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

The sidebar also links to an **Analytics** page with a lightweight Jupyter-style notebook backed by the FastAPI API. A sidebar lists available notebooks and lets you create, open, rename or delete them. Changes are saved automatically and you can manually save at any time using the **Save Notebook** button. When switching notebooks or creating a new one the previous kernel shuts down so no orphan sessions linger. Autosave waits until a notebook finishes loading, and a **Reload List** button refreshes the file list on demand.

## Repository layout

- **backend/** – FastAPI service with routers under `routers/` and helpers in `services/`.
- **frontend/** – Next.js application.
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
