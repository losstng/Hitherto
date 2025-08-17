"""Sentiment analysis module leveraging an LLM when available."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

from backend.database import SessionLocal
from backend.models import Newsletter, Signal
from backend.schemas import SentimentPayload, SentimentSignal
from backend.observability import track

POSITIVE_WORDS = {
    "good",
    "great",
    "positive",
    "up",
    "gain",
    "growth",
    "strong",
    "beat",
    "profit",
}

NEGATIVE_WORDS = {
    "bad",
    "poor",
    "negative",
    "down",
    "loss",
    "weak",
    "miss",
    "risk",
}


class SentimentAnalyzer:
    """Generate sentiment signals from unstructured text.

    The analyzer relies on an LLM (OpenAI) if an API key is configured; otherwise
    it falls back to a simple lexical rule-based scorer. Generated signals are
    persisted to the ``signals`` table for auditability.
    """

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
        """Return True when the OpenAI client is configured."""
        return self._client is not None

    # ------------------------------------------------------------------
    # scoring helpers
    def _rule_based(self, text: str) -> Tuple[float, str]:
        words = re.findall(r"\w+", text.lower())
        pos = sum(w in POSITIVE_WORDS for w in words)
        neg = sum(w in NEGATIVE_WORDS for w in words)
        score = (pos - neg) / max(pos + neg, 1)
        summary = text[:140].strip()
        return score, summary or "summary unavailable"

    def _llm_score(self, asset: str, text: str) -> Tuple[float, str]:
        prompt = (
            "You are a financial news analyst. Given the following news text about"
            f" {asset}, respond with JSON containing 'score' (-1 to 1) and 'summary'.\n"
            f"Text: {text}"
        )
        try:  # pragma: no cover - network
            resp = self._client.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp["choices"][0]["message"]["content"].strip()
            data = json.loads(content)
            return float(data.get("score", 0.0)), data.get("summary", "")
        except Exception:
            return self._rule_based(text)

    # ------------------------------------------------------------------
    def score_text(self, asset: str, text: str) -> SentimentSignal:
        """Return a ``SentimentSignal`` for a single asset/text pair."""
        if self.available:
            score, summary = self._llm_score(asset, text)
        else:
            score, summary = self._rule_based(text)

        payload = SentimentPayload(
            asset=asset,
            sentiment_score=score,
            summary=summary,
            confidence=abs(score),
        )
        return SentimentSignal(
            origin_module="sentiment",
            timestamp=datetime.utcnow(),
            payload=payload,
        )

    # ------------------------------------------------------------------
    @track("sentiment_generate")
    def generate_from_newsletters(self, session: SessionLocal) -> List[SentimentSignal]:
        """Analyze all newsletters and persist resulting signals.

        Parameters
        ----------
        session:
            SQLAlchemy session used to query ``Newsletter`` items and log signals.
        """
        signals: List[SentimentSignal] = []
        newsletters: Iterable[Newsletter] = session.query(Newsletter).filter(
            Newsletter.extracted_text.isnot(None)
        )
        for item in newsletters:
            asset = item.category or "UNKNOWN"
            signal = self.score_text(asset, item.extracted_text or "")
            db_entry = Signal(
                module_name="Sentiment",
                signal_type="SentimentSignal",
                content_json=json.loads(signal.model_dump_json()),
                generated_at=signal.timestamp,
            )
            session.add(db_entry)
            signals.append(signal)
        session.commit()
        return signals


__all__ = ["SentimentAnalyzer"]
