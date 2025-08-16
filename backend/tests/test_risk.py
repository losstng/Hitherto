from datetime import datetime

from backend.schemas import TradeAction, TradeProposal, TradeProposalPayload
from backend.services import risk


def test_risk_var_and_llm(monkeypatch):
    class DummyOpenAI:
        api_key = ""

        class ChatCompletion:
            @staticmethod
            def create(*args, **kwargs):
                return {"choices": [{"message": {"content": "limit breached"}}]}

    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setitem(__import__("sys").modules, "openai", DummyOpenAI)

    proposal = TradeProposal(
        origin_module="overseer",
        timestamp=datetime.utcnow(),
        payload=TradeProposalPayload(
            regime="bull",
            actions=[TradeAction(asset="AAPL", action="BUY", size=10)],
            rationale=[],
        ),
    )

    history = {"AAPL": [-0.03] * 100}
    report = risk.evaluate(proposal, history=history, var_limit=0.02)

    assert "VaR_AAPL" in report.flags
    assert report.summary == "limit breached"

