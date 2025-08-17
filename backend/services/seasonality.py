"""Seasonality analysis module with simple calendar-based heuristics."""
from __future__ import annotations

from datetime import datetime

from backend.schemas import SeasonalityPayload, SeasonalitySignal
from backend.observability import track


# Basic month-based seasonality map: month -> (pattern, bias)
MONTH_BIASES = {
    1: ("january_effect", 1.0),
    5: ("sell_in_may", -1.0),
    10: ("q4_rally", 0.5),
    11: ("q4_rally", 0.5),
    12: ("q4_rally", 0.5),
}


class SeasonalityAnalyzer:
    """Emit a seasonality signal based on simple calendar effects."""

    name = "seasonality"

    @track("seasonality_generate")
    def generate(self, context):
        asset = "AAPL"
        month = datetime.utcnow().month
        pattern, bias = MONTH_BIASES.get(month, ("none", 0.0))
        confidence = 0.6 if bias else 0.2
        payload = SeasonalityPayload(
            asset=asset,
            bias=bias,
            pattern=pattern,
            confidence=confidence,
        )
        return SeasonalitySignal(
            origin_module=self.name,
            timestamp=datetime.utcnow(),
            payload=payload,
            confidence=payload.confidence,
        )


__all__ = ["SeasonalityAnalyzer"]
