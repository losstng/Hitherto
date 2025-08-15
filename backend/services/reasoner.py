"""LLM-based reasoning helper for the Overseer."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

from backend.schemas import SignalBase, TradeAction, TradeProposal


class LLMReasoner:
    """Use an LLM to transform signals into trade actions."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self._client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:  # pragma: no cover - import guarded
                import openai

                openai.api_key = api_key
                self._client = openai
            except Exception:
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def decide(
        self,
        regime: str,
        signals: List[SignalBase],
        playbook: Dict[str, float],
    ) -> Tuple[List[TradeAction], List[str]]:
        """Return trade actions and rationales via the LLM."""
        if not self.available:
            return [], []

        context = {
            "regime": regime,
            "playbook_weights": playbook,
            "signals": [s.model_dump() for s in signals],
        }
        prompt = (
            "You are an AI trading strategist. "
            "Given the JSON context, output a JSON object with an 'actions' list. "
            "Each action must include asset, action (BUY or SELL), size (integer), and rationale. "
            "JSON context: " + json.dumps(context, default=str)
        )
        try:  # pragma: no cover - network
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp["choices"][0]["message"]["content"].strip()
            data = json.loads(content)
            actions = [
                TradeAction(**a)
                for a in data.get("actions", [])
                if {"asset", "action", "size"} <= a.keys()
            ]
            rationales = [a.get("rationale", "") for a in data.get("actions", [])]
            return actions, rationales
        except Exception:
            return [], []

    def summarize(self, proposal: TradeProposal) -> str:
        """Return a human readable summary via the LLM."""
        parts = [f"{a.action} {a.size} {a.asset}" for a in proposal.payload.actions]
        if not self.available:
            return "; ".join(parts)
        prompt = (
            "Summarize the following trade proposal in one sentence: "
            + json.dumps(proposal.payload.model_dump(), default=str)
        )
        try:  # pragma: no cover - network
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp["choices"][0]["message"]["content"].strip()
        except Exception:
            return "; ".join(parts)
