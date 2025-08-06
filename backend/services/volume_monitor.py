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

try:  # pragma: no cover - fallback if email deps missing
    from .email_service import get_authenticated_gmail_service
except Exception:  # pragma: no cover
    def get_authenticated_gmail_service():
        return None

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "raw_data" / "5_min"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TICKERS = ["INOD", "MRVL", "TSLA", "PLTR", "NVDA", "GC=F"]
ALERT_FILE = DATA_DIR / "volume_alerts.json"


def update_5min_csv(ticker: str) -> pd.DataFrame:
    """Fetch latest 5-minute data for ticker and append to CSV."""
    filepath = DATA_DIR / f"{ticker}.csv"
    if filepath.exists():
        old_df = pd.read_csv(filepath, parse_dates=True, index_col="Datetime")
    else:
        old_df = pd.DataFrame()
    last = old_df.index.max() if not old_df.empty else None
    start = last + timedelta(minutes=5) if last is not None else datetime.utcnow() - timedelta(days=5)
    df = yf.Ticker(ticker).history(start=start, interval="5m")
    if df.empty:
        return old_df
    df.index.name = "Datetime"
    combined = pd.concat([old_df, df])
    combined = combined[~combined.index.duplicated(keep="last")]
    combined.to_csv(filepath)
    return combined


def detect_volume_spike(df: pd.DataFrame, multiplier: float = 1.75):
    """Return True if the latest 5m bar volume > multiplier * average of previous bars."""
    if df.empty or len(df) < 2:
        return False, None, None
    last = df["Volume"].iloc[-1]
    prev_avg = df["Volume"].iloc[:-1].mean()
    if prev_avg == 0 or pd.isna(prev_avg):
        return False, last, prev_avg
    return last > multiplier * prev_avg, last, prev_avg

def load_alerted_volumes() -> dict:
    """Load last alerted timestamps from file."""
    if not ALERT_FILE.exists():
        return {}
    try:
        with open(ALERT_FILE, "r") as f:
            return json.load(f)
    except Exception:
        logger.warning("Could not load alert file.")
        return {}


def _to_native(value):
    """Recursively convert numpy/pandas types to native Python types."""
    if isinstance(value, dict):
        return {k: _to_native(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_native(v) for v in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def save_alerted_volumes(alerts: dict) -> None:
    """Persist alert information to disk."""
    try:
        serializable = _to_native(alerts)
        with open(ALERT_FILE, "w") as f:
            json.dump(serializable, f)
    except Exception as e:
        logger.warning(f"Failed to write alert file: {e}")


def send_volume_email(
    ticker: str,
    volume: float,
    avg_volume: float,
    timeframe: str,
    pct_change: float,
    recipient: str | None = None,
) -> bool:
    """Send an email notification about a volume spike.

    Args:
        ticker: Stock symbol.
        volume: Volume of the spike.
        avg_volume: Average volume for comparison.
        timeframe: Time of day when the spike occurred (HH:MM).
        pct_change: Price percentage change during the period.
        recipient: Optional email recipient.
    """
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
    message["Subject"] = (
        f"Volume spike: {ticker} | {timeframe} | {pct_change:+.2f}%"
    )
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

    alerts = load_alerted_volumes()

    while True:
        for t in tickers:
            try:
                df = update_5min_csv(t)
                spike, vol, avg = detect_volume_spike(df)
                last_ts = df.index[-1] if not df.empty else None
                last_ts_iso = last_ts.isoformat() if last_ts is not None else None
                info = alerts.get(t, {})
                info["last_volume"] = int(vol) if vol is not None else None

                if spike and info.get("alerted") != last_ts_iso:
                    pct_change = 0.0
                    if {"Open", "Close"}.issubset(df.columns):
                        last_bar = df.iloc[-1]
                        open_price = last_bar["Open"]
                        close_price = last_bar["Close"]
                        if open_price:
                            pct_change = (close_price - open_price) / open_price * 100

                    timeframe = last_ts.strftime("%H:%M") if last_ts is not None else ""
                    send_volume_email(
                        t,
                        float(vol),
                        float(avg),
                        timeframe,
                        pct_change,
                        recipient,
                    )
                    info["alerted"] = last_ts_iso
                alerts[t] = info
                save_alerted_volumes(alerts)
            except Exception:
                logger.exception("Error processing ticker %s", t)
        time.sleep(interval)
