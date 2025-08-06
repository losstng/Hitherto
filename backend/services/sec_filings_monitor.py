import base64
import logging
import os
import time
from datetime import datetime
from email.mime.text import MIMEText
from typing import Dict, Optional

import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .email_service import get_authenticated_gmail_service
from ..database import SessionLocal
from ..models import SecFiling

logger = logging.getLogger(__name__)

# Mapping of CIK to ticker and company title
COMPANIES: Dict[str, Dict[str, str]] = {
    "1835632": {"ticker": "MRVL", "title": "Marvell Technology, Inc."},
    "1045810": {"ticker": "NVDA", "title": "NVIDIA CORP"},
    "1321655": {"ticker": "PLTR", "title": "Palantir Technologies Inc."},
    "1318605": {"ticker": "TSLA", "title": "Tesla, Inc."},
    "936468": {"ticker": "LMT", "title": "LOCKHEED MARTIN CORP"},
    "903651": {"ticker": "INOD", "title": "INNODATA INC"},
    "875320": {"ticker": "VRTX", "title": "VERTEX PHARMACEUTICALS INC / MA"},
    "1326801": {"ticker": "META", "title": "Meta Platforms, Inc."},
}

SEC_HEADERS = {
    "User-Agent": os.getenv("SEC_USER_AGENT", "HithertoApp/0.1 (hello@example.com)")
}


def fetch_latest_form4(cik: str) -> Optional[Dict[str, str]]:
    """Return metadata for the latest Form 4 filing for the given CIK."""
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    try:
        resp = requests.get(url, headers=SEC_HEADERS, timeout=10)
        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        dates = recent.get("filingDate", [])
        for form, acc, date_str in zip(forms, accessions, dates):
            if form == "4":
                return {
                    "accession_number": acc,
                    "filing_date": datetime.strptime(date_str, "%Y-%m-%d"),
                }
    except Exception:
        logger.exception("Failed fetching filings for CIK %s", cik)
    return None


def send_form4_email(cik: str, filing: Dict[str, str], recipient: Optional[str] = None) -> bool:
    """Send an email notification about a new Form 4 filing."""
    service = get_authenticated_gmail_service()
    if service is None:
        logger.error("No Gmail service available for SEC notification")
        return False
    info = COMPANIES.get(cik, {})
    ticker = info.get("ticker", cik)
    name = info.get("title", "")
    body = (
        f"New Form 4 filed for {ticker} {name}\n"
        f"Accession: {filing['accession_number']}\n"
        f"Filed: {filing['filing_date'].date()}"
    )
    recipient = recipient or os.getenv("EMAIL_RECIPIENT", "long131005@gmail.com")
    message = MIMEText(body, "plain", "utf-8")
    message["To"] = recipient
    message["Subject"] = (
        f"Form 4 Alert: {ticker} ({filing['filing_date'].date()})"
    )
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        logger.info("Sent Form 4 email for %s", ticker)
        return True
    except Exception:
        logger.exception("Failed to send Form 4 email for %s", ticker)
        return False


def process_cik(cik: str, db: Session, recipient: Optional[str] = None) -> None:
    """Fetch, store and notify for the latest Form 4 of a single CIK."""
    filing = fetch_latest_form4(cik)
    if not filing:
        return
    try:
        exists = (
            db.query(SecFiling)
            .filter_by(accession_number=filing["accession_number"])
            .first()
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Database error while checking accession number for %s: %s", cik, exc)
        return
    if exists:
        return
    record = SecFiling(
        cik=cik,
        accession_number=filing["accession_number"],
        form_type="4",
        filed_at=filing["filing_date"],
        data={
            "accession_number": filing["accession_number"],
            "filing_date": filing["filing_date"].isoformat(),
        },
    )
    try:
        db.add(record)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Database error while storing filing for %s: %s", cik, exc)
        return
    send_form4_email(cik, filing, recipient)


def run_sec_filings_monitor_loop(interval: int | None = None) -> None:
    """Continuously poll the SEC API and notify on new Form 4 filings."""
    interval = interval or int(os.getenv("SEC_MONITOR_INTERVAL", "300"))
    recipient = os.getenv("SEC_EMAIL_RECIPIENT", os.getenv("EMAIL_RECIPIENT", "long131005@gmail.com"))
    while True:
        with SessionLocal() as db:
            for cik in COMPANIES.keys():
                try:
                    process_cik(cik, db, recipient)
                except Exception:
                    logger.exception("Error processing CIK %s", cik)
        time.sleep(interval)
