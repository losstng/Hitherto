from datetime import datetime

from backend.schemas import (
    SentimentPayload,
    SentimentSignal,
    TechnicalPayload,
    TechnicalSignal,
    HumanOverrideCommand,
    HumanOverridePayload,
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
    assert proposal.payload.status == "AUTO_APPROVED"


def test_overseer_llm_reasoning(monkeypatch):
    class DummyOpenAI:
        api_key = ""

        class ChatCompletion:
            @staticmethod
            def create(*args, **kwargs):
                msg = kwargs["messages"][0]["content"]
                if "output a JSON object" in msg:
                    return {
                        "choices": [
                            {
                                "message": {
                                    "content": "{\"actions\":[{\"asset\":\"AAPL\",\"action\":\"BUY\",\"size\":5,\"rationale\":\"llm\"}]}"
                                }
                            }
                        ]
                    }
                else:
                    return {"choices": [{"message": {"content": "summary"}}]}

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setitem(__import__("sys").modules, "openai", DummyOpenAI)
    playbooks = load_playbooks("backend/config/playbooks.json")
    overseer = Overseer(playbooks)
    result = overseer.run_cycle([sentiment_module, technical_module])
    action = result["proposal"].payload.actions[0]
    assert action.size == 5
    assert result["proposal"].payload.rationale[0] == "llm"
    assert result["summary"] == "summary"
    assert result["proposal"].payload.status == "AUTO_APPROVED"


def test_overseer_risk_veto(monkeypatch):
    playbooks = load_playbooks("backend/config/playbooks.json")
    overseer = Overseer(playbooks)

    def small_risk(proposal):
        from backend.services.risk import RiskReport

        flags = {}
        for a in proposal.payload.actions:
            if a.size > 1:
                flags[a.asset] = "too large"
        return RiskReport(ok=not flags, flags=flags)

    monkeypatch.setattr("backend.services.overseer.risk.evaluate", small_risk)
    result = overseer.run_cycle([sentiment_module, technical_module])
    assert result["proposal"].payload.actions == []
    assert result["proposal"].payload.status == "REJECTED"


def test_overseer_applies_override():
    playbooks = load_playbooks("backend/config/playbooks.json")
    overseer = Overseer(playbooks)

    override = HumanOverrideCommand(
        origin_module="human",
        timestamp=datetime.utcnow(),
        payload=HumanOverridePayload(
            target_module="overseer", command_type="HALT", reason="maintenance"
        ),
    )
    result = overseer.run_cycle([sentiment_module, technical_module], overrides=[override])
    assert result["proposal"].payload.actions == []
    assert result["proposal"].payload.status == "PENDING_REVIEW"
