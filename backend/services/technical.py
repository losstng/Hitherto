"""Technical analysis module with optional LLM reasoning."""
from __future__ import annotations

import json
import os
from datetime import datetime

from backend.schemas import TechnicalPayload, TechnicalSignal
from backend.observability import track


class TechnicalAnalyzer:
    """Provide moving-average signals using an LLM when available."""

    name = "technical"

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

    def _llm_payload(self, asset: str, price: float, ma: float) -> TechnicalPayload | None:
        prompt = (
            "Given price {price} and moving average {ma} for {asset}, respond with"
            " JSON containing 'indicator', 'value', and 'signal_strength'."
        ).format(price=price, ma=ma, asset=asset)
        try:  # pragma: no cover - network
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp["choices"][0]["message"]["content"].strip()
            data = json.loads(content)
            return TechnicalPayload(
                asset=asset,
                indicator=data.get("indicator", "ma"),
                value=float(data.get("value", price - ma)),
                signal_strength=data.get("signal_strength", "neutral"),
            )
        except Exception:
            return None

    @track("technical_generate")
    def generate(self, context):
        asset = "AAPL"
        price = 100.0
        ma = 95.0
        payload = self._llm_payload(asset, price, ma) if self.available else None
        if payload is None:
            signal = "bullish" if price > ma else "bearish"
            payload = TechnicalPayload(
                asset=asset,
                indicator="ma",
                value=price - ma,
                signal_strength=signal,
            )
        return TechnicalSignal(
            origin_module=self.name,
            timestamp=datetime.utcnow(),
            payload=payload,
        )


__all__ = ["TechnicalAnalyzer"]
