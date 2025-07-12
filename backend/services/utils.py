import logging
import os
import re

from langchain.embeddings import HuggingFaceEmbeddings


def safe_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename on Windows."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def load_embedding_model(device: str) -> HuggingFaceEmbeddings | None:
    """Return a sentence transformer embedding model or ``None`` on failure."""
    cache_dir = os.environ.get("HF_MODEL_DIR")
    model_kwargs = {"device": device}
    if cache_dir:
        model_kwargs["cache_folder"] = cache_dir

    try:
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs=model_kwargs,
            encode_kwargs={"device": device},
        )
    except NotImplementedError as exc:
        logging.exception(
            "Failed to load embedding model. Ensure model weights are available.",
            exc_info=exc,
        )
        return None

