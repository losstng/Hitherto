from datetime import datetime

from backend.schemas import (
    SentimentPayload,
    SentimentSignal,
    TechnicalPayload,
    TechnicalSignal,
)
from backend.services.overseer import Overseer, load_playbooks


def sentiment_module():
    payload = SentimentPayload(
        asset="AAPL",
        sentiment_score=0.8,
        summary="positive",
        confidence=0.9,
    )
    return SentimentSignal(
        origin_module="sentiment",
        timestamp=datetime.utcnow(),
        payload=payload,
    )


def technical_module():
    payload = TechnicalPayload(
        asset="AAPL",
        indicator="MA",
        value=1.0,
        signal_strength="bullish",
    )
    return TechnicalSignal(
        origin_module="technical",
        timestamp=datetime.utcnow(),
        payload=payload,
    )


def test_overseer_run_cycle():
    playbooks = load_playbooks("backend/config/playbooks.json")
    overseer = Overseer(playbooks)
    result = overseer.run_cycle([sentiment_module, technical_module])

    proposal = result["proposal"]
    assert proposal.message_type == "TradeProposal"
    assert proposal.payload.actions[0].action == "BUY"
    assert result["regime_signal"].payload.regime_label == "bull"
    assert result["risk_report"].ok
    assert result["summary"]


def test_overseer_llm_reasoning(monkeypatch):
    class DummyOpenAI:
        api_key = ""

        class ChatCompletion:
            @staticmethod
            def create(*args, **kwargs):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "{\"actions\":[{\"asset\":\"AAPL\",\"action\":\"BUY\",\"size\":5,\"rationale\":\"llm\"}]}"
                            }
                        }
                    ]
                }

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setitem(__import__("sys").modules, "openai", DummyOpenAI)
    playbooks = load_playbooks("backend/config/playbooks.json")
    overseer = Overseer(playbooks)
    result = overseer.run_cycle([sentiment_module, technical_module])
    action = result["proposal"].payload.actions[0]
    assert action.size == 5
    assert result["proposal"].payload.rationale[0] == "llm"
