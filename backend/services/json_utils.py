import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_json(path: str | Path, default: Any) -> Any:
    """Load JSON data from file, returning default on failure."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        logger.warning(f"Could not load {path}.")
        return default


def save_json(path: str | Path, data: Any) -> None:
    """Write JSON data to file, ignoring errors."""
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Failed to write {path}: {e}")
