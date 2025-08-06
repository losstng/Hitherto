import types
from datetime import datetime
import base64
from email import message_from_bytes

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from backend.models import Base, SecFiling
from backend.services import sec_filings_monitor as monitor


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_process_cik_inserts_and_emails(monkeypatch, db_session):
    sample = {"accession_number": "000123", "filing_date": datetime(2024, 5, 1)}
    monkeypatch.setattr(monitor, "fetch_latest_form4", lambda cik: sample)
    sent = {"count": 0}
    def fake_send(cik, filing, recipient=None):
        sent["count"] += 1
        return True
    monkeypatch.setattr(monitor, "send_form4_email", fake_send)

    monitor.process_cik("1835632", db_session)
    assert db_session.query(SecFiling).count() == 1
    assert sent["count"] == 1

    # Second call should not send another email or create record
    monitor.process_cik("1835632", db_session)
    assert db_session.query(SecFiling).count() == 1
    assert sent["count"] == 1


def test_process_cik_rolls_back_on_error(monkeypatch, db_session):
    sample = {"accession_number": "000123", "filing_date": datetime(2024, 5, 1)}
    monkeypatch.setattr(monitor, "fetch_latest_form4", lambda cik: sample)

    original_query = db_session.query

    class FailingQuery:
        def filter_by(self, **kwargs):
            raise SQLAlchemyError("boom")

    def failing(*args, **kwargs):
        return FailingQuery()

    monkeypatch.setattr(db_session, "query", failing)
    monitor.process_cik("1835632", db_session)

    # Restore normal query and ensure session is usable after rollback
    monkeypatch.setattr(db_session, "query", original_query)
    assert db_session.query(SecFiling).count() == 0


def test_send_form4_email_subject_contains_date(monkeypatch):
    sent = {}

    class DummyMessages:
        def send(self, userId, body):
            sent["raw"] = body["raw"]
            class Exec:
                def execute(self_inner):
                    return {}
            return Exec()

    class DummyUsers:
        def messages(self):
            return DummyMessages()

    class DummyService:
        def users(self_inner):
            return DummyUsers()

    monkeypatch.setattr(monitor, "get_authenticated_gmail_service", lambda: DummyService())

    filing = {"accession_number": "000123", "filing_date": datetime(2024, 5, 1)}
    monitor.send_form4_email("1835632", filing, "to@example.com")

    raw = sent["raw"]
    msg = message_from_bytes(base64.urlsafe_b64decode(raw.encode()))
    assert "2024-05-01" in msg["Subject"]
