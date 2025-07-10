import re


def safe_filename(name: str) -> str:
    """Sanitize a string to be safe for use as a filename on Windows."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

