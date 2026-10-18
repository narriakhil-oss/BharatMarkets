"""Technical analysis for chat tools (no DB required)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

from app.providers.base import MarketDataProvider
from app.services.indicator_service import IndicatorService
from app.services.history_service import _company_name
from app.utils.symbol_resolver import resolve_symbol


class AnalysisToolService:
    """Compute indicators + trend from yfinance bars for LLM tools."""

    def __init__(self, provider: MarketDataProvider):
        self.provider = provider

    async def get_analysis(self, symbol_or_name: str) -> Dict[str, Any]:
        resolved = resolve_symbol(symbol_or_name)
        if not resolved:
            raise ValueError(f"Could not resolve stock symbol from '{symbol_or_name}'.")

        bars = await self.provider.get_ohlcv(symbol=resolved, interval="1d", period="1y")
        if not bars:
            raise ValueError(f"Insufficient history to analyze {resolved}.")

        prices: List[Decimal] = [Decimal(str(b["close"])) for b in bars]
        highs: List[Decimal] = [Decimal(str(b["high"])) for b in bars]
        lows: List[Decimal] = [Decimal(str(b["low"])) for b in bars]
        volumes: List[int] = [int(b.get("volume") or 0) for b in bars]
        ltp = prices[-1]

        sma_20 = IndicatorService.calculate_sma(prices, 20)
        sma_50 = IndicatorService.calculate_sma(prices, 50)
        sma_200 = IndicatorService.calculate_sma(prices, 200)
        ema_20 = IndicatorService.calculate_ema(prices, 20)
        rsi_14 = IndicatorService.calculate_rsi(prices, 14)
        macd_line, macd_signal, macd_hist = IndicatorService.calculate_macd(prices)
        bb_u, bb_m, bb_l = IndicatorService.calculate_bollinger_bands(prices)
        atr14 = IndicatorService.calculate_atr(highs, lows, prices, 14)
        high_52w, low_52w = IndicatorService.calculate_52w_high_low(highs, lows)
        levels = IndicatorService.find_support_resistance(highs, lows, prices)

        volume_current = volumes[-1] if volumes else 0
        volume_avg_20d = int(sum(volumes[-20:]) / 20) if len(volumes) >= 20 else (
            int(sum(volumes) / len(volumes)) if volumes else 0
        )

        trend = IndicatorService.analyze_trend(
            ltp=ltp,
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            ema_20=ema_20,
            rsi=rsi_14,
            macd_line=macd_line,
            macd_signal=macd_signal,
            bollinger_upper=bb_u,
            bollinger_lower=bb_l,
            high_52w=high_52w,
            low_52w=low_52w,
            volume=volume_current,
            volume_avg=volume_avg_20d,
        )

        def _d(v: Any) -> Any:
            if isinstance(v, Decimal):
                return str(v)
            return v

        return {
            "symbol": resolved,
            "name": _company_name(resolved),
            "ltp": _d(ltp),
            "indicators": {
                "sma_20": _d(sma_20),
                "sma_50": _d(sma_50),
                "sma_200": _d(sma_200),
                "ema_20": _d(ema_20),
                "rsi_14": _d(rsi_14),
                "macd_line": _d(macd_line),
                "macd_signal": _d(macd_signal),
                "macd_histogram": _d(macd_hist),
                "bollinger_upper": _d(bb_u),
                "bollinger_middle": _d(bb_m),
                "bollinger_lower": _d(bb_l),
                "atr14": _d(atr14),
                "high_52w": _d(high_52w),
                "low_52w": _d(low_52w),
                "support": _d(levels.get("support")),
                "resistance": _d(levels.get("resistance")),
                "volume_current": volume_current,
                "volume_avg_20d": volume_avg_20d or None,
            },
            "trend": {
                "trend": trend.trend,
                "strength": trend.strength,
                "score": trend.score,
                "reasons": trend.reasons,
            },
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }
