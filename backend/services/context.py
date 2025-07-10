from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

from datetime import datetime
import logging
import os

def retrieve_context(
    query: str,
    categories: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
    k: int = 5,
    persist_base_dir: str = "db/faiss_store",
) -> list[Document]:
    """Retrieve relevant chunks filtered by category and optional date range."""
    try:
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        start_dt = datetime.fromisoformat(start_date).date() if start_date else None
        end_dt = datetime.fromisoformat(end_date).date() if end_date else None

        index_path = os.path.join(persist_base_dir, "index.faiss")
        if not os.path.exists(index_path):
            logging.error("Vector store not found at %s", persist_base_dir)
            return []

        vector_db = FAISS.load_local(
            persist_base_dir,
            embedding_model,
            allow_dangerous_deserialization=True,
        )

        raw_docs = vector_db.similarity_search(query, k=50)

        filtered: list[Document] = []
        for d in raw_docs:
            meta = d.metadata or {}
            cat = meta.get("category")
            if categories and cat not in categories:
                continue
            try:
                rec = meta.get("received_at")
                rec_date = datetime.fromisoformat(rec).date() if rec else None
            except Exception:
                rec_date = None
            if start_dt and rec_date and rec_date < start_dt:
                continue
            if end_dt and rec_date and rec_date > end_dt:
                continue
            filtered.append(d)
            if len(filtered) >= k:
                break

        logging.info("Retrieved %d documents for query: %s", len(filtered), query)

        return filtered

    except Exception as e:
        logging.exception(f"Failed to retrieve context for query: {query}")        
        return []
