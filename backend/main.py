import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from sqlalchemy import text

from . import models
from .database import engine
from .env import CORS_ALLOW_ORIGINS, FASTAPI_PORT, GMAIL_SCOPE, LOG_LEVEL
from .routers import ingest, query, stocks  # Adjust if needed
from .services.email_service import get_authenticated_gmail_service
from .services.price_email import run_price_email_loop
from .services.sec_filings_monitor import run_sec_filings_monitor_loop
from .services.volume_monitor import run_volume_monitor_loop

# ----- Logging Setup -----
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.DEBUG), force=True)
logger = logging.getLogger(__name__)

# ----- Gmail Scope and Service Handle -----
SCOPES = [GMAIL_SCOPE]
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
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Schema update successful and connection verified.")
    except Exception as e:
        logger.exception(f"Schema update failed: {e}")

    yield
    # Optional: any shutdown logic here


# ----- FastAPI App -----
app = FastAPI(lifespan=lifespan)

# ----- Middleware -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
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

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=FASTAPI_PORT,
        reload=True,
    )