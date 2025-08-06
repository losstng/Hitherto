import base64
from email import message_from_bytes
import pandas as pd
import pytest
from backend.services import volume_monitor


def test_detect_volume_spike_triggers():
    volumes = [100, 100, 100, 100, 300]
    index = pd.date_range("2024-01-01", periods=5, freq="5min")
    df = pd.DataFrame({"Volume": volumes}, index=index)
    spike, last, avg = volume_monitor.detect_volume_spike(df)
    assert bool(spike)
    assert last == 300
    assert avg == 100


def test_detect_volume_spike_no_trigger():
    volumes = [100] * 5
    index = pd.date_range("2024-01-01", periods=5, freq="5min")
    df = pd.DataFrame({"Volume": volumes}, index=index)
    spike, last, avg = volume_monitor.detect_volume_spike(df)
    assert not bool(spike)
    assert last == 100
    assert avg == 100


def test_alert_file_roundtrip(tmp_path, monkeypatch):
    alert_file = tmp_path / "alerts.json"
    monkeypatch.setattr(volume_monitor, "ALERT_FILE", alert_file)
    volume_monitor.save_alerted_volumes({"TSLA": {"last_volume": 123, "alerted": "ts"}})
    data = volume_monitor.load_alerted_volumes()
    assert data["TSLA"]["last_volume"] == 123


def test_run_loop_skips_duplicate_alerts(monkeypatch, tmp_path):
    alert_file = tmp_path / "alerts.json"
    monkeypatch.setattr(volume_monitor, "ALERT_FILE", alert_file)
    monkeypatch.setattr(volume_monitor, "DEFAULT_TICKERS", ["TSLA"])

    df = pd.DataFrame(
        {"Volume": [100, 100, 100, 100, 300]},
        index=pd.date_range("2024-01-01", periods=5, freq="5min"),
    )
    monkeypatch.setattr(volume_monitor, "update_5min_csv", lambda t: df)

    sent = []

    def fake_send(*args, **kwargs):
        sent.append(args)
        return True

    monkeypatch.setattr(volume_monitor, "send_volume_email", fake_send)

    calls = {"n": 0}

    def fake_sleep(_):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise StopIteration

    monkeypatch.setattr(volume_monitor.time, "sleep", fake_sleep)

    with pytest.raises(StopIteration):
        volume_monitor.run_volume_monitor_loop(interval=0)

    assert len(sent) == 1


def test_send_volume_email_subject_contains_window(monkeypatch):
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

    monkeypatch.setattr(volume_monitor, "get_authenticated_gmail_service", lambda: DummyService())
    volume_monitor.send_volume_email("TSLA", 1500, 1000, 5, "to@example.com")
    msg = message_from_bytes(base64.urlsafe_b64decode(sent["raw"].encode()))
    assert "5m" in msg["Subject"]
