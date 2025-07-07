import os
import logging
from backend.services.email_service import get_authenticated_gmail_service

logging.basicConfig(level=logging.DEBUG)

print("Loading Gmail service...")
service = get_authenticated_gmail_service()

if service is None:
    print("Failed to create Gmail service")
    exit(1)

creds = service._http.credentials if hasattr(service._http, 'credentials') else None
print(f"Credentials valid: {getattr(creds, 'valid', 'N/A')}")
print(f"Credential scopes: {getattr(creds, 'scopes', 'N/A')}")

try:
    print("Fetching labels...")
    labels = service.users().labels().list(userId='me').execute()
    print("Labels:", labels)
except Exception as e:
    logging.exception("API call failed")
