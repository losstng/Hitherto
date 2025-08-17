"""Fundamentals analysis module using a basic P/E heuristic."""
from __future__ import annotations

import json
import os
from datetime import datetime

from backend.schemas import FundamentalPayload, FundamentalSignal
from backend.observability import track


class FundamentalsAnalyzer:
    """Estimate fair value using an LLM when available."""

    name = "fundamentals"

    def __init__(self, eps: float = 5.0, benchmark_pe: float = 15.0, price: float = 100.0, model: str = "gpt-3.5-turbo"):
        self.eps = eps
        self.benchmark_pe = benchmark_pe
        self.price = price
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

    def _llm_payload(self) -> FundamentalPayload | None:
        prompt = (
            "You are a valuation analyst. Given EPS {eps}, benchmark PE {pe}, and "
            "current price {price}, respond with JSON containing 'fair_value', "
            "'mispricing_percent', 'confidence', and 'rationale'."
        ).format(eps=self.eps, pe=self.benchmark_pe, price=self.price)
        try:  # pragma: no cover - network
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp["choices"][0]["message"]["content"].strip()
            data = json.loads(content)
            return FundamentalPayload(
                asset="AAPL",
                fair_value_estimate=float(data.get("fair_value", 0.0)),
                mispricing_percent=float(data.get("mispricing_percent", 0.0)),
                confidence=float(data.get("confidence", 0.5)),
                rationale=data.get("rationale", "LLM valuation"),
            )
        except Exception:
            return None

    @track("fundamentals_generate")
    def generate(self, context):
        payload = self._llm_payload() if self.available else None
        if payload is None:
            fair_value = self.eps * self.benchmark_pe
            mispricing = (fair_value - self.price) / self.price
            payload = FundamentalPayload(
                asset="AAPL",
                fair_value_estimate=fair_value,
                mispricing_percent=mispricing * 100,
                confidence=1.0,
                rationale="P/E heuristic",
            )
        return FundamentalSignal(
            origin_module=self.name,
            timestamp=datetime.utcnow(),
            payload=payload,
            confidence=payload.confidence,
        )


__all__ = ["FundamentalsAnalyzer"]
