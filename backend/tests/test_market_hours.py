"""Unit tests for Indian stock market trading hours and calendar logic."""

from datetime import datetime
from zoneinfo import ZoneInfo
import pytest

from app.core import market_hours

IST = ZoneInfo("Asia/Kolkata")


def test_weekday_during_market_hours():
    """Test is_market_open() on a regular trading weekday at 11:00 AM IST."""
    # 2026-01-14 is Wednesday (regular trading day)
    dt = datetime(2026, 1, 14, 11, 0, 0, tzinfo=IST)
    assert market_hours.is_market_open(dt) is True

    status = market_hours.get_market_status(dt)
    assert status["is_open"] is True
    assert status["status"] == "OPEN"
    assert market_hours.get_cache_ttl(dt) == 15


def test_weekend_market_closed():
    """Test is_market_open() on a weekend (Sunday 11:00 AM IST)."""
    # 2026-01-18 is Sunday
    dt = datetime(2026, 1, 18, 11, 0, 0, tzinfo=IST)
    assert market_hours.is_market_open(dt) is False

    status = market_hours.get_market_status(dt)
    assert status["is_open"] is False
    assert status["status"] == "WEEKEND"
    assert market_hours.get_cache_ttl(dt) == 300


def test_holiday_market_closed():
    """Test is_market_open() on Republic Day 2026-01-26 (Monday)."""
    # 2026-01-26 is Monday and Republic Day holiday
    dt = datetime(2026, 1, 26, 11, 0, 0, tzinfo=IST)
    assert market_hours.is_market_open(dt) is False

    status = market_hours.get_market_status(dt)
    assert status["is_open"] is False
    assert status["status"] == "HOLIDAY"
    assert market_hours.get_cache_ttl(dt) == 300


def test_pre_open_session():
    """Test is_market_open() during pre-open session (09:05 AM IST)."""
    # 2026-01-14 Wednesday at 09:05 AM IST
    dt = datetime(2026, 1, 14, 9, 5, 0, tzinfo=IST)
    # Regular trading is not open during pre-open session
    assert market_hours.is_market_open(dt) is False

    status = market_hours.get_market_status(dt)
    assert status["is_open"] is False
    assert status["status"] == "PRE_OPEN"


def test_after_hours_market_closed():
    """Test is_market_open() after regular session close (04:00 PM IST)."""
    # 2026-01-14 Wednesday at 04:00 PM IST (16:00)
    dt = datetime(2026, 1, 14, 16, 0, 0, tzinfo=IST)
    assert market_hours.is_market_open(dt) is False

    status = market_hours.get_market_status(dt)
    assert status["is_open"] is False
    assert status["status"] == "CLOSED"
    assert market_hours.get_cache_ttl(dt) == 300


def test_before_pre_open_closed():
    """Test is_market_open() before pre-open (08:30 AM IST)."""
    # 2026-01-14 Wednesday at 08:30 AM IST
    dt = datetime(2026, 1, 14, 8, 30, 0, tzinfo=IST)
    assert market_hours.is_market_open(dt) is False

    status = market_hours.get_market_status(dt)
    assert status["is_open"] is False
    assert status["status"] == "CLOSED"
