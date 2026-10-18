"""Market hours and trading calendar logic for Indian Exchanges (NSE/BSE)."""

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Set
from zoneinfo import ZoneInfo

# Indian Standard Time
IST = ZoneInfo("Asia/Kolkata")

# NSE Market Timings (IST)
PRE_OPEN_TIME = time(9, 0)
MARKET_OPEN_TIME = time(9, 15)
MARKET_CLOSE_TIME = time(15, 30)

# In-memory cached holiday sets
_HOLIDAYS_SET: Optional[Set[date]] = None
_SPECIAL_SESSIONS: Optional[Dict[date, Dict[str, Any]]] = None


def _find_holidays_file() -> Path:
    """Locate the nse_holidays_2026.json file across common locations."""
    candidate_paths = [
        # Relative to this file: backend/app/core/market_hours.py -> BharatMarkets/data/...
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "nse_holidays_2026.json",
        # Relative to backend directory
        Path(__file__).resolve().parent.parent.parent / "data" / "nse_holidays_2026.json",
        Path.cwd() / "data" / "nse_holidays_2026.json",
        Path.cwd().parent / "data" / "nse_holidays_2026.json",
        Path("/app/data/nse_holidays_2026.json"),
    ]
    for path in candidate_paths:
        if path.is_file():
            return path
    # Default fallback path
    return candidate_paths[0]


def load_holidays() -> tuple[Set[date], Dict[date, Dict[str, Any]]]:
    """Load and parse holidays and special sessions from JSON file."""
    global _HOLIDAYS_SET, _SPECIAL_SESSIONS
    if _HOLIDAYS_SET is not None and _SPECIAL_SESSIONS is not None:
        return _HOLIDAYS_SET, _SPECIAL_SESSIONS

    holidays: Set[date] = set()
    special_sessions: Dict[date, Dict[str, Any]] = {}

    file_path = _find_holidays_file()
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data.get("holidays", []):
                try:
                    holidays.add(date.fromisoformat(item["date"]))
                except (KeyError, ValueError):
                    continue

            for item in data.get("special_sessions", []):
                try:
                    special_sessions[date.fromisoformat(item["date"])] = item
                except (KeyError, ValueError):
                    continue
        except Exception:
            # Fallback will maintain empty sets or minimal known holidays
            pass

    # Standard fallback if file was missing or empty
    if not holidays:
        holidays.add(date(2026, 1, 26))  # Republic Day
        holidays.add(date(2026, 8, 15))  # Independence Day
        holidays.add(date(2026, 10, 2))  # Gandhi Jayanti

    _HOLIDAYS_SET = holidays
    _SPECIAL_SESSIONS = special_sessions
    return _HOLIDAYS_SET, _SPECIAL_SESSIONS


def is_trading_day(check_date: date) -> bool:
    """
    Check if a given date is a trading day on NSE/BSE.

    Args:
        check_date: The date to check.

    Returns:
        bool: True if it is a normal trading day or a special session day, False otherwise.
    """
    holidays, special = load_holidays()

    # Special trading sessions (e.g., Muhurat trading on Sunday) are trading days
    if check_date in special:
        return True

    # Weekends (Saturday=5, Sunday=6) are non-trading days
    if check_date.weekday() in (5, 6):
        return False

    # Holidays are non-trading days
    if check_date in holidays:
        return False

    return True


def is_market_open(check_time: Optional[datetime] = None) -> bool:
    """
    Determine if the Indian stock market is currently open for regular trading.

    Args:
        check_time: Optional datetime to check. If None, current IST time is used.

    Returns:
        bool: True if market is currently between 09:15 and 15:30 on a trading day.
    """
    if check_time is None:
        check_time = datetime.now(IST)
    elif check_time.tzinfo is None:
        check_time = check_time.replace(tzinfo=IST)
    else:
        check_time = check_time.astimezone(IST)

    today = check_time.date()
    if not is_trading_day(today):
        return False

    current_t = check_time.time()
    return MARKET_OPEN_TIME <= current_t < MARKET_CLOSE_TIME


def get_next_market_open(from_time: Optional[datetime] = None) -> datetime:
    """
    Compute the next market open timestamp in IST.

    Args:
        from_time: Optional starting datetime in IST.

    Returns:
        datetime: Next market open datetime with IST timezone.
    """
    if from_time is None:
        from_time = datetime.now(IST)
    elif from_time.tzinfo is None:
        from_time = from_time.replace(tzinfo=IST)
    else:
        from_time = from_time.astimezone(IST)

    candidate_date = from_time.date()

    # If today is a trading day and we are before 9:15 AM
    if is_trading_day(candidate_date) and from_time.time() < MARKET_OPEN_TIME:
        return datetime.combine(candidate_date, MARKET_OPEN_TIME, tzinfo=IST)

    # Otherwise scan upcoming days
    candidate_date += timedelta(days=1)
    while not is_trading_day(candidate_date):
        candidate_date += timedelta(days=1)

    return datetime.combine(candidate_date, MARKET_OPEN_TIME, tzinfo=IST)


def get_market_status(check_time: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get detailed market status dictionary including human-friendly status text.

    Args:
        check_time: Optional datetime to check. If None, current IST time is used.

    Returns:
        Dict[str, Any]: Status payload with is_open, status, status_text, current_time_ist, next_open.
    """
    if check_time is None:
        check_time = datetime.now(IST)
    elif check_time.tzinfo is None:
        check_time = check_time.replace(tzinfo=IST)
    else:
        check_time = check_time.astimezone(IST)

    today = check_time.date()
    current_t = check_time.time()
    holidays, _ = load_holidays()

    next_open_dt = get_next_market_open(check_time)
    next_open_str = next_open_dt.strftime("%Y-%m-%d %I:%M %p IST")

    if today.weekday() in (5, 6) and not is_trading_day(today):
        status = "WEEKEND"
        status_text = f"Market is Closed for the Weekend. Opens next at {next_open_str}."
        is_open = False
    elif today in holidays:
        status = "HOLIDAY"
        status_text = f"Market is Closed for Holiday. Opens next at {next_open_str}."
        is_open = False
    elif current_t < PRE_OPEN_TIME:
        status = "CLOSED"
        status_text = f"Market is Closed. Pre-open session starts at 09:00 AM IST. Regular trading opens at {next_open_str}."
        is_open = False
    elif PRE_OPEN_TIME <= current_t < MARKET_OPEN_TIME:
        status = "PRE_OPEN"
        status_text = "Pre-Open Session in progress (09:00 AM - 09:15 AM IST). Regular trading opens at 09:15 AM IST."
        is_open = False
    elif MARKET_OPEN_TIME <= current_t < MARKET_CLOSE_TIME:
        status = "OPEN"
        status_text = "Market is Open for Live Trading."
        is_open = True
    else:
        status = "CLOSED"
        status_text = f"Market is Closed for the day. Opens next at {next_open_str}."
        is_open = False

    return {
        "is_open": is_open,
        "status": status,
        "status_text": status_text,
        "current_time_ist": check_time.isoformat(),
        "next_open_ist": next_open_dt.isoformat(),
        "exchange": "NSE",
    }


def get_cache_ttl(check_time: Optional[datetime] = None) -> int:
    """
    Return dynamic Redis cache TTL based on whether the market is open.

    Returns:
        int: 15 seconds during live market hours, 300 seconds (5 mins) when closed.
    """
    return 15 if is_market_open(check_time) else 300
