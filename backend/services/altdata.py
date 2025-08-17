"""Alt-data analysis module leveraging lightweight LLM reasoning."""
from __future__ import annotations

import json
import os
from datetime import datetime

from backend.schemas import AltDataPayload, AltDataSignal
from backend.observability import track


class AltDataAnalyzer:
    """Produce alternative data signals using an LLM when available."""

    name = "altdata"

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

    def _llm_payload(self, asset: str) -> AltDataPayload | None:
        """Return an alt-data payload using the LLM, if possible."""
        prompt = (
            "You are an alternative data analyst. Provide JSON with keys 'metric',"
            " 'value', and 'confidence' (0-1) for recent web traffic changes for"
            f" {asset}."
        )
        try:  # pragma: no cover - network
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp["choices"][0]["message"]["content"].strip()
            data = json.loads(content)
            return AltDataPayload(
                asset=asset,
                metric=data.get("metric", "web_traffic"),
                value=float(data.get("value", 0.0)),
                confidence=float(data.get("confidence", 0.5)),
            )
        except Exception:
            return None

    @track("altdata_generate")
    def generate(self, context):
        asset = "AAPL"
        payload = self._llm_payload(asset) if self.available else None
        if payload is None:
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
