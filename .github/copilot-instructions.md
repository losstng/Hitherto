## Hitherto — Copilot / AI agent instructions

Purpose: give an AI coding agent the minimal, precise project knowledge needed to be immediately productive in this repository.

Keep responses small and actionable. When proposing edits, prefer minimal, single-purpose changes and include a short changelog and required test commands.

1) Big-picture architecture (what matters)
- Backend: `backend/` is a FastAPI app. Entry point: `backend/main.py`. Routes are under `backend/routers/` (notably `ingest.py`, `query.py`, `stocks.py`). Services live in `backend/services/` and contain core logic for Gmail ingestion, chunking, token counting and vector embeddings.
- Frontend: `frontend/` is Next.js (App Router). UI code lives under `frontend/src/app/`, components under `frontend/src/components/`, hooks under `frontend/src/hooks/`.
- Persistence & retrieval: embeddings and semantic index are in `db/faiss_store/`. Embedding code is in `backend/services/vector.py` and chunking in `backend/services/chunking.py`.
- Agents: `agents/` contains doctrine markdowns and legacy prompt artifacts; agent behaviour is primarily driven by structured prompt content rather than heavy business logic.

2) Critical developer workflows (commands you will invoke)
- Install backend deps: `pip install -r requirements.txt` (or `pip install -r codex_requirements.txt` for a lightweight dev setup).
- Install frontend deps: `cd frontend && npm install`.
- Run tests from repo root: `pytest -q`.
- Start backend (development):
  - Ensure `PYTHONPATH` includes repo root (the code expects imports relative to repository). Example (POSIX shown; on Windows use equivalent):
    - `export PYTHONPATH=$(pwd)` then
    - `python -m uvicorn backend.main:app --reload --port ${FASTAPI_PORT:-8000}`
  - The server spawns a background price-email thread if `PRICE_EMAIL_RECIPIENT` is set.
- Start frontend: `cd frontend && npm run dev` (visits at http://localhost:3000).

3) Project-specific conventions & patterns
- LLM-first design: modules prioritize structured context for LLMs. When adding functionality, prefer clear, testable context outputs (structured JSON or Pydantic models) for LLM consumption over embedding complex decision logic inline.
- Re-exports: frontend crates re-export components and hooks via `index.ts` files; import from `@/components` or `@/hooks` rather than deep paths.
- Small runnable scripts: many helpers live under `debug_tools/` and `scripts/` — prefer calling these for reproducible local tasks (e.g., `scripts/clean_pycache.sh`).
- Embedding model: repo expects `sentence-transformers/all-MiniLM-L6-v2` by default and supports `HF_MODEL_DIR` for offline use. Check `backend/services/vector.py` for loading logic.

4) Integration points & external dependencies
- Gmail / OAuth: `credentials.json` + `token.json` are used by `backend/services/email_service.py` and `backend/routers/ingest.py`. These are sensitive; do not send contents to external LLMs without redaction.
- LLM provider: configuration via `.env` (`MODEL_IN_USE`) and `SystemPrompt.txt`. The code uses configurable adapters in `llm/` and services that call the model.
- Vector store: FAISS files under `db/faiss_store/` — modifications here affect retrieval. `backend/services/vector.py` is the ground truth for how vectors are read/written.

5) Files and locations to reference when answering or changing code (high signal)
- `backend/main.py` — app bootstrap, middleware, router registration.
- `backend/routers/ingest.py` — ingestion flow and Gmail integration.
- `backend/routers/query.py` — QA endpoint and how context is passed to the LLM.
- `backend/services/` — especially `email_service.py`, `chunking.py`, `vector.py`, `token_counter.py`.
- `db/faiss_store/` — stored index files, check consistency before editing vector logic.
- `agents/modules/` — domain-specific prompts and doctrines; mirror changes between code and agent docs.

6) Safe-edit rules for Copilot/agents
- Never commit credentials from `.env`, `credentials.json`, or `token.json` — treat them as secrets. If a patch would expose them, abort and request explicit user instruction.
- Prefer creating small branches/PRs for multi-file changes. If applying edits directly, include a test that demonstrates the change.
- When code interacts with the FAISS store or replaces the embedding model, include a migration or reindex step and document expected runtime/cost.

7) Examples of project-specific tasks and how to execute them
- Add a new router: create `backend/routers/myrouter.py`, register it in `backend/main.py`, add tests in `backend/tests/test_myrouter.py`, run `pytest -q`.
- Update embedding model path: set `HF_MODEL_DIR` in `.env`, confirm `backend/services/vector.py` loads it and run a reindex (review `backend/services/vector.py` for example script).
- Recreate FAISS index: inspect `backend/services/vector.py` and `backend/services/chunking.py` to run the chunk->embed->index pipeline; ensure the db/faiss_store backup is saved.

8) Discovery & references
- Agent guidance and higher-level doctrine live in `AGENTS.md` and `agents/README.md`. Use these to align any agent-facing changes.
- System prompt: `SystemPrompt.txt` contains the default LLM system message used in the project.

If anything in this file is unclear or you need examples for a specific task (e.g., reindex steps, test harness for a router, or a safe PR template), tell me which area to expand and I'll iterate.
