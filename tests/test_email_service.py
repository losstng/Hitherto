import os, sys
os.environ["DATABASE_URL"]="sqlite:///:memory:"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import base64
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Newsletter
from backend.services.email_service import scan_bloomberg_emails

class FakeRequest:
    def __init__(self, result):
        self._result = result
    def execute(self):
        return self._result

class FakeMessages:
    def __init__(self, messages):
        self._messages = messages
    def list(self, userId='me', q=None):
        return FakeRequest({'messages': [{'id': mid} for mid in self._messages]})
    def get(self, userId='me', id=None, format='full'):
        return FakeRequest(self._messages[id])

class FakeUsers:
    def __init__(self, messages):
        self._messages = messages
    def messages(self):
        return FakeMessages(self._messages)

class FakeService:
    def __init__(self, messages):
        self._users = FakeUsers(messages)
    def users(self):
        return self._users

def make_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def test_scan_bloomberg_emails_inserts_metadata():
    encoded = base64.urlsafe_b64encode(b'Politics=20\nBody').decode()
    fake_messages = {
        '1': {
            'payload': {
                'headers': [
                    {'name': 'Date', 'value': 'Mon, 01 Jan 2024 00:00:00 +0000'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'noreply@news.bloomberg.com'}
                ],
                'parts': [
                    {
                        'mimeType': 'text/plain',
                        'body': {'data': encoded}
                    }
                ]
            }
        }
    }
    service = FakeService(fake_messages)
    db = make_db()
    inserted = scan_bloomberg_emails(service, db)

    newsletters = db.query(Newsletter).all()
    assert len(newsletters) == 1
    n = newsletters[0]
    assert n.message_id == '1'
    assert n.title == 'Test Subject'
    assert n.sender == 'noreply@news.bloomberg.com'
    assert n.category == 'politics'
    assert inserted[0].id == n.id
