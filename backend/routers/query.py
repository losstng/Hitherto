from fastapi import APIRouter
from pydantic import BaseModel
from ..schemas import ApiResponse

router = APIRouter()

class AskPayload(BaseModel):
    query: str
    mode: str | None = None

@router.post("/ask", response_model=ApiResponse)
async def ask(payload: AskPayload):
    reply = f"You asked: {payload.query}"
    return ApiResponse(success=True, data={"reply": reply, "source": payload.mode or "llm"})
