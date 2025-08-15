from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.schemas.core.schemas import (
    HumanOverrideCommand,
    SentimentPayload,
    SentimentSignal,
    TradeAction,
    TradeProposal,
)


def test_sentiment_signal_validation():
    payload = SentimentPayload(
        asset="AAPL",
        sentiment_score=0.7,
        summary="Bullish earnings news",
        confidence=0.9,
    )
    sig = SentimentSignal(
        module="sentiment",
        timestamp=datetime.utcnow(),
        payload=payload,
        confidence=0.9,
    )
    assert sig.payload.asset == "AAPL"

    with pytest.raises(ValidationError):
        SentimentSignal(
            module="sentiment",
            timestamp=datetime.utcnow(),
            payload={"asset": "AAPL"},  # missing required fields
        )


def test_trade_proposal_requires_actions():
    action = TradeAction(asset="XYZ", action="BUY", size=1000)
    proposal = TradeProposal(
        regime="bull",
        actions=[action],
        rationale=["signal_id:1"],
        risk_flags={},
    )
    assert proposal.actions[0].asset == "XYZ"

    with pytest.raises(ValidationError):
        TradeProposal(regime="bull", actions=[], rationale=["none"])


def test_human_override_command_validation():
    cmd = HumanOverrideCommand(
        target_module="Risk",
        command_type="TIGHTEN",
        reason="policy_uncertainty",
    )
    assert cmd.target_module == "Risk"

    with pytest.raises(ValidationError):
        HumanOverrideCommand(target_module="Risk", command_type="TIGHTEN")

