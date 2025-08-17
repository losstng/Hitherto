"""Seasonality analysis module stub."""
from __future__ import annotations

from datetime import datetime

from backend.schemas import SeasonalityPayload, SeasonalitySignal
from backend.observability import track


class SeasonalityAnalyzer:
    """Emit a simple seasonality signal based on the current month."""

    name = "seasonality"

    @track("seasonality_generate")
    def generate(self, context):
        asset = "AAPL"
        month = datetime.utcnow().month
        pattern = "jan_effect" if month == 1 else "none"
        strength = 1.0 if month == 1 else 0.0
        payload = SeasonalityPayload(
            asset=asset,
            seasonal_strength=strength,
            pattern=pattern,
            confidence=0.5,
        )
        return SeasonalitySignal(
            origin_module=self.name,
            timestamp=datetime.utcnow(),
            payload=payload,
            confidence=payload.confidence,
        )


__all__ = ["SeasonalityAnalyzer"]
