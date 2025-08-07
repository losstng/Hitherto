import logging
from datetime import datetime
from pathlib import Path

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from sqlalchemy.orm import Session

from ..env import EMBEDDING_DEVICE, FAISS_STORE_DIR
from ..models import Newsletter
from .utils import load_embedding_model


def embed_chunked_newsletter(
    db: Session, message_id: str, persist_dir: str = FAISS_STORE_DIR
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
            logging.warning(
                f"Newsletter with message_id {message_id} has no chunked text to embed."
            )
            return None
        if not isinstance(newsletter.chunked_text, list) or not all(
            isinstance(c, str) for c in newsletter.chunked_text
        ):
            logging.error("Chunked text is not in expected format.")
            return None
        # Prepare documents with metadata and unique ids
        documents = []
        for idx, chunk in enumerate(newsletter.chunked_text):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "newsletter_id": newsletter.id,
                        "message_id": newsletter.message_id,
                        "category": newsletter.category,
                        "received_at": (
                            newsletter.received_at.isoformat()
                            if newsletter.received_at
                            else None
                        ),
                        "chunk_index": idx,
                    },
                    id=f"{newsletter.id}-{idx}",
                )
            )

        # Initialize embedding model
        embedding_model = load_embedding_model(EMBEDDING_DEVICE)
        if embedding_model is None:
            return None

        index_path = Path(persist_dir)
        if (index_path / "index.faiss").exists():
            vector_db = FAISS.load_local(
                persist_dir,
                embedding_model,
                allow_dangerous_deserialization=True,
            )
            vector_db.add_documents(documents)
        else:
            vector_db = FAISS.from_documents(documents, embedding_model)

        index_path.mkdir(parents=True, exist_ok=True)
        vector_db.save_local(persist_dir)
        if not (index_path / "index.faiss").exists():
            logging.error(f"FAISS index file not found in {persist_dir}")
            return None
        logging.info(f"Embedded newsletter {message_id} stored in {persist_dir}")

        newsletter.vectorized = True
        db.commit()
        db.refresh(newsletter)

        logging.info(
            f"Successfully embedded and stored newsletter {message_id} into {persist_dir}"
        )
        logger.debug("FAISS files stored under %s", persist_dir)
        return vector_db

    except Exception as e:
        logging.exception(f"Error embedding newsletter {message_id}: {e}")
        return None
