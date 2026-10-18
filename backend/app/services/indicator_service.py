"""Pure-math technical indicators and trend analysis service."""

from decimal import Decimal
import math
from typing import List, Optional, Tuple

from app.schemas.analysis import TrendAnalysis


class IndicatorService:
    """Calculates technical indicators and generates rule-based market analysis."""

    @staticmethod
    def calculate_sma(prices: List[Decimal], period: int) -> Optional[Decimal]:
        """
        Calculate Simple Moving Average (SMA).

        Args:
            prices: Historical closing price series (chronological, oldest to newest).
            period: Window length in bars.

        Returns:
            Optional[Decimal]: Calculated SMA or None if insufficient history.
        """
        if not prices or len(prices) < period or period <= 0:
            return None

        window = prices[-period:]
        sma = sum(window) / Decimal(str(period))
        return sma.quantize(Decimal("0.0001"))

    @staticmethod
    def calculate_ema(prices: List[Decimal], period: int) -> Optional[Decimal]:
        """
        Calculate Exponential Moving Average (EMA).

        Args:
            prices: Chronological closing price series.
            period: Window length.

        Returns:
            Optional[Decimal]: Calculated EMA or None.
        """
        if not prices or len(prices) < period or period <= 0:
            return None

        k = Decimal("2") / Decimal(str(period + 1))
        # Initial EMA is the SMA of the initial period
        current_ema = sum(prices[:period]) / Decimal(str(period))

        for price in prices[period:]:
            current_ema = (price * k) + (current_ema * (Decimal("1") - k))

        return current_ema.quantize(Decimal("0.0001"))

    @staticmethod
    def calculate_rsi(prices: List[Decimal], period: int = 14) -> Optional[Decimal]:
        """
        Calculate Wilder's Relative Strength Index (RSI).

        Args:
            prices: Chronological closing price series.
            period: Lookback window (default 14).

        Returns:
            Optional[Decimal]: RSI value between 0 and 100, or None.
        """
        if not prices or len(prices) <= period or period <= 0:
            return None

        changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        gains = [max(c, Decimal("0")) for c in changes]
        losses = [max(-c, Decimal("0")) for c in changes]

        # Initial averages
        avg_gain = sum(gains[:period]) / Decimal(str(period))
        avg_loss = sum(losses[:period]) / Decimal(str(period))

        p_dec = Decimal(str(period))
        p_minus_1 = Decimal(str(period - 1))

        # Smoothed Wilder's rolling calculation
        for i in range(period, len(changes)):
            avg_gain = ((avg_gain * p_minus_1) + gains[i]) / p_dec
            avg_loss = ((avg_loss * p_minus_1) + losses[i]) / p_dec

        if avg_loss == Decimal("0"):
            return Decimal("100.0000")
        if avg_gain == Decimal("0"):
            return Decimal("0.0000")

        rs = avg_gain / avg_loss
        rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
        return rsi.quantize(Decimal("0.0001"))

    @staticmethod
    def calculate_macd(
        prices: List[Decimal],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """
        Calculate Moving Average Convergence Divergence (MACD).

        Args:
            prices: Chronological closing price series.
            fast: Short EMA period (default 12).
            slow: Long EMA period (default 26).
            signal: Signal line EMA period (default 9).

        Returns:
            Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
                (macd_line, signal_line, histogram)
        """
        if not prices or len(prices) < slow + signal or slow <= fast:
            return None, None, None

        k_fast = Decimal("2") / Decimal(str(fast + 1))
        k_slow = Decimal("2") / Decimal(str(slow + 1))

        # Initial fast and slow EMAs
        fast_ema = sum(prices[:fast]) / Decimal(str(fast))
        # Warm up fast EMA until slow window start
        for p in prices[fast:slow]:
            fast_ema = (p * k_fast) + (fast_ema * (Decimal("1") - k_fast))

        slow_ema = sum(prices[:slow]) / Decimal(str(slow))

        macd_series: List[Decimal] = []
        first_macd = fast_ema - slow_ema
        macd_series.append(first_macd)

        # Step through remainder of prices to build MACD series
        for p in prices[slow:]:
            fast_ema = (p * k_fast) + (fast_ema * (Decimal("1") - k_fast))
            slow_ema = (p * k_slow) + (slow_ema * (Decimal("1") - k_slow))
            macd_series.append(fast_ema - slow_ema)

        if len(macd_series) < signal:
            return None, None, None

        # Signal line is EMA of macd_series
        k_sig = Decimal("2") / Decimal(str(signal + 1))
        sig_ema = sum(macd_series[:signal]) / Decimal(str(signal))
        for m in macd_series[signal:]:
            sig_ema = (m * k_sig) + (sig_ema * (Decimal("1") - k_sig))

        latest_macd = macd_series[-1]
        histogram = latest_macd - sig_ema

        return (
            latest_macd.quantize(Decimal("0.0001")),
            sig_ema.quantize(Decimal("0.0001")),
            histogram.quantize(Decimal("0.0001")),
        )

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[Decimal],
        period: int = 20,
        std_dev: int = 2,
    ) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """
        Calculate Bollinger Bands (Upper, Middle, Lower).

        Args:
            prices: Chronological closing price series.
            period: Lookback period for SMA and volatility (default 20).
            std_dev: Number of standard deviations (default 2).

        Returns:
            Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
                (upper_band, middle_band, lower_band)
        """
        if not prices or len(prices) < period or period <= 0:
            return None, None, None

        window = prices[-period:]
        period_dec = Decimal(str(period))
        middle = sum(window) / period_dec

        variance = sum((p - middle) ** 2 for p in window) / period_dec
        std = Decimal(str(math.sqrt(float(variance))))

        upper = middle + (Decimal(str(std_dev)) * std)
        lower = middle - (Decimal(str(std_dev)) * std)

        return (
            upper.quantize(Decimal("0.0001")),
            middle.quantize(Decimal("0.0001")),
            lower.quantize(Decimal("0.0001")),
        )

    @staticmethod
    def analyze_trend(
        ltp: Decimal,
        sma_20: Optional[Decimal],
        sma_50: Optional[Decimal],
        sma_200: Optional[Decimal],
        ema_20: Optional[Decimal],
        rsi: Optional[Decimal],
        macd_line: Optional[Decimal],
        macd_signal: Optional[Decimal],
        bollinger_upper: Optional[Decimal],
        bollinger_lower: Optional[Decimal],
        high_52w: Optional[Decimal],
        low_52w: Optional[Decimal],
        volume: Optional[int],
        volume_avg: Optional[int],
    ) -> TrendAnalysis:
        """
        Evaluate technical signals and synthesize overall trend with human-readable rationales.

        Returns:
            TrendAnalysis: Pydantic model with trend, strength, score, and reasons.
        """
        score = 0
        reasons: List[str] = []

        # 1. 200-day SMA (Long-term trend)
        if sma_200 is not None:
            if ltp > sma_200:
                score += 1
                reasons.append("Price above 200-day SMA — long-term uptrend")
            elif ltp < sma_200:
                score -= 1
                reasons.append("Price below 200-day SMA — long-term downtrend")

        # 2. Golden Cross / Death Cross structure (50 SMA vs 200 SMA)
        if sma_50 is not None and sma_200 is not None:
            if sma_50 > sma_200:
                score += 1
                reasons.append("50-day SMA above 200-day SMA — Golden Cross structure")
            elif sma_50 < sma_200:
                score -= 1
                reasons.append("50-day SMA below 200-day SMA — Death Cross structure")

        # 3. 20-day SMA (Short-term momentum)
        if sma_20 is not None:
            if ltp > sma_20:
                score += 1
                reasons.append("Price above 20-day SMA — short-term bullish momentum")
            elif ltp < sma_20:
                score -= 1
                reasons.append("Price below 20-day SMA — short-term bearish momentum")

        # 4. 20-day EMA
        if ema_20 is not None:
            if ltp > ema_20:
                score += 1
                reasons.append("Price trading above 20-day EMA — positive short-term trend")
            elif ltp < ema_20:
                score -= 1
                reasons.append("Price trading below 20-day EMA — negative short-term trend")

        # 5. RSI (14)
        if rsi is not None:
            rsi_rounded = round(float(rsi), 1)
            if rsi >= Decimal("70"):
                score -= 1
                reasons.append(f"RSI at {rsi_rounded} — approaching overbought territory")
            elif rsi <= Decimal("30"):
                score += 1
                reasons.append(f"RSI at {rsi_rounded} — approaching oversold territory / potential bounce")
            elif rsi > Decimal("50"):
                score += 1
                reasons.append(f"RSI at {rsi_rounded} — positive bullish momentum")
            else:
                score -= 1
                reasons.append(f"RSI at {rsi_rounded} — negative bearish momentum")

        # 6. MACD vs Signal Line
        if macd_line is not None and macd_signal is not None:
            if macd_line > macd_signal:
                score += 1
                reasons.append("MACD crossed above signal line — bullish momentum")
            elif macd_line < macd_signal:
                score -= 1
                reasons.append("MACD below signal line — bearish momentum")

        # 7. Bollinger Bands Proximity
        if bollinger_upper is not None and ltp >= bollinger_upper * Decimal("0.98"):
            score -= 1
            reasons.append("Price near upper Bollinger Band — may face resistance")
        elif bollinger_lower is not None and ltp <= bollinger_lower * Decimal("1.02"):
            score += 1
            reasons.append("Price near lower Bollinger Band — potential support level")

        # 8. Volume Participation
        if volume and volume_avg and volume_avg > 0:
            vol_ratio = Decimal(str(volume)) / Decimal(str(volume_avg))
            if vol_ratio >= Decimal("1.5"):
                pct_above = round(float(vol_ratio - Decimal("1")) * 100)
                reasons.append(f"Volume {pct_above}% above 20-day average — strong institutional participation")
                if ltp > (sma_20 or ltp):
                    score += 1
                else:
                    score -= 1

        # 9. 52-Week High/Low Levels
        if high_52w is not None and ltp >= high_52w * Decimal("0.95"):
            reasons.append("Price within 5% of 52-week high — near historical resistance")
        if low_52w is not None and ltp <= low_52w * Decimal("1.05"):
            reasons.append("Price within 5% of 52-week low — near historical support")

        # Synthesize Trend and Conviction Strength
        if score >= 3:
            trend = "Bullish"
        elif score <= -3:
            trend = "Bearish"
        else:
            trend = "Sideways"

        abs_score = abs(score)
        if abs_score >= 5:
            strength = "Strong"
        elif abs_score >= 2:
            strength = "Moderate"
        else:
            strength = "Weak"

        return TrendAnalysis(
            trend=trend,
            strength=strength,
            score=score,
            reasons=reasons,
        )

    @staticmethod
    def calculate_atr(
        highs: List[Decimal],
        lows: List[Decimal],
        closes: List[Decimal],
        period: int = 14,
    ) -> Optional[Decimal]:
        """
        Calculate Average True Range (ATR) using Wilder's smoothing.

        True Range = max(high-low, |high-prev_close|, |low-prev_close|).
        """
        n = len(closes)
        if (
            not highs
            or not lows
            or not closes
            or len(highs) != n
            or len(lows) != n
            or n <= period
            or period <= 0
        ):
            return None

        true_ranges: List[Decimal] = [highs[0] - lows[0]]
        for i in range(1, n):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            true_ranges.append(tr)

        period_dec = Decimal(str(period))
        atr = sum(true_ranges[1 : period + 1]) / period_dec
        p_minus_1 = Decimal(str(period - 1))
        for i in range(period + 1, n):
            atr = ((atr * p_minus_1) + true_ranges[i]) / period_dec

        return atr.quantize(Decimal("0.0001"))

    @staticmethod
    def calculate_52w_high_low(
        highs: List[Decimal],
        lows: List[Decimal],
        lookback: int = 252,
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Return 52-week (approx. lookback trading days) high and low.

        Uses the most recent `lookback` bars when more history is available.
        """
        if not highs or not lows or len(highs) != len(lows):
            return None, None

        window_highs = highs[-lookback:] if len(highs) > lookback else highs
        window_lows = lows[-lookback:] if len(lows) > lookback else lows
        if not window_highs or not window_lows:
            return None, None

        return (
            max(window_highs).quantize(Decimal("0.0001")),
            min(window_lows).quantize(Decimal("0.0001")),
        )

    @staticmethod
    def find_support_resistance(
        highs: List[Decimal],
        lows: List[Decimal],
        closes: Optional[List[Decimal]] = None,
        lookback: int = 60,
        swing_order: int = 2,
        max_levels: int = 3,
    ) -> dict:
        """
        Estimate support/resistance from recent swing lows/highs.

        A swing low is a low lower than `swing_order` neighbours on each side;
        swing highs are symmetric. Returns nearest support below and resistance
        above the latest close when available.
        """
        n = len(lows)
        if n < (2 * swing_order + 1) or len(highs) != n:
            return {
                "support": None,
                "resistance": None,
                "support_levels": [],
                "resistance_levels": [],
            }

        start = max(0, n - lookback)
        swing_lows: List[Decimal] = []
        swing_highs: List[Decimal] = []

        for i in range(start + swing_order, n - swing_order):
            low_i = lows[i]
            high_i = highs[i]
            is_swing_low = all(
                low_i <= lows[i - j] and low_i <= lows[i + j]
                for j in range(1, swing_order + 1)
            )
            is_swing_high = all(
                high_i >= highs[i - j] and high_i >= highs[i + j]
                for j in range(1, swing_order + 1)
            )
            if is_swing_low:
                swing_lows.append(low_i)
            if is_swing_high:
                swing_highs.append(high_i)

        # Deduplicate nearby levels (within 0.5%)
        def _cluster(levels: List[Decimal]) -> List[Decimal]:
            if not levels:
                return []
            ordered = sorted(levels)
            clusters: List[Decimal] = [ordered[0]]
            for lvl in ordered[1:]:
                ref = clusters[-1]
                if ref == 0 or abs(lvl - ref) / ref > Decimal("0.005"):
                    clusters.append(lvl)
                else:
                    clusters[-1] = ((clusters[-1] + lvl) / Decimal("2")).quantize(
                        Decimal("0.0001")
                    )
            return clusters

        support_levels = _cluster(swing_lows)[-max_levels:]
        resistance_levels = _cluster(swing_highs)[:max_levels]

        last_close = closes[-1] if closes else (lows[-1] + highs[-1]) / Decimal("2")
        support: Optional[Decimal] = None
        resistance: Optional[Decimal] = None

        below = [s for s in support_levels if s <= last_close]
        above = [r for r in resistance_levels if r >= last_close]
        if below:
            support = max(below).quantize(Decimal("0.0001"))
        elif support_levels:
            support = min(support_levels).quantize(Decimal("0.0001"))

        if above:
            resistance = min(above).quantize(Decimal("0.0001"))
        elif resistance_levels:
            resistance = max(resistance_levels).quantize(Decimal("0.0001"))

        return {
            "support": support,
            "resistance": resistance,
            "support_levels": [s.quantize(Decimal("0.0001")) for s in support_levels],
            "resistance_levels": [r.quantize(Decimal("0.0001")) for r in resistance_levels],
        }
