from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from sqlalchemy.orm import Session
from ..models import Newsletter  # assuming your ORM model is named Newsletter
from pathlib import Path
import logging, os

def embed_chunked_newsletter(db: Session, message_id: str, persist_dir="db/faiss_store"):
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
        # Prepare documents
        documents = [Document(page_content=chunk) for chunk in newsletter.chunked_text]

        # Initialize embedding model
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Embed and store
        vector_db = FAISS.from_documents(documents, embedding_model)

        # Dynamically assign persist_dir based on category
        category = (newsletter.category or "uncategorized").lower().replace(" ", "_")
        category_dir = os.path.join(persist_dir, category)
        Path(category_dir).mkdir(parents=True, exist_ok=True)
        vector_db.save_local(category_dir)
        if not os.path.exists(os.path.join(category_dir, "index.faiss")):
            logging.error(f"FAISS index file not found in {category_dir}")
            return None
        logging.info(f"Embedded newsletter {message_id} stored in category directory: {category_dir}")

        logging.info(f"Successfully embedded and stored newsletter {message_id} into {persist_dir}")
        return vector_db

    except Exception as e:
        logging.exception(f"Error embedding newsletter {message_id}: {e}")
        return None
    
