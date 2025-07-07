# app/routers/ingest.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import logging
from ..database import get_db
from ..schemas import ApiResponse
from ..services.chunking import chunk_newsletter_text
from ..services.vector import embed_chunked_newsletter
from ..services.token_counter import compute_token_count_simple
from .. import main
from ..models import Newsletter

from ..services.email_service import extract_bloomberg_email_text, scan_bloomberg_emails
from pathlib import Path


router = APIRouter(tags=["Ingestion"])
logger = logging.getLogger(__name__)

# ----- Status ------------------------------------------------------------
@router.get("/gmail_status", response_model=ApiResponse)
def gmail_status():
    """Return whether the Gmail service is connected."""
    return ApiResponse(success=True, data={"connected": main.gmail_service is not None})

# retrieve
@router.post("/bloomberg_reload", response_model=ApiResponse)
async def reload_bloomberg_emails(db: Session = Depends(get_db)):
    logger.info("Starting bloomberg_reload endpoint")
    logger.debug("DB session opened for bloomberg_reload")
    try:
        if main.gmail_service is None:
            logger.error("Gmail service not initialized")
            raise RuntimeError("Gmail service not initialized")

        logger.debug("Invoking scan_bloomberg_emails")
        stored = scan_bloomberg_emails(service=main.gmail_service, db=db)
        logger.debug(f"scan_bloomberg_emails stored {len(stored)} new entries")

        logger.debug("Querying newsletters from DB")
        newsletters = (
            db.query(Newsletter)
            .order_by(Newsletter.received_at.desc())
            .all()
        )
        logger.debug(f"Retrieved {len(newsletters)} newsletters from DB")

        payload = [
            {
                "title": n.title,
                "message_id": n.message_id,
                "category": n.category,
                "received_at": n.received_at.isoformat() if n.received_at else None,
                "has_text": n.extracted_text is not None,
                "has_chunks": bool(n.chunked_text),
            }
            for n in newsletters
        ]

        logger.info("bloomberg_reload completed")
        return ApiResponse(success=True, data=payload)

    except Exception as e:
        logger.exception("Error in bloomberg_reload endpoint")
        return ApiResponse(success=False, error=str(e))
        

@router.get("/category_filter", response_model=ApiResponse)
def get_newsletters_by_category(category: str = Query(...), db: Session = Depends(get_db)):
    logger.info(f"Filtering newsletters by category: {category}")
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
        logger.debug(f"Found {len(filtered)} newsletters for category {category}")
        return ApiResponse(success=True, data=filtered)
    except Exception as e:
        logger.exception("Error in extract_bloomberg_content")
        return ApiResponse(success=False, error=str(e))


# preprocess
@router.post("/extract_text/{message_id}", response_model=ApiResponse)
def extract_bloomberg_content(message_id: str, db: Session = Depends(get_db)):
    logger.info(f"Extracting text for {message_id}")
    try:
        if main.gmail_service is None:
            logger.error("Gmail service is not initialized")
            raise RuntimeError("Gmail service is not initialized")

        # ⇣ helper already does the “skip-if-present” logic
        newsletter = extract_bloomberg_email_text(
            service=main.gmail_service, db=db, message_id=message_id
        )
        if newsletter is None:
            logger.warning(f"Extraction failed for {message_id}")
            return ApiResponse(success=False, error="Extraction failed or no content.")

        logger.info(f"Extraction complete for {message_id}")
        return ApiResponse(
            success=True,
            data={
                "message_id": newsletter.message_id,
                "title":       newsletter.title,
                "category":    newsletter.category,
                "excerpt":     newsletter.extracted_text[:250] + "…",
                "has_text":    True,
            },
        )
    except Exception as e:
        return ApiResponse(success=False, error=str(e))

@router.post("/chunk/{message_id}", response_model=ApiResponse)
def chunk_newsletter(message_id: str, db: Session = Depends(get_db)):
    logger.info(f"Chunking newsletter {message_id}")
    newsletter = chunk_newsletter_text(db, message_id)
    if newsletter:
        logger.info(f"Chunking complete for {message_id}")
        return ApiResponse(success=True, data={"message_id": message_id, "has_chunks": True})
    logger.warning(f"Chunking failed for {message_id}")
    return ApiResponse(success=False, error="Chunking failed or prerequisites missing.")

# process
@router.post("/embed/{message_id}", response_model=ApiResponse)
def embed_newsletter(message_id: str, db: Session = Depends(get_db)):
    """Only embed if chunked_text exists and we have NOT already embedded."""
    logger.info(f"Embedding newsletter {message_id}")
    try:
        newsletter = db.query(Newsletter).filter_by(message_id=message_id).first()
        if not newsletter:
            return ApiResponse(success=False, error="Newsletter not found.")

        if not newsletter.chunked_text:
            return ApiResponse(success=False, error="Chunked text missing. Run /chunk first.")

        # Primitive “already-embedded” check: does dir exist?
        cat   = (newsletter.category or "uncategorized").lower().replace(" ", "_")
        vec_dir = Path("db/faiss_store") / cat
        if (vec_dir / "index.faiss").exists():
            logger.info(f"Newsletter {message_id} already embedded")
            return ApiResponse(success=True, data={"message_id": message_id, "already_embedded": True})

        db_obj = embed_chunked_newsletter(db, message_id)
        if not db_obj:
            logger.warning(f"Embedding failed for {message_id}")
            return ApiResponse(success=False, error="Embedding failed.")
        logger.info(f"Embedding complete for {message_id}")
        return ApiResponse(success=True, data={"message_id": message_id, "embedded": True})

    except Exception as e:
        logger.exception("Error in embed_newsletter")
        return ApiResponse(success=False, error=str(e))

# ----- Review ------------------------------------------------------------
@router.get("/raw_text/{message_id}", response_model=ApiResponse)
def get_raw_text(message_id: str, db: Session = Depends(get_db)):
    """Return previously extracted plain text for a newsletter."""
    logger.debug(f"Fetching raw text for {message_id}")
    n = db.query(Newsletter).filter_by(message_id=message_id).first()
    if not n or not n.extracted_text:
        logger.warning(f"No text available for {message_id}")
        return ApiResponse(success=False, error="Text not available")
    logger.info(f"Returning raw text for {message_id}")
    return ApiResponse(success=True, data={"text": n.extracted_text})

@router.get("/chunked_text/{message_id}", response_model=ApiResponse)
def get_chunked_text(message_id: str, db: Session = Depends(get_db)):
    """Return stored chunked text for a newsletter."""
    logger.debug(f"Fetching chunks for {message_id}")
    n = db.query(Newsletter).filter_by(message_id=message_id).first()
    if not n or not n.chunked_text:
        logger.warning(f"No chunks available for {message_id}")
        return ApiResponse(success=False, error="Chunked text not available")
    logger.info(f"Returning chunks for {message_id}")
    return ApiResponse(success=True, data={"chunks": n.chunked_text})

# review
@router.post("/tokenize/{message_id}")
def tokenize_newsletter(message_id: str, db: Session = Depends(get_db)):
    logger.info(f"Tokenizing newsletter {message_id}")
    count = compute_token_count_simple(db, message_id)
    if count is not None:
        logger.info(f"Token count for {message_id}: {count}")
    else:
        logger.warning(f"Tokenization failed for {message_id}")
    return count
