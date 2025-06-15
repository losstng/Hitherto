# app/routers/ingest.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import ApiResponse
from services.chunking import chunk_newsletter_text
from services.vector import embed_chunked_newsletter
from services.token_counter import compute_token_count_simple
from main import gmail_service
from models import Newsletter

from services.email_service import extract_bloomberg_email_text, scan_bloomberg_emails

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

# retrieve
@router.post("/bloomberg_reload", response_model=ApiResponse)
async def reload_bloomberg_emails(db: Session = Depends(get_db)):
    try:
        if gmail_service is None:
            raise RuntimeError("Gmail service not initialized")

        count = scan_bloomberg_emails(service=gmail_service, db=db)
        return ApiResponse(success=True, data={"new_entries": count})

    except Exception as e:
        return ApiResponse(success=False, error=str(e))

@router.get("/category_filter", response_model=ApiResponse)
def get_newsletters_by_category(category: str = Query(...), db: Session = Depends(get_db)):
    def filter_newsletters_by_category(db: Session, category: str):
        normalized = category.lower().replace(" ", "_")
        results = (
            db.query(Newsletter)
            .filter(Newsletter.category == normalized)
            .order_by(Newsletter.received_at.desc())
            .all()
        )

        return [
            {
                "title": n.title,
                "message_id": n.message_id,
                "received_at": n.received_at,
            }
        for n in results
    ]
    try:
        filtered = filter_newsletters_by_category(db=db, category=category)
        return ApiResponse(success=True, data=filtered)
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


# preprocess
@router.post("/extract_text/{message_id}", response_model=ApiResponse)
def extract_bloomberg_content(message_id: str, db: Session = Depends(get_db)):
    try:
        if gmail_service is None:
            raise RuntimeError("Gmail service is not initialized")

        newsletter = extract_bloomberg_email_text(service=gmail_service, db=db, msg_id=message_id)
        if not newsletter:
            return ApiResponse(success=False, error=f"Extraction failed for {message_id}")

        return ApiResponse(
            success=True,
            data={
                "message_id": newsletter.message_id,
                "title": newsletter.title,
                "category": newsletter.category,
                "extracted_text_preview": newsletter.extracted_text[:250] + "..."  # Just a preview
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=str(e))

@router.post("/chunk/{message_id}")
def chunk_newsletter(message_id: str, db: Session = Depends(get_db)):
    return chunk_newsletter_text(db, message_id)

# process
@router.post("/embed/{message_id}")
def embed_newsletter(message_id: str, db: Session = Depends(get_db)):
    return embed_chunked_newsletter(db, message_id)

# review
@router.post("/tokenize/{message_id}")
def tokenize_newsletter(message_id: str, db: Session = Depends(get_db)):
    return compute_token_count_simple(db, message_id)