from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SignalBase(BaseModel):
    """Common envelope for all module signals."""

    module: str
    timestamp: datetime
    payload: Dict[str, Any]
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
    payload: SentimentPayload


class TechnicalSignal(SignalBase):
    payload: TechnicalPayload


class TradeAction(BaseModel):
    asset: str
    action: str
    size: float


class TradeProposal(BaseModel):
    regime: str
    actions: List[TradeAction] = Field(..., min_length=1)
    rationale: List[Any]
    risk_flags: Dict[str, Any] = Field(default_factory=dict)
    requires_human: bool = False


class HumanOverrideCommand(BaseModel):
    target_module: str
    command_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str

