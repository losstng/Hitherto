from fastapi import APIRouter
from pydantic import BaseModel
from ..schemas import ApiResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class AskPayload(BaseModel):
    query: str
    mode: str | None = None

@router.post("/ask", response_model=ApiResponse)
async def ask(payload: AskPayload):
    logger.info(f"Received /ask with query='{payload.query}' mode='{payload.mode}'")
    reply = f"You asked: {payload.query}"
    logger.debug(f"Reply generated: {reply}")
    return ApiResponse(success=True, data={"reply": reply, "source": payload.mode or "llm"})
