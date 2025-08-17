"""Overseer service coordinating signals and trade proposals."""
from __future__ import annotations

from datetime import datetime
import json
import time
from typing import Dict, List, Any, Tuple, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.schemas import (
    RegimeSignal,
    RegimePayload,
    SignalBase,
    SentimentSignal,
    TechnicalSignal,
    FundamentalSignal,
    AltDataSignal,
    SeasonalitySignal,
    IntermarketSignal,
    TradeAction,
    HumanOverrideCommand,
    TradeProposal,
    TradeProposalPayload,
    ExecutionReport,
)
from backend.database import SessionLocal
from backend import models
from . import risk
from .reasoner import LLMReasoner
from .execution import execution, ExecutionService
from .coordinator import ModuleCoordinator
from backend.observability import track, cycle_latency, cycle_success, cycle_failure


def load_playbooks(path: str) -> Dict[str, Dict[str, float]]:
    """Load playbook weight configuration from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class RegimeClassifier:
    """Simple regime classifier with hysteresis and confirmation."""

    def __init__(self, *, session: Optional[Session] = None, dwell: int = 3):
        self._session = session
        self._dwell = dwell
        self._current = "bull"
        self._pending: Optional[str] = None
        self._count = 0
        self.awaiting_confirmation = False

    def _determine_regime(self) -> str:
        return "bull" if datetime.utcnow().minute % 2 == 0 else "bear"

    def _log(self, label: str, confirmed: bool) -> None:
        try:
            session = self._session or SessionLocal()
            session.add(
                models.Regime(
                    effective_at=datetime.utcnow(),
                    regime_label=label,
                    classified_by="AI",
                    confidence=1.0,
                    confirmed=confirmed,
                )
            )
            session.commit()
        except SQLAlchemyError:
            pass
        finally:
            if self._session is None:
                try:
                    session.close()
                except Exception:
                    pass

    @property
    def active_regime(self) -> str:
        return self._current

    def confirm_pending(self) -> None:
        if self.awaiting_confirmation and self._pending:
            self._current = self._pending
            self.awaiting_confirmation = False
            self._log(self._current, True)
            self._pending = None

    def classify(self) -> RegimeSignal:
        candidate = self._determine_regime()
        if candidate != self._current:
            if self._pending != candidate:
                self._pending = candidate
                self._count = 1
            else:
                self._count += 1
                if self._count >= self._dwell:
                    self.awaiting_confirmation = True
                    self._log(candidate, False)
        else:
            self._pending = None
            self._count = 0
        payload = RegimePayload(regime_label=self._current, confidence=1.0)
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
        playbooks: Dict[str, Any],
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
        return self.playbooks.get(regime, {}).get("weights", {})

    def _review_threshold(self, regime: str) -> Optional[float]:
        return self.playbooks.get(regime, {}).get("review_threshold")

    def _score_signal(self, sig: SignalBase) -> float:
        if isinstance(sig, SentimentSignal):
            return sig.payload.sentiment_score
        if isinstance(sig, TechnicalSignal):
            mapping = {"bullish": 1.0, "bearish": -1.0}
            return mapping.get(sig.payload.signal_strength.lower(), 0.0)
        if isinstance(sig, FundamentalSignal):
            return sig.payload.mispricing_percent / 100.0
        if isinstance(sig, AltDataSignal):
            return sig.payload.value
        if isinstance(sig, SeasonalitySignal):
            return sig.payload.seasonal_strength
        if isinstance(sig, IntermarketSignal):
            return sig.payload.value
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

    def apply_overrides(
        self, proposal: TradeProposal, overrides: List[HumanOverrideCommand]
    ) -> None:
        """Modify the proposal according to any active human overrides."""
        for cmd in overrides:
            if cmd.payload.target_module.lower() != "overseer":
                continue
            if cmd.payload.command_type.upper() in {"HALT", "TIGHTEN"}:
                proposal.payload.actions = []
                proposal.payload.rationale.append(
                    f"halted by human: {cmd.payload.reason}"
                )
                proposal.payload.requires_human = True

    @track("overseer_cycle")
    def run_cycle(
        self,
        coordinator: ModuleCoordinator,
        overrides: Optional[List[HumanOverrideCommand]] = None,
        db: Optional[Session] = None,
    ):
        """Run a full overseer cycle: classify regime, gather signals, propose trades."""
        start = time.perf_counter()
        session = db or SessionLocal()
        own_session = db is None
        try:
            regime_signal = self.regime_classifier.classify()
            regime = self.regime_classifier.active_regime
            signals = coordinator.run()
            proposal = self.propose_trades(signals, regime)
            report = risk.evaluate(proposal)
            if not report.ok and report.suggested:
                adjusted: List[TradeAction] = []
                for action in proposal.payload.actions:
                    if action.asset in report.suggested:
                        new_size = report.suggested[action.asset]
                        adjusted.append(
                            TradeAction(
                                asset=action.asset,
                                action=action.action,
                                size=new_size,
                            )
                        )
                        proposal.payload.rationale.append(
                            f"size for {action.asset} adjusted to {new_size} by risk"
                        )
                    else:
                        adjusted.append(action)
                proposal.payload.adjusted_actions = adjusted
                proposal.payload.actions = adjusted
                report.ok = True
            proposal.payload.risk_flags = report.flags
            if not report.ok:
                proposal.payload.actions = []
                proposal.payload.rationale.append(
                    f"rejected by risk: {report.flags}"
                )
                proposal.payload.requires_human = True
                proposal.payload.status = "REJECTED"
            else:
                self.apply_overrides(proposal, overrides or [])
                threshold = self._review_threshold(regime)
                actions_to_check = proposal.payload.adjusted_actions or proposal.payload.actions
                if threshold is not None and any(a.size > threshold for a in actions_to_check):
                    proposal.payload.requires_human = True
                if proposal.payload.requires_human:
                    proposal.payload.status = "PENDING_REVIEW"
                else:
                    proposal.payload.status = "AUTO_APPROVED"
            summary = self.summarize(proposal)
            exec_reports: List[ExecutionReport] = []
            try:
                for sig in signals:
                    session.add(
                        models.Signal(
                            module_name=sig.origin_module,
                            signal_type=sig.message_type,
                            content_json=sig.payload.model_dump(),
                            generated_at=sig.timestamp,
                        )
                    )
                session.commit()
                status_map = {
                    "AUTO_APPROVED": models.ProposalStatus.APPROVED,
                    "PENDING_REVIEW": models.ProposalStatus.PENDING_REVIEW,
                    "REJECTED": models.ProposalStatus.REJECTED,
                }
                db_proposal = models.Proposal(
                    proposal_json=proposal.payload.model_dump(),
                    status=status_map.get(proposal.payload.status, models.ProposalStatus.PENDING_REVIEW),
                )
                session.add(db_proposal)
                session.commit()
                for cmd in overrides or []:
                    session.add(
                        models.Override(
                            module=cmd.payload.target_module,
                            action=cmd.payload.command_type,
                            details_json=cmd.payload.parameters,
                            user=cmd.payload.parameters.get("user", "unknown"),
                            proposal_id=db_proposal.id,
                        )
                    )
                session.commit()
                if proposal.payload.status == "AUTO_APPROVED":
                    exec_reports = execution.execute(
                        proposal, db_proposal.id, session
                    )
                cycle_success.inc()
            except SQLAlchemyError:
                session.rollback()
                cycle_failure.inc()
            finally:
                if own_session:
                    try:
                        session.close()
                    except Exception:
                        pass
            return {
                "regime_signal": regime_signal,
                "signals": signals,
                "proposal": proposal,
                "risk_report": report,
                "summary": summary,
                "executions": exec_reports,
            }
        finally:
            cycle_latency.observe(time.perf_counter() - start)
