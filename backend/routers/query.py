from fastapi import APIRouter
from pydantic import BaseModel
from ..schemas import ApiResponse
from ..services.context import retrieve_context
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class AskPayload(BaseModel):
    query: str
    mode: str | None = None

class ContextPayload(BaseModel):
    query: str
    categories: list[str]
    start_date: str | None = None
    end_date: str | None = None
    k: int = 5

@router.post("/ask", response_model=ApiResponse)
async def ask(payload: AskPayload):
    logger.info(f"Received /ask with query='{payload.query}' mode='{payload.mode}'")
    reply = f"You asked: {payload.query}"
    logger.debug(f"Reply generated: {reply}")
    return ApiResponse(success=True, data={"reply": reply, "source": payload.mode or "llm"})


@router.post("/context", response_model=ApiResponse)
async def context_search(payload: ContextPayload):
    """Retrieve context documents filtered by category and optional dates."""
    logger.info(
        f"Received /context query='{payload.query}' categories={payload.categories}"
    )
    docs = retrieve_context(
        query=payload.query,
        categories=payload.categories,
        start_date=payload.start_date,
        end_date=payload.end_date,
        k=payload.k,
    )
    items = [
        {"page_content": d.page_content, "metadata": d.metadata}
        for d in docs
    ]
    return ApiResponse(success=True, data=items)
