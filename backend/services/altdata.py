"""Alt-data analysis module stub."""
from __future__ import annotations

from datetime import datetime

from backend.schemas import AltDataPayload, AltDataSignal
from backend.observability import track


class AltDataAnalyzer:
    """Produce alternative data signals using a simple heuristic."""

    name = "altdata"

    @track("altdata_generate")
    def generate(self, context):
        asset = "AAPL"
        payload = AltDataPayload(
            asset=asset,
            metric="web_traffic",
            value=0.1,
            confidence=0.5,
        )
        return AltDataSignal(
            origin_module=self.name,
            timestamp=datetime.utcnow(),
            payload=payload,
            confidence=payload.confidence,
        )


__all__ = ["AltDataAnalyzer"]
