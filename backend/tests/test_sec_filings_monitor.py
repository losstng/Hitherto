import types
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
