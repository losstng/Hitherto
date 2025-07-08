# Agent Guide for Hitherto Repository

This file provides an overview of the codebase for future automation agents.
It describes the main folders, important scripts, and common commands to help
understand the project quickly.

## Structure

- **backend/** – FastAPI application
  - `main.py` bootstraps the server and registers API routes from `routers/`
  - `routers/` contains REST endpoints for ingesting newsletters and basic query
    functionality.
  - `services/` implements Gmail ingestion, text chunking, token counting and
    vector embedding. Logging is enabled throughout these modules.
  - `models.py`, `database.py` and `schemas.py` define the ORM models and
    Pydantic response classes.
  - `tests/` holds unit tests (run with `pytest -q`).
  - `llm/` and `redis.py` are placeholders for future extensions.

- **frontend/** – Next.js application
  - Uses the App Router with React components under `src/`.
  - `components/` includes UI elements such as the newsletter table and row.
  - `app/actions/` and `hooks/` contain wrappers for API requests and React
    Query helpers.

- **debug_tools/** – Helper scripts for manual Gmail API debugging.

- **credentials.json**, **token.json**, and **.env** contain OAuth credentials
  for Gmail and other secrets. They are currently stored in the repo but should
  be treated as private data.

## Usage

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install frontend packages if needed:
   ```bash
   cd frontend && npm install && cd ..
   ```
3. Run the backend:
   ```bash
   export PYTHONPATH=$(pwd)
   python -m backend.main
   ```
4. Run the frontend:
   ```bash
   cd frontend && npm run dev
   ```

## Tests

Execute the test suite from the repository root:

```bash
pytest -q
```

These tests cover basic debug utilities at the moment.

