"""Forecast tests — walk-forward has no look-ahead leakage."""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from app.services.forecast_service import (
    StatsmodelsEngine,
    walk_forward_backtest,
    MIN_HISTORY_BARS,
)


class RecordingEngine(StatsmodelsEngine):
    """Records the last training index date used for each one-step prediction."""

    def __init__(self):
        self.train_ends = []

    def predict_next(self, series: pd.Series) -> float:
        self.train_ends.append(series.index[-1])
        # Deterministic: predict previous close (no peeking)
        return float(series.iloc[-1])


def _make_series(n: int = 150) -> pd.Series:
    idx = pd.bdate_range("2024-01-01", periods=n)
    rng = np.random.default_rng(42)
    values = 100 + np.cumsum(rng.normal(0, 1, size=n))
    return pd.Series(values, index=idx, name="close")


def test_walk_forward_no_lookahead():
    """Each backtest step must train only on dates strictly before the target day."""
    series = _make_series(120)
    engine = RecordingEngine()
    metrics = walk_forward_backtest(series, engine, window=30)

    assert metrics.samples > 0
    assert len(engine.train_ends) == metrics.samples

    # Reconstruct targets: holdout starts at len - holdout
    holdout = min(30, max(5, len(series) // 3))
    start_idx = len(series) - holdout
    target_dates = []
    for i in range(start_idx, len(series)):
        if i < MIN_HISTORY_BARS:
            continue
        target_dates.append(series.index[i])

    assert len(target_dates) == len(engine.train_ends)
    for train_end, target in zip(engine.train_ends, target_dates):
        assert train_end < target, "Look-ahead leak: train included target date"


def test_walk_forward_short_history():
    series = _make_series(20)
    metrics = walk_forward_backtest(series, StatsmodelsEngine(), window=10)
    assert metrics.samples == 0
    assert metrics.note is not None


def test_statsmodels_fit_predict_shapes():
    series = _make_series(80)
    engine = StatsmodelsEngine()
    pred, lower, upper = engine.fit_predict(series, horizon=7)
    assert len(pred) == 7
    assert len(lower) == 7
    assert len(upper) == 7
    assert np.all(lower <= upper)
