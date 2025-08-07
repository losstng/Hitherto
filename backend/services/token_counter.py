from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..env import MODEL_IN_USE
from ..models import Newsletter

MODEL = MODEL_IN_USE
logger = logging.getLogger(__name__)


def compute_token_count_simple(
    db: Session, message_id: str, model_name: str = MODEL
) -> Optional[int]:
    """Compute and persist the token count for a newsletter."""
    logger.debug(
        "compute_token_count_simple called with message_id=%s model=%s",
        message_id,
        model_name,
    )
    try:
        import tiktoken  # local import for optional dependency

        try:
            tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            tokenizer = tiktoken.get_encoding("cl100k_base")

        newsletter = db.query(Newsletter).filter_by(message_id=message_id).first()
        if not newsletter:
            logger.warning("No newsletter found with message_id: %s", message_id)
            return None
        if not newsletter.extracted_text:
            logger.warning(
                "Newsletter with message_id %s has no extracted text.", message_id
            )
            return None

        token_count = len(tokenizer.encode(newsletter.extracted_text))
        newsletter.token_count = token_count
        db.commit()
        db.refresh(newsletter)

        logger.info(
            "Token count (%d) stored for newsletter %s", token_count, message_id
        )
        return token_count

    except Exception as e:  # pragma: no cover - external issues
        db.rollback()
        logger.exception("Failed to compute token count for %s: %s", message_id, e)
        return None
