# Hitherto

## Running the backend

The FastAPI server now reads the `FASTAPI_PORT` environment variable (falling
back to `PORT` or `8000`) when started directly. This prevents the port from
changing unexpectedly across restarts.

```bash
export PYTHONPATH=$(pwd)
python -m backend.main
```
