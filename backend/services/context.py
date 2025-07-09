from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

from datetime import datetime, date, timedelta
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
        vector_dbs = []

        start_dt = datetime.fromisoformat(start_date).date() if start_date else None
        end_dt = datetime.fromisoformat(end_date).date() if end_date else None

        def months_between(start: date, end: date):
            m = date(start.year, start.month, 1)
            while m <= end:
                yield m.strftime("%Y-%m")
                m = (m.replace(day=28) + timedelta(days=4)).replace(day=1)

        months: list[str] | None = None
        if start_dt and end_dt:
            if end_dt < start_dt:
                start_dt, end_dt = end_dt, start_dt
            months = list(months_between(start_dt, end_dt))
        elif start_dt:
            months = [start_dt.strftime("%Y-%m")]
        elif end_dt:
            months = [end_dt.strftime("%Y-%m")]

        for category in categories:
            safe_category = category.lower().replace(" ", "_")
            base_path = os.path.join(persist_base_dir, safe_category)

            if months:
                paths = [os.path.join(base_path, m) for m in months]
            else:
                if not os.path.exists(base_path):
                    logging.warning(f"Vector store not found at {base_path}. Skipping '{category}'.")
                    continue
                paths = [os.path.join(base_path, d) for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

            for path in paths:
                if not os.path.exists(path):
                    logging.warning(f"Vector store not found at {path}. Skipping.")
                    continue
                try:
                    db = FAISS.load_local(path, embedding_model)
                    vector_dbs.append(db)
                except Exception as e:
                    logging.error(f"Failed to load FAISS from {path}: {e}")

        if not vector_dbs:
            logging.error("No vector stores loaded. Cannot perform context retrieval.")
            return []


        # Merge all into one store
        merged_store = vector_dbs[0]
        for db in vector_dbs[1:]:
            merged_store.merge_from(db)

        # Perform retrieval with Maximal Marginal Relevance for diverse results
        retriever = merged_store.as_retriever(search_type="mmr", search_kwargs={"k": k})
        context_docs = retriever.get_relevant_documents(query)

        logging.info(f"Retrieved {len(context_docs)} documents for query: {query}")
        
        return context_docs

    except Exception as e:
        logging.exception(f"Failed to retrieve context for query: {query}")        return []