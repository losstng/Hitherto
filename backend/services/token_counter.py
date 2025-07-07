import tiktoken
import os
import logging
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from ..models import Newsletter
load_dotenv()

MODEL = os.getenv("MODEL_IN_USE")

def compute_token_count_simple(db: Session, message_id: str, model_name: str = MODEL):
    logging.info(f"Computing token count for {message_id}")
    try:
        import tiktoken  # localize import to ensure modular portability

        # Try to get tokenizer for the specified model
        try:
            tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            tokenizer = tiktoken.get_encoding("cl100k_base")

        # Query the newsletter
        newsletter = db.query(Newsletter).filter_by(message_id=message_id).first()
        if not newsletter:
            logging.warning(f"No newsletter found with message_id: {message_id}")
            return None
        if not newsletter.extracted_text:
            logging.warning(f"Newsletter with message_id {message_id} has no extracted text.")
            return None

        # Count and save
        token_count = len(tokenizer.encode(newsletter.extracted_text))
        newsletter.token_count = token_count
        db.commit()
        db.refresh(newsletter)

        logging.info(f"Token count ({token_count}) stored for newsletter {message_id}")
        return token_count

    except Exception as e:
        db.rollback()
        logging.exception(f"Failed to compute token count for {message_id}: {e}")
        return None