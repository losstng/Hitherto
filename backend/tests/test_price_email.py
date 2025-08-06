import pytest

from backend.services import price_email


def test_send_price_email_skips_when_unchanged(monkeypatch, tmp_path):
    cache_file = tmp_path / "prices.json"
    monkeypatch.setattr(price_email, "CACHE_FILE", str(cache_file))
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
