import base64
import logging
import os
import time
from email.mime.text import MIMEText
from typing import Iterable

from googleapiclient.errors import HttpError

from .email_service import get_authenticated_gmail_service
from ..routers.stocks import get_stock_quotes

logger = logging.getLogger(__name__)


def _format_prices(quotes: Iterable[dict]) -> str:
    """Return a simple text table from quote dictionaries."""
    return "\n".join(f"{q['symbol']}: {q.get('price')}" for q in quotes)


def send_price_email(tickers: str | None = None, recipient: str | None = None) -> bool:
    """Fetch stock prices and email them via the Gmail API.

    Parameters
    ----------
    tickers:
        Comma-separated ticker symbols. Defaults to ``None`` which uses
        the backend's default tickers.
    recipient:
        Email address to send to. If omitted, the message is addressed to
        ``me`` (the authenticated user).

    Returns
    -------
    bool
        ``True`` if the message was queued successfully.
    """
    service = get_authenticated_gmail_service()
    if service is None:
        logger.error("No Gmail service available")
        return False

    resp = get_stock_quotes(tickers)
    body = _format_prices(resp.data)

    message = MIMEText(body)
    message["to"] = recipient or "me"
    message["subject"] = "Stock price update"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        logger.info("Sent stock price email")
        return True
    except HttpError:
        logger.exception("Failed to send stock price email")
        return False


def run_price_email_loop(interval: int | None = None) -> None:
    """Continuously send price emails on a fixed interval.

    Parameters
    ----------
    interval:
        Sleep duration in seconds between emails. Defaults to the value of
        ``PRICE_EMAIL_INTERVAL`` or 300 if unset.
    """
    tickers = os.getenv("PRICE_EMAIL_TICKERS")
    recipient = os.getenv("PRICE_EMAIL_RECIPIENT")
    interval = interval or int(os.getenv("PRICE_EMAIL_INTERVAL", "300"))
    while True:
        send_price_email(tickers, recipient)
        time.sleep(interval)


if __name__ == "__main__":
    run_price_email_loop()
