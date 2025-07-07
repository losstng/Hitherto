from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.utils import parsedate_to_datetime
import os, pickle, json
from dotenv import load_dotenv
import base64
import quopri
import logging
from sqlalchemy.orm import Session
from ..models import Newsletter
from bs4 import BeautifulSoup
from ..database import get_db
load_dotenv()

SCOPES = [os.getenv("GMAIL_SCOPE")]


def get_authenticated_gmail_service():
    logging.basicConfig(level=logging.INFO)
    creds = None

    # Step 1: Try loading token
    if os.path.exists("token.json"):
        try:
            with open("token.json", "rb") as token:
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
            os.remove("token.json")
            return get_authenticated_gmail_service()

    # Step 3: If creds don't exist or still invalid, run OAuth
    if not creds or not creds.valid:
        try:
            if not os.path.exists("credentials.json"):
                logging.error("Missing credentials.json for OAuth flow.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

            with open("token.json", "wb") as token:
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
        return service
    except Exception as e:
        logging.exception(f"Failed to build Gmail service: {e}")
        return None

def scan_bloomberg_emails(service, db: Session):
    logging.info("Starting scan_bloomberg_emails")
    try:
        logging.debug("Listing Bloomberg messages from Gmail")
        results = service.users().messages().list(userId='me', q="from:noreply@news.bloomberg.com").execute()
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

            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = msg.get('payload', {})
            headers = {h['name']: h['value'] for h in payload.get('headers', [])}
            raw_date = headers.get("Date")
            received_at = parsedate_to_datetime(raw_date) if raw_date else None
            subject = headers.get("Subject", "Untitled")
            sender = headers.get("From")

            # Quick category parsing from the raw body (no extraction)
            category = None
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                        try:
                            data = part['body']['data']
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
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
                token_count=None
            )
            db.add(newsletter)
            stored.append(newsletter)
            logging.debug(f"Stored metadata for {msg_id}")

        db.commit()
        logging.info(f"scan_bloomberg_emails stored {len(stored)} new newsletters")
        return stored

    except Exception as e:
        db.rollback()
        logging.exception("Failed to scan and store Bloomberg email metadata.")
        return []


def extract_bloomberg_email_text(service, db: Session, message_id: str):
    try:
        newsletter = db.query(Newsletter).filter_by(message_id=message_id).first()
        if not newsletter:
            logging.warning(f"No newsletter entry found for message_id: {message_id}")
            return None
        if newsletter.extracted_text:
            logging.info(f"extracted_text already exists for message_id: {message_id}")
            return newsletter

        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                    try:
                        data = part["body"]["data"]
                        raw_bytes = base64.urlsafe_b64decode(data)
                        body = quopri.decodestring(raw_bytes).decode("utf-8", errors="replace")
                        break
                    except Exception as e:
                        logging.warning(f"Failed to decode body of {message_id}: {e}")
                        return None

        if not body:
            logging.warning(f"No text/plain body found for message_id: {message_id}")
            return None

        # Category extraction from body
        category_updated = False
        for line in body.splitlines():
            line = line.strip()
            if line.endswith("=20"):
                raw_category = line.replace("=20", "").strip()
                newsletter.category = raw_category.lower().replace(" ", "_")
                logging.debug(
                    f"Backfilled category '{newsletter.category}' for {newsletter.message_id}"
                )
                category_updated = True
                break

        if category_updated:
            db.commit()
            db.refresh(newsletter)

        # Parsing logic for extracting useful content
        lines = body.splitlines()
        content_lines = []
        in_content = False
        for i in range(len(lines)):
            line = lines[i]

            if not in_content:
                if 'Content-Type: text/plain; charset="UTF-8"' in line:
                    in_content = True
                continue

            if i + 1 < len(lines) and lines[i].strip().lower() == "more from bloomberg" and lines[i + 1].strip().lower().startswith("enjoying"):
                break

            content_lines.append(line)

        extracted_text = "\n".join(content_lines).strip()

        if not extracted_text:
            logging.warning(f"No content extracted for {message_id}")
            return None

        newsletter.extracted_text = extracted_text
        db.commit()
        db.refresh(newsletter)

        logging.info(f"Extracted and updated content for message_id: {message_id}")
        return newsletter

    except Exception as e:
        db.rollback()
        logging.exception(f"Error extracting text for message_id: {message_id}")
        return None