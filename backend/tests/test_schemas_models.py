from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.schemas.core.schemas import (
    HumanOverrideCommand,
    HumanOverridePayload,
    SentimentPayload,
    SentimentSignal,
    TradeAction,
    TradeProposal,
    TradeProposalPayload,
    ExecutionPayload,
    ExecutionReport,
)


def test_sentiment_signal_validation():
    payload = SentimentPayload(
        asset="AAPL",
        sentiment_score=0.7,
        summary="Bullish earnings news",
        confidence=0.9,
    )
    sig = SentimentSignal(
        origin_module="sentiment",
        timestamp=datetime.utcnow(),
        payload=payload,
        confidence=0.9,
    )
    assert sig.payload.asset == "AAPL"
    assert sig.message_type == "SentimentSignal"

    with pytest.raises(ValidationError):
        SentimentSignal(
            origin_module="sentiment",
            timestamp=datetime.utcnow(),
            payload={"asset": "AAPL"},  # missing required fields
        )


def test_trade_proposal_requires_actions():
    action = TradeAction(asset="XYZ", action="BUY", size=1000)
    payload = TradeProposalPayload(
        regime="bull",
        actions=[action],
        rationale=["signal_id:1"],
        risk_flags={},
    )
    proposal = TradeProposal(
        origin_module="overseer",
        timestamp=datetime.utcnow(),
        payload=payload,
    )
    assert proposal.payload.actions[0].asset == "XYZ"

    with pytest.raises(ValidationError):
        bad_payload = TradeProposalPayload(regime="bull", actions=[], rationale=["none"])
        TradeProposal(origin_module="overseer", timestamp=datetime.utcnow(), payload=bad_payload)


def test_human_override_command_validation():
    payload = HumanOverridePayload(
        target_module="Risk",
        command_type="TIGHTEN",
        reason="policy_uncertainty",
    )
    cmd = HumanOverrideCommand(
        origin_module="human",
        timestamp=datetime.utcnow(),
        payload=payload,
    )
    assert cmd.payload.target_module == "Risk"

    with pytest.raises(ValidationError):
        HumanOverrideCommand(
            origin_module="human",
            timestamp=datetime.utcnow(),
            payload={"target_module": "Risk", "command_type": "TIGHTEN"},
        )


def test_execution_report_validation():
    payload = ExecutionPayload(
        asset="AAPL", action="BUY", size=10, price=100.0
    )
    report = ExecutionReport(
        origin_module="execution",
        timestamp=datetime.utcnow(),
        payload=payload,
    )
    assert report.payload.price == 100.0
    with pytest.raises(ValidationError):
        ExecutionReport(
            origin_module="execution",
            timestamp=datetime.utcnow(),
            payload={"asset": "AAPL"},
        )

