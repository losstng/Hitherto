from __future__ import annotations
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..models import Newsletter
from .cleaning import clean_bloomberg_newsletter


logger = logging.getLogger(__name__)


def chunk_newsletter_text(
    db: Session,
    message_id: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> Newsletter | None:
    """Split extracted text into overlapping chunks and persist them."""
    logger.debug(
        "chunk_newsletter_text called with message_id=%s chunk_size=%d chunk_overlap=%d",
        message_id,
        chunk_size,
        chunk_overlap,
    )
    try:
        newsletter = db.query(Newsletter).filter_by(message_id=message_id).first()
        if not newsletter:
            logger.warning("No newsletter found with message_id: %s", message_id)
            return None
        if not newsletter.extracted_text:
            logger.warning(
                "Newsletter with message_id %s has no extracted text.", message_id
            )
            return None

        try:
            splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", ".", " "],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            cleaned = clean_bloomberg_newsletter(newsletter.extracted_text)
            docs = [Document(page_content=cleaned)]
            chunks = splitter.split_documents(docs)
            chunked_payload = [c.page_content for c in chunks]
        except Exception as split_err:  # pragma: no cover - langchain internals
            logger.error("Error during text splitting: %s", split_err)
            return None

        try:
            newsletter.chunked_text = chunked_payload
            db.commit()
            db.refresh(newsletter)
        except SQLAlchemyError as db_err:
            db.rollback()
            logger.error(
                "Database update failed for message_id %s: %s", message_id, db_err
            )
            return None

        logger.debug("Chunking produced %d chunks", len(chunked_payload))
        return newsletter

    except Exception as e:  # pragma: no cover - defensive
        logger.exception(
            "Unexpected error while chunking newsletter with ID %s: %s",
            message_id,
            e,
        )
        return None
