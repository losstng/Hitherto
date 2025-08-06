import pytest

import json

from backend.services import price_email


def test_send_price_email_skips_when_unchanged(monkeypatch, tmp_path):
    cache_file = tmp_path / "prices.json"
    thread_file = tmp_path / "thread.json"
    monkeypatch.setattr(price_email, "CACHE_FILE", str(cache_file))
    monkeypatch.setattr(price_email, "THREAD_FILE", str(thread_file))
    price_email.save_prices_to_cache({"TSLA": 100.0})

    class DummyResp:
        data = [{"symbol": "TSLA", "price": 100.0}]

    monkeypatch.setattr(price_email, "get_stock_quotes", lambda tickers: DummyResp())

    sent = {"called": False}

    class DummyMessages:
        def send(self, userId, body):
            sent["called"] = True
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

    monkeypatch.setattr(price_email, "get_authenticated_gmail_service", lambda: DummyService())

    result = price_email.send_price_email("TSLA", "to@example.com")
    assert result is False
    assert not sent["called"]


def test_send_price_email_uses_thread(monkeypatch, tmp_path):
    cache_file = tmp_path / "prices.json"
    thread_file = tmp_path / "thread.json"
    monkeypatch.setattr(price_email, "CACHE_FILE", str(cache_file))
    monkeypatch.setattr(price_email, "THREAD_FILE", str(thread_file))
    price_email.save_prices_to_cache({"TSLA": 100.0})
    price_email.save_thread_info("t123", "m123")

    class DummyResp:
        data = [{"symbol": "TSLA", "price": 110.0}]

    monkeypatch.setattr(price_email, "get_stock_quotes", lambda tickers: DummyResp())

    captured = {}

    class DummyMessages:
        def send(self, userId, body):
            captured["body"] = body
            class Exec:
                def execute(self_inner):
                    return {"threadId": body.get("threadId", "t123"), "id": "m124"}
            return Exec()

    class DummyUsers:
        def messages(self):
            return DummyMessages()

    class DummyService:
        def users(self_inner):
            return DummyUsers()

    monkeypatch.setattr(price_email, "get_authenticated_gmail_service", lambda: DummyService())

    sent_message = {}

    class CapturingMIMEText(price_email.MIMEText):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            sent_message["msg"] = self

    monkeypatch.setattr(price_email, "MIMEText", CapturingMIMEText)

    result = price_email.send_price_email("TSLA", "to@example.com")
    assert result is True
    assert captured["body"].get("threadId") == "t123"
    msg = sent_message["msg"]
    assert msg["In-Reply-To"] == "m123"
    assert msg["References"] == "m123"
    with open(thread_file, "r") as f:
        saved = json.load(f)
    assert saved == {"thread_id": "t123", "message_id": "m124"}
