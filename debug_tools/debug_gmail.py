"""Utility helpers for manual Gmail API debugging."""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def fetch_labels(service: Any) -> Any:
    """Return the labels for the authenticated Gmail user."""
    logger.debug("Fetching labels via Gmail API")
    return service.users().labels().list(userId="me").execute()


def run(get_service: Callable[[], Any] | None = None) -> Any:
    """Execute the debugging flow of authenticating and listing labels."""
    logger.info("Loading Gmail service ...")
    if get_service is None:
        from backend.services.email_service import get_authenticated_gmail_service

        get_service = get_authenticated_gmail_service

    service = get_service()
    if service is None:
        logger.error("Failed to create Gmail service")
        return None

    creds = service._http.credentials if hasattr(service._http, "credentials") else None
    logger.info("Credentials valid: %s", getattr(creds, "valid", "N/A"))
    logger.debug("Credential scopes: %s", getattr(creds, "scopes", "N/A"))

    try:
        labels = fetch_labels(service)
        logger.info("Retrieved %d labels", len(labels.get("labels", [])))
        return labels
    except Exception:  # pragma: no cover - network failures
        logger.exception("API call failed")
        return None


if __name__ == "__main__":  # pragma: no cover - manual execution
    logging.basicConfig(level=logging.DEBUG)
    fetched = run()
    if fetched is not None:
        print("Labels:", fetched)
