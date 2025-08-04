import pandas as pd
from backend.services.volume_monitor import detect_volume_spike


def test_detect_volume_spike_triggers():
    volumes = [100] * 5 + [300] * 5
    index = pd.date_range("2024-01-01", periods=10, freq="min")
    df = pd.DataFrame({"Volume": volumes}, index=index)
    spike, last, avg = detect_volume_spike(df)
    assert bool(spike)
    assert last == 1500
    assert avg == 900


def test_detect_volume_spike_no_trigger():
    volumes = [100] * 10
    index = pd.date_range("2024-01-01", periods=10, freq="min")
    df = pd.DataFrame({"Volume": volumes}, index=index)
    spike, last, avg = detect_volume_spike(df)
    assert not bool(spike)
    assert last == 500
    assert avg == 500
