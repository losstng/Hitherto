"""Execution module simulating order fills with LLM summaries."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend import models
from backend.schemas import TradeProposal, ExecutionPayload, ExecutionReport
from .reasoner import LLMReasoner


class ExecutionService:
    """Convert approved proposals into executed decisions."""

    def __init__(self, reasoner: Optional[LLMReasoner] = None) -> None:
        self.reasoner = reasoner or LLMReasoner()

    def _mock_price(self, asset: str) -> float:  # pragma: no cover - deterministic mock
        return 100.0

    def execute(
        self, proposal: TradeProposal, proposal_id: int, db: Optional[Session] = None
    ) -> List[ExecutionReport]:
        """Execute the proposal and persist decisions.

        Returns a list of execution reports summarising each order.
        """
        session = db or SessionLocal()
        own_session = db is None
        reports: List[ExecutionReport] = []
        try:
            for action in proposal.payload.actions:
                if action.action.upper() == "HOLD" or action.size <= 0:
                    continue
                price = self._mock_price(action.asset)
                payload = ExecutionPayload(
                    asset=action.asset,
                    action=action.action,
                    size=action.size,
                    price=price,
                )
                report = ExecutionReport(
                    origin_module="execution",
                    timestamp=datetime.utcnow(),
                    payload=payload,
                )
                summary = self.reasoner.summarize_execution(payload.model_dump())
                session.add(
                    models.Decision(
                        proposal_id=proposal_id,
                        executed_action=payload.model_dump(),
                        human_note=summary,
                    )
                )
                reports.append(report)
            session.commit()
        finally:
            if own_session:
                session.close()
        return reports


# shared instance similar to risk helper
execution = ExecutionService()
