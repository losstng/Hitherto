gmail_service = None
from fastapi import FastAPI, Request
from .services.email_service import get_authenticated_gmail_service
from fastapi.middleware.cors import CORSMiddleware
import logging
from .database import engine
from . import models
from contextlib import asynccontextmanager
from fastapi.routing import APIRoute
import os
from .routers import ingest, query  # Adjust based on actual folder structure
import pickle
#  export PYTHONPATH=$(pwd)
# Run with: python -m uvicorn backend.main:app --reload --log-level debug
# redis-server

# Force reconfiguration so our app logs show even when uvicorn
# sets up logging before importing this module.
logging.basicConfig(level=logging.INFO, force=True)
SCOPES = [os.getenv("GMAIL_SCOPE")]
gmail_service = None  # global handle

@asynccontextmanager
async def lifespan(app: FastAPI):
    global gmail_service
    gmail_service = get_authenticated_gmail_service()
    if gmail_service:
        logging.info("Gmail service authenticated on startup.")
    else:
        logging.error("Failed to authenticate Gmail service on startup.")
    yield

app = FastAPI(lifespan=lifespan)

models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend origin explicitly for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(query.router, tags=["Query"])

# Log available routes on startup
for route in app.routes:
    if isinstance(route, APIRoute):
        logging.info(f"{route.path} -> {route.methods}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("FASTAPI_PORT", os.getenv("PORT", 8000)))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)

