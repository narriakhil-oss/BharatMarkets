"""Transparent point-score Buy/Sell/Hold signals for the college project chatbot."""

from __future__ import annotations

from decimal import Decimal
import logging
from typing import List, Optional

from app.providers.base import MarketDataProvider
from app.schemas.chat import (
    BacktestMetrics,
    PriceRange,
    SignalFactor,
    SignalResult,
)
from app.services.forecast_service import ForecastService
from app.services.indicator_service import IndicatorService
from app.utils.symbol_resolver import resolve_symbol

logger = logging.getLogger(__name__)


class SignalService:
    """
    Score factors at +1 / -1 / 0 and map totals to Buy / Sell / Hold.

    Factors:
      1. Price vs SMA50
      2. SMA50 vs SMA200
      3. RSI14 (<35 +1, >70 -1, else 0)
      4. MACD vs signal line
      5. 7-day forecast direction
    """

    def __init__(self, provider: MarketDataProvider, forecast_service: Optional[ForecastService] = None):
        self.provider = provider
        self.forecast_service = forecast_service or ForecastService(provider)

    async def get_signal(self, symbol_or_name: str) -> SignalResult:
        resolved = resolve_symbol(symbol_or_name)
        if not resolved:
            raise ValueError(f"Could not resolve stock symbol from '{symbol_or_name}'.")

        bars = await self.provider.get_ohlcv(symbol=resolved, interval="1d", period="2y")
        if not bars or len(bars) < 30:
            raise ValueError(f"Insufficient history to score a signal for {resolved}.")

        closes: List[Decimal] = [Decimal(str(b["close"])) for b in bars]
        highs: List[Decimal] = [Decimal(str(b["high"])) for b in bars]
        lows: List[Decimal] = [Decimal(str(b["low"])) for b in bars]
        ltp = closes[-1]

        sma50 = IndicatorService.calculate_sma(closes, 50)
        sma200 = IndicatorService.calculate_sma(closes, 200)
        rsi = IndicatorService.calculate_rsi(closes, 14)
        macd_line, macd_signal, _ = IndicatorService.calculate_macd(closes)
        atr14 = IndicatorService.calculate_atr(highs, lows, closes, 14)
        levels = IndicatorService.find_support_resistance(highs, lows, closes)
        support = levels.get("support")
        resistance = levels.get("resistance")

        factors: List[SignalFactor] = []
        score = 0

        # 1. Price vs SMA50
        if sma50 is not None:
            if ltp > sma50:
                factors.append(
                    SignalFactor(name="price_vs_sma50", score=1, detail=f"Price {ltp} above SMA50 {sma50}")
                )
                score += 1
            elif ltp < sma50:
                factors.append(
                    SignalFactor(name="price_vs_sma50", score=-1, detail=f"Price {ltp} below SMA50 {sma50}")
                )
                score -= 1
            else:
                factors.append(
                    SignalFactor(name="price_vs_sma50", score=0, detail=f"Price equal to SMA50 {sma50}")
                )
        else:
            factors.append(
                SignalFactor(name="price_vs_sma50", score=0, detail="SMA50 unavailable")
            )

        # 2. SMA50 vs SMA200
        if sma50 is not None and sma200 is not None:
            if sma50 > sma200:
                factors.append(
                    SignalFactor(
                        name="sma50_vs_sma200",
                        score=1,
                        detail=f"SMA50 {sma50} above SMA200 {sma200} (golden-cross structure)",
                    )
                )
                score += 1
            elif sma50 < sma200:
                factors.append(
                    SignalFactor(
                        name="sma50_vs_sma200",
                        score=-1,
                        detail=f"SMA50 {sma50} below SMA200 {sma200} (death-cross structure)",
                    )
                )
                score -= 1
            else:
                factors.append(
                    SignalFactor(name="sma50_vs_sma200", score=0, detail="SMA50 equals SMA200")
                )
        else:
            factors.append(
                SignalFactor(name="sma50_vs_sma200", score=0, detail="SMA50/SMA200 unavailable")
            )

        # 3. RSI14
        if rsi is not None:
            if rsi < Decimal("35"):
                factors.append(
                    SignalFactor(name="rsi14", score=1, detail=f"RSI14 at {rsi} (<35, oversold bias)")
                )
                score += 1
            elif rsi > Decimal("70"):
                factors.append(
                    SignalFactor(name="rsi14", score=-1, detail=f"RSI14 at {rsi} (>70, overbought bias)")
                )
                score -= 1
            else:
                factors.append(
                    SignalFactor(name="rsi14", score=0, detail=f"RSI14 at {rsi} (neutral 35–70)")
                )
        else:
            factors.append(SignalFactor(name="rsi14", score=0, detail="RSI14 unavailable"))

        # 4. MACD vs signal
        if macd_line is not None and macd_signal is not None:
            if macd_line > macd_signal:
                factors.append(
                    SignalFactor(
                        name="macd_vs_signal",
                        score=1,
                        detail=f"MACD {macd_line} above signal {macd_signal}",
                    )
                )
                score += 1
            elif macd_line < macd_signal:
                factors.append(
                    SignalFactor(
                        name="macd_vs_signal",
                        score=-1,
                        detail=f"MACD {macd_line} below signal {macd_signal}",
                    )
                )
                score -= 1
            else:
                factors.append(
                    SignalFactor(name="macd_vs_signal", score=0, detail="MACD equals signal line")
                )
        else:
            factors.append(
                SignalFactor(name="macd_vs_signal", score=0, detail="MACD unavailable")
            )

        # 5. 7-day forecast direction
        backtest: Optional[BacktestMetrics] = None
        try:
            forecast = await self.forecast_service.get_forecast(resolved, horizon_days=7)
            backtest = forecast.backtest
            if forecast.forecast and forecast.last_close is not None:
                end_pred = forecast.forecast[-1].predicted
                if end_pred > forecast.last_close:
                    factors.append(
                        SignalFactor(
                            name="forecast_7d",
                            score=1,
                            detail=(
                                f"7d forecast {end_pred} above last close {forecast.last_close} "
                                f"({forecast.forecast_change_pct}%)"
                            ),
                        )
                    )
                    score += 1
                elif end_pred < forecast.last_close:
                    factors.append(
                        SignalFactor(
                            name="forecast_7d",
                            score=-1,
                            detail=(
                                f"7d forecast {end_pred} below last close {forecast.last_close} "
                                f"({forecast.forecast_change_pct}%)"
                            ),
                        )
                    )
                    score -= 1
                else:
                    factors.append(
                        SignalFactor(name="forecast_7d", score=0, detail="7d forecast flat vs last close")
                    )
            else:
                factors.append(
                    SignalFactor(
                        name="forecast_7d",
                        score=0,
                        detail=forecast.backtest.note or "Forecast unavailable",
                    )
                )
        except Exception as e:
            logger.warning("Forecast factor failed for %s: %s", resolved, e)
            factors.append(
                SignalFactor(name="forecast_7d", score=0, detail=f"Forecast failed: {e}")
            )

        if score >= 3:
            signal = "Buy"
        elif score <= -3:
            signal = "Sell"
        else:
            signal = "Hold"

        entry_zone, stop_loss = self._zones(ltp, support, resistance, atr14, signal)

        return SignalResult(
            symbol=resolved,
            signal=signal,
            score=score,
            factors=factors,
            entry_zone=entry_zone,
            stop_loss=stop_loss,
            atr14=atr14,
            support=support,
            resistance=resistance,
            backtest=backtest,
            ltp=ltp.quantize(Decimal("0.0001")),
        )

    @staticmethod
    def _zones(
        ltp: Decimal,
        support: Optional[Decimal],
        resistance: Optional[Decimal],
        atr14: Optional[Decimal],
        signal: str,
    ) -> tuple[Optional[PriceRange], Optional[PriceRange]]:
        """Indicative entry and stop-loss ranges from S/R + ATR14."""
        atr = atr14 or (ltp * Decimal("0.02"))
        half = (atr * Decimal("0.5")).quantize(Decimal("0.0001"))

        if signal == "Buy":
            # Entry near support / slightly below market; stop under support
            base = support if support is not None else (ltp - atr)
            entry = PriceRange(
                low=(base - half).quantize(Decimal("0.0001")),
                high=(base + half).quantize(Decimal("0.0001")),
            )
            stop_center = (base - atr).quantize(Decimal("0.0001"))
            stop = PriceRange(
                low=(stop_center - half).quantize(Decimal("0.0001")),
                high=(stop_center + half).quantize(Decimal("0.0001")),
            )
            return entry, stop

        if signal == "Sell":
            base = resistance if resistance is not None else (ltp + atr)
            entry = PriceRange(
                low=(base - half).quantize(Decimal("0.0001")),
                high=(base + half).quantize(Decimal("0.0001")),
            )
            stop_center = (base + atr).quantize(Decimal("0.0001"))
            stop = PriceRange(
                low=(stop_center - half).quantize(Decimal("0.0001")),
                high=(stop_center + half).quantize(Decimal("0.0001")),
            )
            return entry, stop

        # Hold — still show a neutral band around last price
        entry = PriceRange(
            low=(ltp - half).quantize(Decimal("0.0001")),
            high=(ltp + half).quantize(Decimal("0.0001")),
        )
        stop_center = (ltp - atr).quantize(Decimal("0.0001"))
        stop = PriceRange(
            low=(stop_center - half).quantize(Decimal("0.0001")),
            high=(stop_center + half).quantize(Decimal("0.0001")),
        )
        return entry, stop
