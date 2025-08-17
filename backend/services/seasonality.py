"""Seasonality analysis module with optional LLM reasoning."""
from __future__ import annotations

import json
import os
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
    """Emit a seasonality signal using an LLM when available."""

    name = "seasonality"

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self._client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:  # pragma: no cover - optional import
                import openai

                openai.api_key = api_key
                self._client = openai
            except Exception:
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def _llm_payload(self, asset: str) -> SeasonalityPayload | None:
        month = datetime.utcnow().month
        prompt = (
            "Identify any notable seasonal bias for month {month} and asset {asset}."
            " Respond with JSON containing 'pattern', 'bias' (-1 to 1) and 'confidence'."
        ).format(month=month, asset=asset)
        try:  # pragma: no cover - network
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp["choices"][0]["message"]["content"].strip()
            data = json.loads(content)
            return SeasonalityPayload(
                asset=asset,
                bias=float(data.get("bias", 0.0)),
                pattern=data.get("pattern", "none"),
                confidence=float(data.get("confidence", 0.5)),
            )
        except Exception:
            return None

    @track("seasonality_generate")
    def generate(self, context):
        asset = "AAPL"
        payload = self._llm_payload(asset) if self.available else None
        if payload is None:
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
