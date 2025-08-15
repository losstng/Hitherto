"""Simple risk module for evaluating trade proposals."""
from typing import Dict, Any

from pydantic import BaseModel

from backend.schemas import TradeProposal


class RiskReport(BaseModel):
    """Structured risk evaluation result."""

    ok: bool
    flags: Dict[str, Any]


def evaluate(proposal: TradeProposal, max_size: float = 100) -> RiskReport:
    """Evaluate a proposal and flag actions exceeding limits.

    Args:
        proposal: The trade proposal to evaluate.
        max_size: Maximum allowed size for any trade action.
    """
    flags: Dict[str, Any] = {}
    for action in proposal.payload.actions:
        if action.size > max_size:
            flags[action.asset] = f"size {action.size} exceeds limit {max_size}"
    ok = not flags
    return RiskReport(ok=ok, flags=flags)
