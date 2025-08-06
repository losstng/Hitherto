import base64
from email import message_from_bytes
import pandas as pd
from backend.services import volume_monitor


def test_detect_volume_spike_triggers():
    volumes = [100] * 5 + [300] * 5
    index = pd.date_range("2024-01-01", periods=10, freq="min")
    df = pd.DataFrame({"Volume": volumes}, index=index)
    spike, last, avg = volume_monitor.detect_volume_spike(df)
    assert bool(spike)
    assert last == 1500
    assert avg == 900


def test_detect_volume_spike_no_trigger():
    volumes = [100] * 10
    index = pd.date_range("2024-01-01", periods=10, freq="min")
    df = pd.DataFrame({"Volume": volumes}, index=index)
    spike, last, avg = volume_monitor.detect_volume_spike(df)
    assert not bool(spike)
    assert last == 500
    assert avg == 500


def test_volume_cache_roundtrip(tmp_path, monkeypatch):
    cache_file = tmp_path / "vol.json"
    monkeypatch.setattr(volume_monitor, "CACHE_FILE", str(cache_file))
    volume_monitor.save_volumes_to_cache({"TSLA": 123})
    data = volume_monitor.load_cached_volumes()
    assert data["TSLA"] == 123


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
