from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from sqlalchemy.orm import Session
from models import Newsletter  # assuming your ORM model is named Newsletter
from pathlib import Path
import logging, os

def retrieve_context(query: str, categories: list[str], k: int = 5, persist_base_dir: str = "db/faiss_store") -> list[Document]:
    try:
        embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_dbs = []

        for category in categories:
            safe_category = category.lower().replace(" ", "_")
            path = os.path.join(persist_base_dir, safe_category)

            if not os.path.exists(path):
                logging.warning(f"Vector store not found at {path}. Skipping '{category}'.")
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

        # Perform retrieval
        retriever = merged_store.as_retriever(search_type="similarity", search_kwargs={"k": k})
        context_docs = retriever.get_relevant_documents(query)

        logging.info(f"Retrieved {len(context_docs)} documents for query: {query}")
        
        return context_docs

    except Exception as e:
        logging.exception(f"Failed to retrieve context for query: {query}")
        return []