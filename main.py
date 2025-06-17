gmail_service = None
from fastapi import FastAPI, Request
from services.email_service import get_authenticated_gmail_service  # adjust path
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import engine
import models
from contextlib import asynccontextmanager
from fastapi.routing import APIRoute
import os
from routers import ingest # query  # Adjust based on actual folder structure
import pickle
#  export PYTHONPATH=$(pwd)
# =>. python3 -m uvicorn main:app --reload --log-level debug
# redis-server
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
# app.include_router(query.router, prefix="/query", tags=["Query"])

# Log available routes on startup
for route in app.routes:
    if isinstance(route, APIRoute):
        logging.info(f"{route.path} -> {route.methods}")