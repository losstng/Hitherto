import os
import logging
import threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from contextlib import asynccontextmanager
from sqlalchemy import text

from .services.email_service import get_authenticated_gmail_service
from .services.price_email import run_price_email_loop
from .services.volume_monitor import run_volume_monitor_loop
from .services.sec_filings_monitor import run_sec_filings_monitor_loop
from .database import engine
from . import models
from .routers import ingest, query, stocks  # Adjust if needed

# ----- Logging Setup -----
logging.basicConfig(level=logging.DEBUG, force=True)
logger = logging.getLogger(__name__)

# ----- Gmail Scope and Service Handle -----
SCOPES = [os.getenv("GMAIL_SCOPE")]
gmail_service = None  # Global handle

# ----- Lifespan Context Manager -----
@asynccontextmanager
async def lifespan(app: FastAPI):
    global gmail_service

    # Gmail authentication
    logger.info("Starting Gmail authentication...")
    gmail_service = get_authenticated_gmail_service()
    if gmail_service:
        logger.info("Gmail service authenticated on startup.")
    else:
        logger.error("Failed to authenticate Gmail service on startup.")

    # Start price and volume notifications in background threads
    threading.Thread(target=run_price_email_loop, daemon=True).start()
    threading.Thread(target=run_volume_monitor_loop, daemon=True).start()
    threading.Thread(target=run_sec_filings_monitor_loop, daemon=True).start()

    # Database setup
    try:
        logger.info("Connecting to DB for schema update...")
        models.Base.metadata.create_all(bind=engine)
        logger.info("Schema update successful.")
    except Exception as e:
        logger.exception(f"Schema update failed: {e}")

    yield
    # Optional: any shutdown logic here

# ----- FastAPI App -----
app = FastAPI(lifespan=lifespan)

# ----- Middleware -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider restricting for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Routers -----
app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(query.router, tags=["Query"])
app.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])

# ----- Sanity Check Route -----
@app.get("/")
def root():
    return {"status": "ok"}

# ----- Log Routes -----
for route in app.routes:
    if isinstance(route, APIRoute):
        logger.info(f"Route registered: {route.path} -> {route.methods}")

# ----- Uvicorn Entry Point -----
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("FASTAPI_PORT", os.getenv("PORT", 8000)))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
