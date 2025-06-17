from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.utils import parsedate_to_datetime
import os, pickle, json
from dotenv import load_dotenv
import base64
import logging
from sqlalchemy.orm import Session
from models import Newsletter
from bs4 import BeautifulSoup
from database import get_db
load_dotenv

SCOPES = [os.getenv("GMAIL_SCOPE")]


def get_authenticated_gmail_service():
    logging.basicConfig(level=logging.INFO)
    creds = None

    # Try loading token from file
    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, go through the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                logging.error("Missing credentials.json for OAuth flow.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=8080)

        # Save the credentials for the next run
        with open("token.json", "wb") as token:
            pickle.dump(creds, token)

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except Exception as e:
        logging.exception(f"Failed to build Gmail service: {e}")
        return None

def scan_bloomberg_emails(service, db: Session):
    try:
        results = service.users().messages().list(userId='me', q="from:noreply@news.bloomberg.com").execute()
        messages = results.get("messages", [])
        if not messages:
            logging.info("No Bloomberg emails found.")
            return []

        stored = []

        for msg_meta in messages:
            msg_id = msg_meta["id"]

            # Skip if already exists
            if db.query(Newsletter).filter_by(message_id=msg_id).first():
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

        db.commit()
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
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                        break
                    except Exception as e:
                        logging.warning(f"Failed to decode body of {message_id}: {e}")
                        return None

        if not body:
            logging.warning(f"No text/plain body found for message_id: {message_id}")
            return None

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