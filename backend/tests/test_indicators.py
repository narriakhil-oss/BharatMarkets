"""Unit tests for IndicatorService technical indicator calculations."""

from decimal import Decimal
import pytest

from app.services.indicator_service import IndicatorService


def test_sma_with_known_values():
    """Test Simple Moving Average calculation against known expected values."""
    prices = [Decimal(str(x)) for x in [10, 20, 30, 40, 50]]

    # Period 3 of [10, 20, 30, 40, 50] is (30 + 40 + 50) / 3 = 40.0000
    sma_3 = IndicatorService.calculate_sma(prices, period=3)
    assert sma_3 is not None
    assert sma_3 == Decimal("40.0000")

    # Period 5 of [10, 20, 30, 40, 50] is (10 + 20 + 30 + 40 + 50) / 5 = 30.0000
    sma_5 = IndicatorService.calculate_sma(prices, period=5)
    assert sma_5 is not None
    assert sma_5 == Decimal("30.0000")

    # Insufficient elements returns None
    assert IndicatorService.calculate_sma(prices, period=10) is None


def test_ema_calculation():
    """Test Exponential Moving Average calculation."""
    prices = [Decimal(str(x)) for x in [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]]
    ema = IndicatorService.calculate_ema(prices, period=5)
    assert ema is not None
    assert isinstance(ema, Decimal)
    # EMA in an uptrend should track near latest prices
    assert Decimal("16") < ema < Decimal("21")


def test_rsi_boundaries():
    """Test Relative Strength Index (RSI) stays strictly within [0, 100] and detects extremes."""
    # Monotonically increasing prices -> RSI should be very high (> 80)
    uptrend_prices = [Decimal(str(100 + i * 5)) for i in range(30)]
    rsi_up = IndicatorService.calculate_rsi(uptrend_prices, period=14)
    assert rsi_up is not None
    assert Decimal("0") <= rsi_up <= Decimal("100")
    assert rsi_up > Decimal("80")

    # Monotonically falling prices -> RSI should be very low (< 20)
    downtrend_prices = [Decimal(str(200 - i * 5)) for i in range(30)]
    rsi_down = IndicatorService.calculate_rsi(downtrend_prices, period=14)
    assert rsi_down is not None
    assert Decimal("0") <= rsi_down <= Decimal("100")
    assert rsi_down < Decimal("20")

    # Insufficient history returns None
    assert IndicatorService.calculate_rsi([Decimal("100"), Decimal("101")], period=14) is None


def test_macd_components():
    """Test MACD line, signal line, and histogram relations."""
    # Generate 50 realistic price steps
    base = Decimal("100")
    prices = [base + Decimal(str(i * 1.5)) for i in range(50)]

    macd_line, signal_line, histogram = IndicatorService.calculate_macd(
        prices, fast=12, slow=26, signal=9
    )

    assert macd_line is not None
    assert signal_line is not None
    assert histogram is not None

    # Relationship check: Histogram = MACD Line - Signal Line (within rounding tolerance)
    computed_diff = (macd_line - signal_line).quantize(Decimal("0.0001"))
    assert abs(histogram - computed_diff) <= Decimal("0.0001")


def test_bollinger_bands_width_and_order():
    """Test Bollinger Bands order: Upper > Middle > Lower and middle matches SMA."""
    prices = [Decimal(str(100 + (i % 7) * 2)) for i in range(30)]

    upper, middle, lower = IndicatorService.calculate_bollinger_bands(
        prices, period=20, std_dev=2
    )

    assert upper is not None
    assert middle is not None
    assert lower is not None

    # Structural hierarchy: upper > middle > lower
    assert upper > middle
    assert middle > lower

    # Middle band must equal 20-period SMA
    expected_sma = IndicatorService.calculate_sma(prices, period=20)
    assert middle == expected_sma

    # Width between upper and lower should be greater than zero
    band_width = upper - lower
    assert band_width > Decimal("0")


def test_atr14_positive_and_scales_with_volatility():
    """ATR14 should be positive and larger when ranges widen."""
    closes = [Decimal(str(100 + i)) for i in range(40)]
    highs = [c + Decimal("1") for c in closes]
    lows = [c - Decimal("1") for c in closes]
    atr_tight = IndicatorService.calculate_atr(highs, lows, closes, period=14)
    assert atr_tight is not None
    assert atr_tight > Decimal("0")

    highs_wide = [c + Decimal("5") for c in closes]
    lows_wide = [c - Decimal("5") for c in closes]
    atr_wide = IndicatorService.calculate_atr(highs_wide, lows_wide, closes, period=14)
    assert atr_wide is not None
    assert atr_wide > atr_tight

    assert IndicatorService.calculate_atr(highs[:10], lows[:10], closes[:10], 14) is None


def test_52w_high_low():
    """52-week high/low should match max high / min low in the window."""
    highs = [Decimal(str(100 + i)) for i in range(30)]
    lows = [Decimal(str(90 + i)) for i in range(30)]
    high_52w, low_52w = IndicatorService.calculate_52w_high_low(highs, lows, lookback=252)
    assert high_52w == Decimal("129.0000")
    assert low_52w == Decimal("90.0000")


def test_support_resistance_swings():
    """Support should sit below latest close; resistance above when swings exist."""
    # Synthetic V shape then rise — creates a clear swing low
    lows = [Decimal(str(x)) for x in [20, 18, 15, 14, 13, 14, 16, 18, 19, 20, 21, 22]]
    highs = [Decimal(str(x)) for x in [22, 20, 17, 16, 15, 17, 19, 21, 22, 23, 24, 25]]
    closes = [Decimal(str(x)) for x in [21, 19, 16, 15, 14, 16, 18, 20, 21, 22, 23, 24]]
    levels = IndicatorService.find_support_resistance(
        highs, lows, closes, lookback=60, swing_order=1, max_levels=3
    )
    assert levels["support"] is not None or levels["support_levels"]
    if levels["support"] is not None and levels["resistance"] is not None:
        assert levels["support"] <= closes[-1] or levels["resistance"] >= closes[-1]


def test_trend_analysis_scoring():
    """Test trend analysis evaluation logic under bullish and bearish conditions."""
    # Bullish scenario
    bullish_analysis = IndicatorService.analyze_trend(
        ltp=Decimal("2500"),
        sma_20=Decimal("2400"),
        sma_50=Decimal("2300"),
        sma_200=Decimal("2100"),
        ema_20=Decimal("2420"),
        rsi=Decimal("62"),
        macd_line=Decimal("25"),
        macd_signal=Decimal("15"),
        bollinger_upper=Decimal("2600"),
        bollinger_lower=Decimal("2200"),
        high_52w=Decimal("2550"),
        low_52w=Decimal("1900"),
        volume=1500000,
        volume_avg=1000000,
    )

    assert bullish_analysis.trend == "Bullish"
    assert bullish_analysis.strength in ("Moderate", "Strong")
    assert len(bullish_analysis.reasons) > 0

    # Bearish scenario
    bearish_analysis = IndicatorService.analyze_trend(
        ltp=Decimal("1900"),
        sma_20=Decimal("2100"),
        sma_50=Decimal("2200"),
        sma_200=Decimal("2400"),
        ema_20=Decimal("2080"),
        rsi=Decimal("25"),
        macd_line=Decimal("-30"),
        macd_signal=Decimal("-10"),
        bollinger_upper=Decimal("2300"),
        bollinger_lower=Decimal("1950"),
        high_52w=Decimal("2600"),
        low_52w=Decimal("1880"),
        volume=2000000,
        volume_avg=1000000,
    )

    assert bearish_analysis.trend in ("Bearish", "Sideways")
    assert len(bearish_analysis.reasons) > 0
