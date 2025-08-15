"""Overseer service coordinating signals and trade proposals."""
from __future__ import annotations

from datetime import datetime
import json
from typing import Callable, Dict, List, Any, Tuple, Optional

from backend.schemas import (
    RegimeSignal,
    RegimePayload,
    SignalBase,
    SentimentSignal,
    TechnicalSignal,
    TradeAction,
    TradeProposal,
    TradeProposalPayload,
)
from . import risk
from .reasoner import LLMReasoner


def load_playbooks(path: str) -> Dict[str, Dict[str, float]]:
    """Load playbook weight configuration from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class RegimeClassifier:
    """Placeholder regime classifier returning a static regime."""

    def classify(self) -> RegimeSignal:
        payload = RegimePayload(regime_label="bull", confidence=1.0)
        return RegimeSignal(
            origin_module="regime",
            timestamp=datetime.utcnow(),
            payload=payload,
            confidence=payload.confidence,
        )


class Overseer:
    """Central coordinator for signal fusion and proposal generation."""

    def __init__(
        self,
        playbooks: Dict[str, Dict[str, float]],
        *,
        reasoner: Optional[LLMReasoner] = None,
        regime_classifier: Optional[RegimeClassifier] = None,
    ):
        self.playbooks = playbooks
        self.regime_classifier = regime_classifier or RegimeClassifier()
        self.reasoner = reasoner or LLMReasoner()

    # -----------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------
    def _weights(self, regime: str) -> Dict[str, float]:
        return self.playbooks.get(regime, {})

    def _score_signal(self, sig: SignalBase) -> float:
        if isinstance(sig, SentimentSignal):
            return sig.payload.sentiment_score
        if isinstance(sig, TechnicalSignal):
            mapping = {"bullish": 1.0, "bearish": -1.0}
            return mapping.get(sig.payload.signal_strength.lower(), 0.0)
        return 0.0

    # -----------------------------------------------------
    def fuse_signals(self, signals: List[SignalBase], regime: str) -> Dict[str, float]:
        weights = self._weights(regime)
        scores: Dict[str, float] = {}
        for sig in signals:
            asset = getattr(sig.payload, "asset", None)
            if asset is None:
                continue
            weight = weights.get(sig.origin_module, 0.0)
            scores[asset] = scores.get(asset, 0.0) + weight * self._score_signal(sig)
        return scores

    def _rule_based_actions(self, scores: Dict[str, float]) -> Tuple[List[TradeAction], List[Any]]:
        actions: List[TradeAction] = []
        rationale: List[Any] = []
        for asset, score in scores.items():
            if score > 0:
                actions.append(TradeAction(asset=asset, action="BUY", size=10))
                rationale.append(f"{asset} score {score:.2f} -> BUY")
            elif score < 0:
                actions.append(TradeAction(asset=asset, action="SELL", size=10))
                rationale.append(f"{asset} score {score:.2f} -> SELL")
        return actions, rationale

    def propose_trades(self, signals: List[SignalBase], regime: str) -> TradeProposal:
        if self.reasoner.available:
            actions, rationale = self.reasoner.decide(regime, signals, self._weights(regime))
        else:
            scores = self.fuse_signals(signals, regime)
            actions, rationale = self._rule_based_actions(scores)
        if not actions:
            actions = [TradeAction(asset="NONE", action="HOLD", size=0)]
        payload = TradeProposalPayload(regime=regime, actions=actions, rationale=rationale)
        return TradeProposal(
            origin_module="overseer",
            timestamp=datetime.utcnow(),
            payload=payload,
        )

    def summarize(self, proposal: TradeProposal) -> str:
        """Create a human-readable summary via the configured reasoner."""
        return self.reasoner.summarize(proposal)

    def run_cycle(self, modules: List[Callable[[], SignalBase]]):
        """Run a full overseer cycle: classify regime, gather signals, propose trades."""
        regime_signal = self.regime_classifier.classify()
        signals = [m() for m in modules]
        proposal = self.propose_trades(signals, regime_signal.payload.regime_label)
        report = risk.evaluate(proposal)
        proposal.payload.risk_flags = report.flags
        proposal.payload.requires_human = not report.ok
        summary = self.summarize(proposal)
        return {
            "regime_signal": regime_signal,
            "signals": signals,
            "proposal": proposal,
            "risk_report": report,
            "summary": summary,
        }
