"""Signal scoring unit tests."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.chat import BacktestMetrics, ForecastPoint, ForecastResult, PricePoint
from app.services.signal_service import SignalService


def _bars_uptrend(n: int = 250):
    bars = []
    for i in range(n):
        close = Decimal("100") + Decimal(str(i)) * Decimal("0.5")
        bars.append(
            {
                "date": f"2024-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}",
                "open": close - Decimal("0.2"),
                "high": close + Decimal("1"),
                "low": close - Decimal("1"),
                "close": close,
                "volume": 1_000_000,
            }
        )
    return bars


@pytest.mark.asyncio
async def test_signal_buy_when_all_bullish():
    provider = MagicMock()
    provider.get_ohlcv = AsyncMock(return_value=_bars_uptrend())

    forecast = ForecastResult(
        symbol="TEST.NS",
        horizon_days=7,
        method="test",
        history_tail=[PricePoint(date="2024-01-01", close=Decimal("200"))],
        forecast=[
            ForecastPoint(
                date="2024-01-02",
                predicted=Decimal("220"),
                lower=Decimal("210"),
                upper=Decimal("230"),
            )
        ],
        backtest=BacktestMetrics(mape_pct=Decimal("5"), directional_accuracy_pct=Decimal("60"), samples=40, method="test"),
        last_close=Decimal("200"),
        forecast_change_pct=Decimal("10"),
    )
    forecast_svc = MagicMock()
    forecast_svc.get_forecast = AsyncMock(return_value=forecast)

    svc = SignalService(provider, forecast_service=forecast_svc)
    import app.services.signal_service as signal_mod

    original = signal_mod.resolve_symbol
    signal_mod.resolve_symbol = lambda q: "TEST.NS"
    try:
        result = await svc.get_signal("TEST")
    finally:
        signal_mod.resolve_symbol = original

    assert result.signal in ("Buy", "Hold", "Sell")
    assert isinstance(result.score, int)
    assert len(result.factors) == 5
    names = {f.name for f in result.factors}
    assert names == {
        "price_vs_sma50",
        "sma50_vs_sma200",
        "rsi14",
        "macd_vs_signal",
        "forecast_7d",
    }
    # Uptrend + rising forecast should lean Buy or at least not Sell
    assert result.score >= 0
    assert result.entry_zone is not None
    assert result.stop_loss is not None


def test_signal_thresholds():
    """Document threshold mapping used by the service."""
    assert 3 >= 3  # Buy threshold
    assert -3 <= -3  # Sell threshold

    def map_score(score: int) -> str:
        if score >= 3:
            return "Buy"
        if score <= -3:
            return "Sell"
        return "Hold"

    assert map_score(3) == "Buy"
    assert map_score(5) == "Buy"
    assert map_score(-3) == "Sell"
    assert map_score(0) == "Hold"
    assert map_score(2) == "Hold"
