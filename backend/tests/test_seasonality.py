from datetime import datetime

import backend.services.seasonality as seasonality
from backend.schemas import SeasonalityPayload, SeasonalitySignal
from backend.services import SeasonalityAnalyzer


def test_seasonality_signal_model():
    payload = SeasonalityPayload(
        asset="AAPL", bias=1.0, pattern="january_effect", confidence=0.6
    )
    sig = SeasonalitySignal(
        origin_module="seasonality",
        timestamp=datetime.utcnow(),
        payload=payload,
        confidence=payload.confidence,
    )
    assert sig.payload.bias == 1.0
    assert sig.payload.pattern == "january_effect"


def test_seasonality_analyzer_bias(monkeypatch):
    analyzer = SeasonalityAnalyzer()

    monkeypatch.setattr(
        seasonality,
        "datetime",
        type("dt", (), {"utcnow": staticmethod(lambda: datetime(2024, 1, 15))}),
    )
    sig = analyzer.generate({})
    assert sig.payload.pattern == "january_effect"
    assert sig.payload.bias == 1.0

    monkeypatch.setattr(
        seasonality,
        "datetime",
        type("dt", (), {"utcnow": staticmethod(lambda: datetime(2024, 5, 15))}),
    )
    sig2 = analyzer.generate({})
    assert sig2.payload.pattern == "sell_in_may"
    assert sig2.payload.bias == -1.0
