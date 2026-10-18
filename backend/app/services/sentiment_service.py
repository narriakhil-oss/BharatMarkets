"""
Sentiment analysis hook (FinBERT / news sentiment) — intentionally stubbed.

Skipped for the current college-project phase. Keep this module so a future
implementation can plug into SignalService / chat tools without reshaping APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SentimentResult:
    """Placeholder sentiment payload."""

    symbol: str
    score: Optional[float] = None  # -1 bearish … +1 bullish
    label: str = "unavailable"
    summary: str = "Sentiment analysis is not enabled yet."
    source: str = "none"


class SentimentService:
    """No-op sentiment provider. Replace with FinBERT/news later."""

    enabled: bool = False

    async def get_sentiment(self, symbol: str) -> SentimentResult:
        """Return an unavailable stub so callers can keep a stable interface."""
        return SentimentResult(symbol=symbol)

    async def is_available(self) -> bool:
        return self.enabled
