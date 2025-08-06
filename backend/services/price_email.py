import base64
import json
import logging
import os
import time
from email.mime.text import MIMEText

from googleapiclient.errors import HttpError

from .email_service import get_authenticated_gmail_service
from ..routers.stocks import get_stock_quotes

logger = logging.getLogger(__name__)
CACHE_FILE = "stock_prices_cache.json"


def load_cached_prices() -> dict:
    """Load cached prices from local file if exists."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        logger.warning("Could not load cached prices.")
        return {}


def save_prices_to_cache(prices: dict) -> None:
    """Save latest prices to local cache."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(prices, f)
    except Exception as e:
        logger.warning(f"Failed to write cache: {e}")


def _format_prices(previous_prices: dict, current_prices: dict) -> str:
    """Return an HTML table with color-coded price changes."""
    def get_color_style(percent_change: float) -> str:
        if percent_change > 1:
            return "color: darkgreen;"
        elif percent_change > 0:
            return "color: green;"
        elif percent_change < -1:
            return "color: darkred;"
        elif percent_change < 0:
            return "color: red;"
        return ""

    rows = []
    for symbol, current_price in current_prices.items():
        prev_price = previous_prices.get(symbol)
        if prev_price is not None:
            diff = current_price - prev_price
            percent = (diff / prev_price) * 100 if prev_price else 0
            style = get_color_style(percent)
            diff_str = f"{diff:+.3f}"
            percent_str = f"{percent:+.2f}%"
        else:
            diff_str = percent_str = "N/A"
            style = ""

        row = (
            f"<tr>"
            f"<td><b><i>{symbol}</i></b></td>"
            f"<td>{current_price:.3f}</td>"
            f"<td style='{style}'>{diff_str}</td>"
            f"<td style='{style}'>{percent_str}</td>"
            f"</tr>"
        )
        rows.append(row)

    table = (
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse;'>"
        "<tr><th>Ticker</th><th>Price</th><th>Change</th><th>% Change</th></tr>"
        + "".join(rows) +
        "</table>"
    )
    return table


def send_price_email(tickers: str | None = None, recipient: str | None = None) -> bool:
    """Fetch stock prices and send HTML-formatted email."""
    service = get_authenticated_gmail_service()
    if service is None:
        logger.error("No Gmail service available")
        return False

    try:
        previous = load_cached_prices()
        resp = get_stock_quotes(tickers)

        current = {q["symbol"]: float(q["price"]) for q in resp.data}
        if current == previous:
            logger.info("Prices unchanged; skipping email")
            return False
        save_prices_to_cache(current)
        body = _format_prices(previous, current)

        recipient = recipient or os.getenv("EMAIL_RECIPIENT", "long131005@gmail.com")
        message = MIMEText(body, "html", "utf-8")
        message["To"] = recipient
        message["Subject"] = "Stock Price Update"

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        logger.info("Sent stock price email")
        return True

    except HttpError:
        logger.exception("Failed to send stock price email")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False


def run_price_email_loop(interval: int | None = None) -> None:
    """Continuously send stock price emails every interval."""
    tickers = os.getenv("PRICE_EMAIL_TICKERS")
    recipient = os.getenv("PRICE_EMAIL_RECIPIENT", os.getenv("EMAIL_RECIPIENT", "long131005@gmail.com"))
    interval = interval or int(os.getenv("PRICE_EMAIL_INTERVAL", "300"))

    while True:
        send_price_email(tickers, recipient)
        time.sleep(interval)


if __name__ == "__main__":
    run_price_email_loop()
