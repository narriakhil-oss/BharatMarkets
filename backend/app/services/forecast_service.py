"""Price forecast service — Prophet when available, else statsmodels ETS/ARIMA."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import logging
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from app.core.redis_client import cache_get, cache_set
from app.providers.base import MarketDataProvider
from app.schemas.chat import (
    BacktestMetrics,
    ForecastPoint,
    ForecastResult,
    PricePoint,
)
from app.utils.symbol_resolver import resolve_symbol

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60 * 60  # 1 hour
MIN_HISTORY_BARS = 40
BACKTEST_WINDOW = 90

_PROPHET_AVAILABLE: Optional[bool] = None


def _try_import_prophet() -> bool:
    global _PROPHET_AVAILABLE
    if _PROPHET_AVAILABLE is not None:
        return _PROPHET_AVAILABLE
    try:
        from prophet import Prophet  # noqa: F401

        _PROPHET_AVAILABLE = True
    except Exception as e:
        logger.info("Prophet unavailable (%s); using statsmodels fallback.", e)
        _PROPHET_AVAILABLE = False
    return _PROPHET_AVAILABLE


def _to_decimal(val: float, places: str = "0.0001") -> Decimal:
    if val != val or val is None:  # NaN
        return Decimal("0.0000")
    return Decimal(f"{float(val):.4f}").quantize(Decimal(places))


def _bars_to_series(bars: Sequence[dict]) -> pd.Series:
    dates = []
    closes = []
    for b in bars:
        if b.get("close") is None or b.get("date") is None:
            continue
        dates.append(pd.Timestamp(str(b["date"])[:10]))
        closes.append(float(b["close"]))
    if not closes:
        return pd.Series(dtype=float)
    s = pd.Series(closes, index=pd.DatetimeIndex(dates), name="close")
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s


class ForecastEngine:
    """Shared interface for Prophet and statsmodels backends."""

    name: str = "base"

    def fit_predict(
        self,
        series: pd.Series,
        horizon: int,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (predicted, lower, upper) arrays of length horizon."""
        raise NotImplementedError

    def predict_next(self, series: pd.Series) -> float:
        """One-step-ahead point forecast (for walk-forward backtest)."""
        preds, _, _ = self.fit_predict(series, horizon=1)
        return float(preds[0])


class ProphetEngine(ForecastEngine):
    name = "prophet"

    def fit_predict(
        self,
        series: pd.Series,
        horizon: int,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        from prophet import Prophet

        df = pd.DataFrame({"ds": series.index, "y": series.values})
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=len(series) >= 200,
            interval_width=0.8,
        )
        model.fit(df)
        future = model.make_future_dataframe(periods=horizon, freq="B")
        forecast = model.predict(future)
        tail = forecast.tail(horizon)
        return (
            tail["yhat"].to_numpy(dtype=float),
            tail["yhat_lower"].to_numpy(dtype=float),
            tail["yhat_upper"].to_numpy(dtype=float),
        )


class StatsmodelsEngine(ForecastEngine):
    """ETS (Holt-Winters) with ARIMA fallback."""

    name = "statsmodels_ets"

    def fit_predict(
        self,
        series: pd.Series,
        horizon: int,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        values = series.astype(float).values
        resid_std = self._residual_std(values)

        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing

            # Prefer additive trend; skip seasonal if history is short
            seasonal = "add" if len(values) >= 60 else None
            seasonal_periods = 5 if seasonal else None
            model = ExponentialSmoothing(
                values,
                trend="add",
                seasonal=seasonal,
                seasonal_periods=seasonal_periods,
                initialization_method="estimated",
            )
            fitted = model.fit(optimized=True)
            pred = np.asarray(fitted.forecast(horizon), dtype=float)
            self.name = "statsmodels_ets"
        except Exception as e:
            logger.debug("ETS failed (%s); trying ARIMA.", e)
            pred = self._arima_forecast(values, horizon)
            self.name = "statsmodels_arima"

        z = 1.2816  # ~80% interval
        # Widen band with horizon (random-walk style)
        steps = np.arange(1, horizon + 1, dtype=float)
        band = z * resid_std * np.sqrt(steps)
        lower = pred - band
        upper = pred + band
        return pred, lower, upper

    def _arima_forecast(self, values: np.ndarray, horizon: int) -> np.ndarray:
        from statsmodels.tsa.arima.model import ARIMA

        try:
            model = ARIMA(values, order=(1, 1, 1))
            fitted = model.fit()
            return np.asarray(fitted.forecast(horizon), dtype=float)
        except Exception:
            # Naive drift fallback
            if len(values) < 2:
                return np.full(horizon, values[-1] if len(values) else 0.0)
            drift = (values[-1] - values[0]) / max(len(values) - 1, 1)
            return np.array([values[-1] + drift * (i + 1) for i in range(horizon)], dtype=float)

    @staticmethod
    def _residual_std(values: np.ndarray) -> float:
        if len(values) < 3:
            return max(abs(float(values[-1])) * 0.01, 1.0) if len(values) else 1.0
        diffs = np.diff(values)
        std = float(np.std(diffs))
        return max(std, abs(float(values[-1])) * 0.002, 0.01)


def _select_engine() -> ForecastEngine:
    if _try_import_prophet():
        return ProphetEngine()
    return StatsmodelsEngine()


def _business_days_ahead(start: pd.Timestamp, n: int) -> List[str]:
    dates = pd.bdate_range(start=start + pd.Timedelta(days=1), periods=n)
    return [d.strftime("%Y-%m-%d") for d in dates]


def walk_forward_backtest(
    series: pd.Series,
    engine: ForecastEngine,
    window: int = BACKTEST_WINDOW,
) -> BacktestMetrics:
    """
    Walk-forward one-step backtest over the last `window` days.

    For each day t in the holdout, train ONLY on data strictly before t,
    predict the close at t, then score — no look-ahead leakage.
    """
    if len(series) < MIN_HISTORY_BARS + 5:
        return BacktestMetrics(
            mape_pct=None,
            directional_accuracy_pct=None,
            samples=0,
            method=engine.name,
            note="Insufficient history for backtest",
        )

    holdout = min(window, max(5, len(series) // 3))
    start_idx = len(series) - holdout
    abs_pct_errors: List[float] = []
    direction_hits = 0
    direction_total = 0

    for i in range(start_idx, len(series)):
        train = series.iloc[:i]
        if len(train) < MIN_HISTORY_BARS:
            continue
        actual = float(series.iloc[i])
        prev = float(series.iloc[i - 1])
        try:
            predicted = engine.predict_next(train)
        except Exception as e:
            logger.debug("Backtest step failed at %s: %s", series.index[i], e)
            continue

        if actual != 0:
            abs_pct_errors.append(abs(predicted - actual) / abs(actual) * 100.0)

        # Directional accuracy: did we correctly predict up/down vs previous close?
        pred_dir = predicted - prev
        actual_dir = actual - prev
        if pred_dir == 0 and actual_dir == 0:
            direction_hits += 1
            direction_total += 1
        elif pred_dir * actual_dir > 0:
            direction_hits += 1
            direction_total += 1
        elif pred_dir != 0 or actual_dir != 0:
            direction_total += 1

    samples = len(abs_pct_errors)
    mape = _to_decimal(float(np.mean(abs_pct_errors))) if samples else None
    dir_acc = (
        _to_decimal(100.0 * direction_hits / direction_total)
        if direction_total
        else None
    )
    return BacktestMetrics(
        mape_pct=mape,
        directional_accuracy_pct=dir_acc,
        samples=samples,
        method=engine.name,
        note=None if samples else "Backtest produced no samples",
    )


class ForecastService:
    """Forecast daily closes with caching and short-history handling."""

    def __init__(self, provider: MarketDataProvider):
        self.provider = provider

    async def get_forecast(
        self,
        symbol_or_name: str,
        horizon_days: int = 7,
    ) -> ForecastResult:
        if horizon_days not in (7, 30):
            raise ValueError("horizon_days must be 7 or 30")

        resolved = resolve_symbol(symbol_or_name)
        if not resolved:
            raise ValueError(f"Could not resolve stock symbol from '{symbol_or_name}'.")

        cache_key = f"forecast:{resolved}:{horizon_days}"
        cached = await cache_get(cache_key)
        if cached:
            return ForecastResult(**cached)

        # Need enough history for SMA200-style context + backtest
        bars = await self.provider.get_ohlcv(symbol=resolved, interval="1d", period="2y")
        series = _bars_to_series(bars)
        if len(series) < MIN_HISTORY_BARS:
            return ForecastResult(
                symbol=resolved,
                horizon_days=horizon_days,
                method="none",
                history_tail=[],
                forecast=[],
                backtest=BacktestMetrics(
                    samples=0,
                    method="none",
                    note=f"Need at least {MIN_HISTORY_BARS} daily bars; got {len(series)}",
                ),
                last_close=_to_decimal(float(series.iloc[-1])) if len(series) else None,
                forecast_change_pct=None,
            )

        engine = _select_engine()
        # Walk-forward uses a fast statsmodels engine to avoid 90× Prophet refits;
        # still trains only on past data (no look-ahead). Metrics method notes this.
        backtest_engine = StatsmodelsEngine()
        backtest = walk_forward_backtest(series, backtest_engine)
        if engine.name == "prophet":
            backtest = backtest.model_copy(
                update={
                    "method": f"{engine.name}+backtest:{backtest.method}",
                    "note": (backtest.note or "")
                    + (" " if backtest.note else "")
                    + "Walk-forward metrics from statsmodels (same no-leakage protocol).",
                }
            )

        try:
            pred, lower, upper = engine.fit_predict(series, horizon_days)
        except Exception as e:
            logger.warning("Primary engine %s failed (%s); forcing statsmodels.", engine.name, e)
            engine = StatsmodelsEngine()
            pred, lower, upper = engine.fit_predict(series, horizon_days)
            backtest = walk_forward_backtest(series, engine)

        # Ensure bands are ordered
        lower = np.minimum(lower, pred)
        upper = np.maximum(upper, pred)

        dates = _business_days_ahead(series.index[-1], horizon_days)
        forecast_points = [
            ForecastPoint(
                date=dates[i],
                predicted=_to_decimal(float(pred[i])),
                lower=_to_decimal(float(lower[i])),
                upper=_to_decimal(float(upper[i])),
            )
            for i in range(horizon_days)
        ]

        tail_n = min(60, len(series))
        history_tail = [
            PricePoint(date=idx.strftime("%Y-%m-%d"), close=_to_decimal(float(val)))
            for idx, val in series.iloc[-tail_n:].items()
        ]

        last_close = _to_decimal(float(series.iloc[-1]))
        end_pred = forecast_points[-1].predicted if forecast_points else last_close
        change_pct = (
            ((end_pred - last_close) / last_close) * Decimal("100")
            if last_close != 0
            else Decimal("0")
        )

        result = ForecastResult(
            symbol=resolved,
            horizon_days=horizon_days,
            method=engine.name,
            history_tail=history_tail,
            forecast=forecast_points,
            backtest=backtest,
            last_close=last_close,
            forecast_change_pct=change_pct.quantize(Decimal("0.0001")),
        )
        await cache_set(cache_key, result.model_dump(mode="json"), ttl=CACHE_TTL_SECONDS)
        return result
