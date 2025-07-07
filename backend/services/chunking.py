from ..models import Newsletter
from sqlalchemy.exc import SQLAlchemyError
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
import logging

def chunk_newsletter_text(db: Session, message_id: str, chunk_size=500, chunk_overlap=100):
    logging.info(f"Chunking text for newsletter {message_id}")
    try:
        newsletter = db.query(Newsletter).filter_by(message_id=message_id).first()
        if not newsletter:
            logging.warning(f"No newsletter found with message_id: {message_id}")
            return None
        if not newsletter.extracted_text:
            logging.warning(f"Newsletter with message_id {message_id} has no extracted text.")
            return None

        try:
            splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", ".", " "],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            docs = [Document(page_content=newsletter.extracted_text)]
            chunks = splitter.split_documents(docs)
            chunked_payload = [c.page_content for c in chunks]
            logging.debug(f"Generated {len(chunked_payload)} chunks")
        except Exception as split_err:
            logging.error(f"Error during text splitting: {split_err}")
            return None

        try:
            newsletter.chunked_text = chunked_payload
            db.commit()
            db.refresh(newsletter)
        except SQLAlchemyError as db_err:
            db.rollback()
            logging.error(f"Database update failed for message_id {message_id}: {db_err}")
            return None

        logging.info(f"Chunking stored for newsletter {message_id}")
        return newsletter

    except Exception as e:
        logging.exception(f"Unexpected error while chunking newsletter with ID {message_id}: {e}")
        return None