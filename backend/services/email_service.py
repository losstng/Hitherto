import base64
import json
import logging
import os
import pickle
import quopri
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from ..database import get_db
from ..env import GMAIL_CREDENTIALS_FILE, GMAIL_SCOPE, GMAIL_TOKEN_FILE
from ..models import Newsletter

SCOPES = [GMAIL_SCOPE]


def get_authenticated_gmail_service():
    """Return an authenticated Gmail service or ``None`` on failure."""
    logging.debug("Entering get_authenticated_gmail_service")
    logging.basicConfig(level=logging.INFO)
    creds = None

    # Step 1: Try loading token
    if os.path.exists(GMAIL_TOKEN_FILE):
        try:
            with open(GMAIL_TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
        except Exception as e:
            logging.error(f"Failed to load token: {e}")
            creds = None

    # Step 2: Refresh or delete invalid token
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            logging.error(f"Token refresh failed: {e}, deleting token.")
            os.remove(GMAIL_TOKEN_FILE)
            return get_authenticated_gmail_service()

    # Step 3: If creds don't exist or still invalid, run OAuth
    if not creds or not creds.valid:
        try:
            if not os.path.exists(GMAIL_CREDENTIALS_FILE):
                logging.error("Missing credentials.json for OAuth flow.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

            with open(GMAIL_TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)

        except Exception as e:
            logging.error(f"OAuth flow failed: {e}")
            return None

    logging.info(f"Credentials valid: {getattr(creds, 'valid', False)}")
    logging.info(f"Credential scopes: {getattr(creds, 'scopes', [])}")

    # Step 4: Return Gmail service
    try:
        service = build("gmail", "v1", credentials=creds)
        # Force an API call to verify the service
        try:
            service.users().labels().list(userId="me").execute()
            logging.info("Successfully accessed Gmail API.")
        except Exception:
            logging.exception("Test Gmail API call failed")
        logging.debug("Gmail service successfully built")
        return service
    except Exception as e:
        logging.exception(f"Failed to build Gmail service: {e}")
        return None


def scan_bloomberg_emails(service, db: Session):
    logging.info("Starting scan_bloomberg_emails")
    logging.debug("Service: %s, DB Session: %s", service, db)
    try:
        logging.debug("Listing Bloomberg messages from Gmail")
        results = (
            service.users()
            .messages()
            .list(userId="me", q="from:noreply@news.bloomberg.com")
            .execute()
        )
        messages = results.get("messages", [])
        logging.debug(f"Found {len(messages)} messages")
        if not messages:
            logging.info("No Bloomberg emails found.")
            return []

        stored = []

        for msg_meta in messages:
            msg_id = msg_meta["id"]
            logging.debug(f"Processing message {msg_id}")

            # Skip if already exists
            if db.query(Newsletter).filter_by(message_id=msg_id).first():
                logging.debug(f"Skipping {msg_id}, already in DB")
                continue

            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
            payload = msg.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
            raw_date = headers.get("Date")
            received_at = parsedate_to_datetime(raw_date) if raw_date else None
            subject = headers.get("Subject", "Untitled")
            sender = headers.get("From")

            # Quick category parsing from the raw body (no extraction)
            category = None
            body = ""
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and "data" in part.get(
                        "body", {}
                    ):
                        try:
                            data = part["body"]["data"]
                            body = base64.urlsafe_b64decode(data).decode(
                                "utf-8", errors="replace"
                            )
                        except Exception as e:
                            logging.warning(f"Failed to decode message {msg_id}: {e}")
                        break

            if body:
                for line in body.splitlines():
                    if line.strip().endswith("=20"):
                        raw_category = line.strip().replace("=20", "").strip()
                        category = raw_category.lower().replace(" ", "_")
                        break

            newsletter = Newsletter(
                title=subject,
                sender=sender,
                received_at=received_at,
                category=category,
                extracted_text=None,
                chunked_text=None,
                message_id=msg_id,
                token_count=None,
            )
            db.add(newsletter)
            stored.append(newsletter)
            logging.debug(f"Stored metadata for {msg_id}")

        db.commit()
        logging.info(f"scan_bloomberg_emails stored {len(stored)} new newsletters")
        logging.debug("Stored entries: %s", [n.message_id for n in stored])
        return stored

    except Exception as e:
        db.rollback()
        logging.exception("Failed to scan and store Bloomberg email metadata.")
        return []


def fetch_raw_email(service, message_id: str):
    """Return the full Gmail API response for the given message."""
    logging.debug("Fetching raw email %s", message_id)
    try:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        logging.info(f"Fetched raw message for {message_id}")
        logging.info(
            "Gmail API response for %s: %s",
            message_id,
            json.dumps(msg, indent=2)[:1000],
        )
        return msg
    except Exception:
        logging.exception(f"Failed to fetch raw message for {message_id}")
        return None


def find_text_plain_part(payload):
    logging.debug("Searching for text/plain part")
    if (
        payload.get("mimeType") == "text/plain"
        and "body" in payload
        and "data" in payload["body"]
    ):
        logging.debug("Found direct text/plain part")
        return payload
    for part in payload.get("parts", []):
        found = find_text_plain_part(part)
        if found:
            logging.debug("Found nested text/plain part")
            return found
    logging.debug("No text/plain part found")
    return None


def find_largest_text_plain_part(payload):
    """Return the largest text/plain MIME part available."""
    logging.debug("Locating largest text/plain MIME part")
    best_part = None
    best_size = -1

    def _walk(part):
        nonlocal best_part, best_size
        if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
            size = int(part.get("body", {}).get("size", 0))
            if size > best_size:
                best_part = part
                best_size = size
                logging.debug("New best text/plain part size=%d", best_size)
        for child in part.get("parts", []):
            _walk(child)

    _walk(payload)
    if best_part:
        logging.debug("Largest text/plain part size=%d", best_size)
    return best_part


def log_mime_structure(payload, depth=0):
    indent = "  " * depth
    logging.debug(f"{indent}- {payload.get('mimeType', 'unknown')}")
    for part in payload.get("parts", []):
        log_mime_structure(part, depth + 1)


def extract_bloomberg_email_text(service, db: Session, message_id: str):
    logging.debug("Extracting newsletter text for %s", message_id)
    try:
        newsletter = db.query(Newsletter).filter_by(message_id=message_id).first()
        if not newsletter:
            logging.warning(f"No newsletter entry found for message_id: {message_id}")
            return None
        if newsletter.extracted_text:
            logging.info(f"extracted_text already exists for message_id: {message_id}")
            return newsletter

        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

        log_mime_structure(payload)

        body = ""
        # Prefer the largest text/plain part in case of multiple alternatives
        text_part = find_largest_text_plain_part(payload)
        if text_part:
            try:
                data = text_part["body"]["data"]
                raw_bytes = base64.urlsafe_b64decode(data)
                body = quopri.decodestring(raw_bytes).decode("utf-8", errors="replace")
            except Exception as e:
                logging.warning(f"Failed to decode body of {message_id}: {e}")
                return None
        else:
            logging.warning(f"No text/plain part found in message {message_id}")
            return None

        if not body:
            logging.warning(f"No text/plain body found for message_id: {message_id}")
            return None

        # Remove any header metadata that might be embedded in the part
        if body.startswith("Content-Type:"):
            split_idx = body.find("\n\n")
            if split_idx != -1:
                body = body[split_idx + 2 :]

        # Extract meaningful content between header and footer
        lines = body.splitlines()
        content_lines = []
        for i in range(len(lines)):
            line = lines[i]
            # Stop just before the common footer
            if line.strip().lower() == "more from bloomberg":
                break
            content_lines.append(line)

        extracted_text = "\n".join(content_lines).strip()
        if not extracted_text:
            logging.warning(f"No content extracted for {message_id}")
            return None

        newsletter.extracted_text = extracted_text
        db.commit()
        db.refresh(newsletter)

        # Derive category from stored extracted_text if missing
        if newsletter.category is None and newsletter.extracted_text:
            logging.debug(
                f"Deriving category from stored text for {newsletter.message_id}"
            )
            for line in newsletter.extracted_text.splitlines():
                line = line.strip()
                if line:
                    newsletter.category = line.lower().replace(" ", "_")
                    db.commit()
                    db.refresh(newsletter)
                    logging.debug(
                        f"Backfilled category '{newsletter.category}' for {newsletter.message_id}"
                    )
                    break

        logging.info(f"Extracted and updated content for message_id: {message_id}")
        logging.debug("Stored text length for %s: %d", message_id, len(extracted_text))
        return newsletter

    except Exception as e:
        db.rollback()
        logging.exception(f"Error extracting text for message_id: {message_id}")
        return None


def backfill_categories_from_text(db: Session):
    """Fill missing categories using the first line of extracted text."""
    logging.info("Starting category backfill from extracted_text")
    logging.debug("DB Session: %s", db)

    newsletters = (
        db.query(Newsletter)
        .filter(
            Newsletter.category == None,
            Newsletter.extracted_text != None,
        )
        .all()
    )

    logging.debug(f"{len(newsletters)} newsletters need category backfill from text")

    for newsletter in newsletters:
        try:
            for line in newsletter.extracted_text.splitlines():
                line = line.strip()
                if line:
                    category = line.lower().replace(" ", "_")
                    newsletter.category = category
                    logging.debug(
                        f"Backfilled category '{category}' for message {newsletter.message_id}"
                    )
                    break
        except Exception as e:
            logging.warning(
                f"Failed to backfill for message {newsletter.message_id}: {e}"
            )
            continue

    db.commit()
    logging.debug("Committed category updates for %d newsletters", len(newsletters))
    logging.info("Finished category backfill from extracted_text")
