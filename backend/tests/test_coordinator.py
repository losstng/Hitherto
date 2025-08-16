from datetime import datetime

from backend.schemas import SentimentPayload, SentimentSignal, TechnicalPayload, TechnicalSignal
from backend.services import ModuleCoordinator


class FirstModule:
    name = "sentiment"

    def generate(self, context):
        payload = SentimentPayload(asset="AAPL", sentiment_score=1.0, summary="pos", confidence=1.0)
        return SentimentSignal(origin_module=self.name, timestamp=datetime.utcnow(), payload=payload)


class SecondModule:
    name = "technical"

    def generate(self, context):
        # ensure context passed includes first module
        assert "sentiment" in context
        payload = TechnicalPayload(asset="AAPL", indicator="ma", value=1.0, signal_strength="bullish")
        return TechnicalSignal(origin_module=self.name, timestamp=datetime.utcnow(), payload=payload)


def test_coordinator_runs_modules_with_context():
    coord = ModuleCoordinator([FirstModule(), SecondModule()])
    signals = coord.run()
    assert len(signals) == 2
    assert "sentiment" in coord.context
    assert "technical" in coord.context
