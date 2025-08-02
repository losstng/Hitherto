"""Utility script to email stock price updates every five minutes."""

import base64
import logging
import os
import time
from email.mime.text import MIMEText
from typing import Iterable

from backend.routers.stocks import get_stock_quotes
from backend.services.email_service import get_authenticated_gmail_service

INTERVAL_SECONDS = 5 * 60  # five minutes


def _format_quotes(quotes: Iterable[dict]) -> str:
    """Return human-readable lines describing each quote."""
    lines: list[str] = []
    for q in quotes:
        symbol = q.get("symbol")
        price = q.get("price")
        change = q.get("change")
        pct = q.get("change_percent")
        if change is not None and pct is not None:
            lines.append(f"{symbol}: {price} ({change:+.2f}, {pct:+.2f}%)")
        else:
            lines.append(f"{symbol}: {price}")
    return "\n".join(lines)


def _send_email(service, recipient: str, subject: str, body: str) -> None:
    """Send an email via the Gmail API using the provided service."""
    message = MIMEText(body)
    message["to"] = recipient
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def main() -> None:
    """Continuously send stock price updates every ``INTERVAL_SECONDS``."""
    service = get_authenticated_gmail_service()
    recipient = os.environ.get("PRICE_UPDATE_RECIPIENT")
    if not service or not recipient:
        logging.error("Missing Gmail service or PRICE_UPDATE_RECIPIENT env var.")
        return

    while True:
        response = get_stock_quotes(tickers=None)
        quotes = response.data if getattr(response, "success", False) else []
        body = _format_quotes(quotes)
        _send_email(service, recipient, "Stock Price Update", body)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
