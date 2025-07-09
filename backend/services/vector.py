from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from sqlalchemy.orm import Session
from ..models import Newsletter
from pathlib import Path
from datetime import datetime
import logging
import os

def embed_chunked_newsletter(
    db: Session, message_id: str, persist_dir: str = "db/faiss_store"
) -> FAISS | None:
    logger = logging.getLogger(__name__)
    logger.debug(
        "embed_chunked_newsletter called with message_id=%s persist_dir=%s",
        message_id,
        persist_dir,
    )
    try:
        newsletter = db.query(Newsletter).filter_by(message_id=message_id).first()
        if not newsletter:
            logging.warning(f"No newsletter found with message_id: {message_id}")
            return None
        if not newsletter.chunked_text:
            logging.warning(f"Newsletter with message_id {message_id} has no chunked text to embed.")
            return None
        if not isinstance(newsletter.chunked_text, list) or not all(isinstance(c, str) for c in newsletter.chunked_text):
            logging.error("Chunked text is not in expected format.")
            return None
        # Prepare documents with metadata and unique ids
        documents = []
        ids = []
        for idx, chunk in enumerate(newsletter.chunked_text):
            doc_id = idx
            ids.append(doc_id)
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "id": f"{newsletter.message_id}-{idx}",
                        "message_id": newsletter.message_id,
                        "category": newsletter.category,
                        "received_at": newsletter.received_at.isoformat() if newsletter.received_at else None,
                        "chunk_index": idx,
                    },
                )
            )

        # Initialize embedding model
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Embed and store using explicit ids so vectors can be referenced later
        vector_db = FAISS.from_documents(documents, embedding_model, ids=ids)

        # Dynamically assign persist_dir based on category and month for sharding
        category = (newsletter.category or "uncategorized").lower().replace(" ", "_")
        month = (
            newsletter.received_at.strftime("%Y-%m")
            if isinstance(newsletter.received_at, datetime)
            else "unknown"
        )
        category_dir = os.path.join(persist_dir, category, month)
        Path(category_dir).mkdir(parents=True, exist_ok=True)
        vector_db.save_local(category_dir)
        if not os.path.exists(os.path.join(category_dir, "index.faiss")):
            logging.error(f"FAISS index file not found in {category_dir}")
            return None
        logging.info(f"Embedded newsletter {message_id} stored in category directory: {category_dir}")

        logging.info(
            f"Successfully embedded and stored newsletter {message_id} into {persist_dir}"
        )
        logger.debug("FAISS files stored under %s", category_dir)
        return vector_db

    except Exception as e:
        logging.exception(f"Error embedding newsletter {message_id}: {e}")
        return None
    
