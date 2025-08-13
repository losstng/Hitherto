from fastapi import APIRouter
from pydantic import BaseModel
from ..schemas import ApiResponse
from ..services.context import retrieve_context
import logging
from backend.llm.llm import LocalLLMClient
from backend.llm.load_prompt import load_system_prompt

router = APIRouter()
logger = logging.getLogger(__name__)

class AskPayload(BaseModel):
    query: str
    mode: str | None = None
    chunks: list[str] | None = None

class ContextPayload(BaseModel):
    query: str
    categories: list[str]
    start_date: str | None = None
    end_date: str | None = None
    k: int = 5
    message_ids: list[str] | None = None

@router.post("/ask", response_model=ApiResponse)
async def ask(payload: AskPayload):
    logger.info(
        f"Received /ask with query='{payload.query}' mode='{payload.mode}'"
    )
    try:
        if payload.mode == "rag":
            if not payload.chunks:
                logger.warning("No chunks provided for RAG mode")
                return ApiResponse(success=False, error="No context for RAG")

            try:
                system_prompt = load_system_prompt()
            except Exception as perr:
                logger.error(f"Failed to load system prompt: {perr}")
                return ApiResponse(success=False, error="Server missing SystemPrompt.txt. Contact admin.")

            messages = [
                {"role": "system", "content": system_prompt},
            ]
            context_block = "\n---\n".join(payload.chunks)
            messages.append({
                "role": "system",
                "content": f"Relevant context excerpts (retrieved):\n{context_block}"
            })
            messages.append({"role": "user", "content": payload.query})

            try:
                llm = LocalLLMClient()
                llm_reply = llm.complete_chat(messages, max_tokens=512)
            except Exception as llm_err:
                logger.error(f"Local LLM call failed: {llm_err}")
                llm_reply = f"[LLM ERROR: {llm_err}]"
            logger.info(f"LLM reply length: {len(llm_reply) if llm_reply else 0}")
            return ApiResponse(success=True, data={"reply": llm_reply, "source": "rag+local-llm"})

        reply = f"You asked: {payload.query}"
        logger.debug(f"Reply generated: {reply}")
        return ApiResponse(
            success=True, data={"reply": reply, "source": payload.mode or "llm"}
        )
    except Exception as e:
        logger.exception("Error processing /ask")
        return ApiResponse(success=False, error=str(e))

@router.post("/context", response_model=ApiResponse)
async def context_search(payload: ContextPayload):
    logger.info(
        f"Received /context query='{payload.query}' categories={payload.categories}"
    )
    docs = retrieve_context(
        query=payload.query,
        categories=payload.categories,
        start_date=payload.start_date,
        end_date=payload.end_date,
        k=payload.k,
        message_ids=payload.message_ids,
    )
    items = [
        {"page_content": d.page_content, "metadata": d.metadata}
        for d in docs
    ]
    return ApiResponse(success=True, data=items)