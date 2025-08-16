"""Risk management helpers leveraging LLM reasoning."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel

from backend.schemas import TradeProposal


class LLMRiskAdvisor:
    """LLM wrapper used to summarise risk evaluations."""

    def __init__(self, model: str = "gpt-3.5-turbo") -> None:
        self.model = model
        self._client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:  # pragma: no cover - import guarded
                import openai

                openai.api_key = api_key
                self._client = openai
            except Exception:  # pragma: no cover - network import failure
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def analyze(self, context: Dict[str, Any]) -> str:
        """Return a human readable summary for the risk context."""

        if not self.available:
            # Fall back to a naive summary
            flags = context.get("flags", {})
            return ", ".join(flags.values()) if flags else "within limits"

        prompt = (
            "You are an AI risk officer. Given the JSON context of a proposed trade "
            "and computed risk metrics, provide a short recommendation summarizing "
            "any breaches and suggested adjustments. JSON context: "
            + json.dumps(context, default=str)
        )
        try:  # pragma: no cover - network call
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp["choices"][0]["message"]["content"].strip()
        except Exception:  # pragma: no cover - network failure
            flags = context.get("flags", {})
            return ", ".join(flags.values()) if flags else "within limits"


class RiskReport(BaseModel):
    """Structured risk evaluation result."""

    ok: bool
    flags: Dict[str, Any]
    suggested: Dict[str, float] = {}
    metrics: Dict[str, float] = {}
    summary: Optional[str] = None


def _var_from_history(returns: List[float], quantile: float = 0.01) -> float:
    """Compute one-sided historical VaR for a series of returns."""

    if not returns:
        return 0.0
    arr = np.asarray(returns)
    return float(-np.quantile(arr, quantile))


def evaluate(
    proposal: TradeProposal,
    *,
    history: Optional[Dict[str, List[float]]] = None,
    max_size: float = 100,
    var_limit: float = 0.02,
    advisor: Optional[LLMRiskAdvisor] = None,
) -> RiskReport:
    """Evaluate a proposal using simple rules and VaR metrics.

    Args:
        proposal: The trade proposal to evaluate.
        history: Optional mapping of asset -> list of historical returns.
        max_size: Maximum allowed size for any trade action.
        var_limit: Maximum allowed 99% one-day VaR per asset.
        advisor: Optional LLM risk advisor for summarisation.
    """

    flags: Dict[str, Any] = {}
    suggested: Dict[str, float] = {}
    metrics: Dict[str, float] = {}

    # Check position limits
    for action in proposal.payload.actions:
        if action.size > max_size:
            flags[action.asset] = f"size {action.size} exceeds limit {max_size}"
            suggested[action.asset] = max_size

    # Compute per-asset VaR if history is provided
    if history:
        for asset, returns in history.items():
            var = _var_from_history(returns)
            metrics[f"VaR_{asset}"] = var
            if var > var_limit:
                key = f"VaR_{asset}"
                flags[key] = f"VaR {var:.4f} exceeds limit {var_limit}"
                # Suggest scaling actions involving this asset proportionally
                for action in proposal.payload.actions:
                    if action.asset == asset:
                        scale = var_limit / var if var > 0 else 0
                        suggested[action.asset] = max(0.0, action.size * scale)

    ok = not flags

    advisor = advisor or LLMRiskAdvisor()
    summary = advisor.analyze(
        {
            "proposal": proposal.payload.model_dump(),
            "metrics": metrics,
            "flags": flags,
            "suggested": suggested,
        }
    )

    return RiskReport(
        ok=ok, flags=flags, suggested=suggested, metrics=metrics, summary=summary
    )

