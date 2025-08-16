from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class MessageEnvelope(BaseModel):
    """Base structure for messages exchanged between modules."""

    timestamp: datetime
    origin_module: str
    message_type: str
    payload: Dict[str, Any]


class SignalBase(MessageEnvelope):
    """Envelope for all module signals."""

    confidence: Optional[float] = None


class SentimentPayload(BaseModel):
    asset: str
    sentiment_score: float
    summary: str
    confidence: float
    rationale: Optional[str] = None


class TechnicalPayload(BaseModel):
    asset: str
    indicator: str
    value: float
    signal_strength: str


class SentimentSignal(SignalBase):
    message_type: Literal["SentimentSignal"] = "SentimentSignal"
    payload: SentimentPayload


class TechnicalSignal(SignalBase):
    message_type: Literal["TechnicalSignal"] = "TechnicalSignal"
    payload: TechnicalPayload


class RegimePayload(BaseModel):
    regime_label: str
    confidence: float


class RegimeSignal(SignalBase):
    message_type: Literal["RegimeSignal"] = "RegimeSignal"
    payload: RegimePayload


class TradeAction(BaseModel):
    asset: str
    action: str
    size: float


class TradeProposalPayload(BaseModel):
    regime: str
    actions: List[TradeAction] = Field(..., min_length=1)
    rationale: List[Any]
    risk_flags: Dict[str, Any] = Field(default_factory=dict)
    requires_human: bool = False
    status: Literal["PENDING", "AUTO_APPROVED", "PENDING_REVIEW", "REJECTED"] = "PENDING"
    adjusted_actions: Optional[List[TradeAction]] = None


class TradeProposal(MessageEnvelope):
    message_type: Literal["TradeProposal"] = "TradeProposal"
    payload: TradeProposalPayload


class ExecutionPayload(BaseModel):
    asset: str
    action: str
    size: float
    price: float
    strategy: str = "IMMEDIATE"


class ExecutionReport(MessageEnvelope):
    message_type: Literal["ExecutionReport"] = "ExecutionReport"
    payload: ExecutionPayload


class HumanOverridePayload(BaseModel):
    target_module: str
    command_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str


class HumanOverrideCommand(MessageEnvelope):
    message_type: Literal["HumanOverrideCommand"] = "HumanOverrideCommand"
    payload: HumanOverridePayload

