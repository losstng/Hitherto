"""Intermarket analysis module with optional LLM reasoning."""
from __future__ import annotations

import json
import os
from datetime import datetime

from backend.schemas import IntermarketPayload, IntermarketSignal
from backend.observability import track


class IntermarketAnalyzer:
    """Generate intermarket signals using an LLM when available."""

    name = "intermarket"

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

    def _llm_payload(self, asset: str) -> IntermarketPayload | None:
        prompt = (
            "Assess the impact of a strong US dollar on {asset}. Respond with JSON "
            "containing 'indicator', 'value', 'implication', and 'confidence'."
        ).format(asset=asset)
        try:  # pragma: no cover - network
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp["choices"][0]["message"]["content"].strip()
            data = json.loads(content)
            return IntermarketPayload(
                asset=asset,
                indicator=data.get("indicator", "usd_strength"),
                value=float(data.get("value", 0.0)),
                implication=data.get("implication", "neutral"),
                confidence=float(data.get("confidence", 0.5)),
            )
        except Exception:
            return None

    @track("intermarket_generate")
    def generate(self, context):
        asset = "AAPL"
        payload = self._llm_payload(asset) if self.available else None
        if payload is None:
            payload = IntermarketPayload(
                asset=asset,
                indicator="usd_strength",
                value=0.0,
                implication="neutral",
                confidence=0.5,
            )
        return IntermarketSignal(
            origin_module=self.name,
            timestamp=datetime.utcnow(),
            payload=payload,
            confidence=payload.confidence,
        )


__all__ = ["IntermarketAnalyzer"]
