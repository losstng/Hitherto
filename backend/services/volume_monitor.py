import base64
import json
import logging
import os
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd
import yfinance as yf

from .email_service import get_authenticated_gmail_service

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "raw_data" / "intraday"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TICKERS = ["INOD", "MRVL", "TSLA", "PLTR", "NVDA", "GC=F"]
CACHE_FILE = "volume_cache.json"


def update_intraday_csv(ticker: str) -> pd.DataFrame:
    """Fetch latest 1-minute data for ticker and append to CSV."""
    filepath = DATA_DIR / f"intraday_{ticker}.csv"
    if filepath.exists():
        old_df = pd.read_csv(filepath, parse_dates=True, index_col="Datetime")
    else:
        old_df = pd.DataFrame()
    last = old_df.index.max() if not old_df.empty else None
    start = last + timedelta(minutes=1) if last is not None else datetime.utcnow() - timedelta(days=5)
    df = yf.Ticker(ticker).history(start=start, interval="1m")
    if df.empty:
        return old_df
    df.index.name = "Datetime"
    combined = pd.concat([old_df, df])
    combined = combined[~combined.index.duplicated(keep="last")]
    combined.to_csv(filepath)
    return combined


def detect_volume_spike(df: pd.DataFrame, window: int = 5, multiplier: float = 1.5):
    """Return True if the latest window shows volume > multiplier * average."""
    if df.empty or len(df) < window + 1:
        return False, None, None
    rolling = df["Volume"].rolling(window=window).sum()
    last = rolling.iloc[-1]
    prev_avg = rolling.iloc[:-1].mean()
    if prev_avg == 0 or pd.isna(prev_avg):
        return False, last, prev_avg
    return last > multiplier * prev_avg, last, prev_avg


def load_cached_volumes() -> dict:
    """Load cached volume totals from local file."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        logger.warning("Could not load volume cache.")
        return {}


def save_volumes_to_cache(volumes: dict) -> None:
    """Persist latest volume totals to cache file."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(volumes, f)
    except Exception as e:
        logger.warning(f"Failed to write volume cache: {e}")


def send_volume_email(
    ticker: str,
    volume: float,
    avg_volume: float,
    window: int,
    recipient: str | None = None,
) -> bool:
    """Send an email notification about a volume spike."""
    service = get_authenticated_gmail_service()
    if service is None:
        logger.error("No Gmail service available")
        return False
    body = (
        f"Volume spike detected for {ticker}: {volume:.0f} vs avg {avg_volume:.0f}"
    )
    recipient = recipient or os.getenv("EMAIL_RECIPIENT", "long131005@gmail.com")
    message = MIMEText(body, "plain", "utf-8")
    message["To"] = recipient
    message["Subject"] = f"Volume spike for {ticker} over {window}m"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        logger.info("Sent volume spike email for %s", ticker)
        return True
    except Exception:
        logger.exception("Failed to send volume email for %s", ticker)
        return False


def run_volume_monitor_loop(interval: int | None = None) -> None:
    """Continuously monitor tickers for volume spikes and update CSVs."""
    tickers_env = os.getenv("VOLUME_TICKERS")
    tickers = [t.strip() for t in tickers_env.split(",")] if tickers_env else DEFAULT_TICKERS
    recipient = os.getenv("VOLUME_EMAIL_RECIPIENT", os.getenv("EMAIL_RECIPIENT", "long131005@gmail.com"))
    interval = interval or int(os.getenv("VOLUME_MONITOR_INTERVAL", "300"))
    window = int(os.getenv("VOLUME_MONITOR_WINDOW", "5"))

    volumes_cache = load_cached_volumes()

    while True:
        for t in tickers:
            try:
                df = update_intraday_csv(t)
                spike, vol, avg = detect_volume_spike(df, window=window)
                volumes_cache[t] = vol
                save_volumes_to_cache(volumes_cache)
                if spike:
                    send_volume_email(t, vol, avg, window, recipient)
            except Exception:
                logger.exception("Error processing ticker %s", t)
        time.sleep(interval)
