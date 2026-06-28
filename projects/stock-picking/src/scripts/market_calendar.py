#!/usr/bin/env python3
"""Production market calendar source using pandas-market-calendars.

Provides trading-day status for A-share (XSHG), HK (XHKG), and US (NYSE)
markets. Replaces the M4b hard-reject for ``production_calendar`` with
real exchange-calendar data.

Dependencies: pandas-market-calendars, pandas, pytz
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import pandas as pd

try:
    import pandas_market_calendars as mcal
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pandas-market-calendars is required: pip install pandas-market-calendars"
    ) from exc


CALENDAR_VERSION = "pmc-5.4.0"

_MARKET_CALENDAR_MAP: dict[str, str] = {
    "CN": "XSHG",
    "HK": "XHKG",
    "US": "NYSE",
}

_TZ_MAP: dict[str, str] = {
    "CN": "Asia/Shanghai",
    "HK": "Asia/Hong_Kong",
    "US": "America/New_York",
}


def _get_calendar(market: str) -> Any:
    """Return the exchange calendar for the given market code."""
    cal_name = _MARKET_CALENDAR_MAP.get(market)
    if cal_name is None:
        raise ValueError(f"Unsupported market for calendar lookup: {market!r}")
    return mcal.get_calendar(cal_name)


def _to_date(timestamp_or_str: Any) -> dt.date:
    """Coerce a date string or Timestamp to a plain date."""
    if isinstance(timestamp_or_str, dt.date) and not isinstance(timestamp_or_str, dt.datetime):
        return timestamp_or_str
    if isinstance(timestamp_or_str, dt.datetime):
        return timestamp_or_str.astimezone(dt.timezone.utc).date()
    if isinstance(timestamp_or_str, str):
        return dt.date.fromisoformat(timestamp_or_str[:10])
    if isinstance(timestamp_or_str, pd.Timestamp):
        return timestamp_or_str.tz_convert("UTC").date()
    raise TypeError(f"Cannot coerce {type(timestamp_or_str)} to date")


def get_calendar_status(
    market: str,
    check_date: dt.date | str | None = None,
) -> dict[str, Any]:
    """Return trading-calendar status for *market* on *check_date*.

    Returns a dict with keys:
        calendar_status: "open" | "closed" | "half_day" | "unknown"
        market_session: "regular" | "closed" | "half_day"
        calendar_source: "production_calendar"
        calendar_source_version: str
        calendar_checked_at: ISO-8601 UTC timestamp
        market: str
        checked_date: ISO date string
        skip_reason: str  ("none" when open)
        details: dict with open/close times if available
    """
    if check_date is None:
        today = dt.date.today()
    else:
        today = _to_date(check_date)

    cal = _get_calendar(market)

    # Query a small window around the date to catch timezone edge cases
    window_start = pd.Timestamp(today)
    window_end = pd.Timestamp(today) + pd.Timedelta(days=1)

    try:
        sched = cal.schedule(
            start_date=window_start.strftime("%Y-%m-%d"),
            end_date=window_end.strftime("%Y-%m-%d"),
        )
    except Exception:
        return {
            "calendar_status": "unknown",
            "market_session": "closed",
            "calendar_source": "production_calendar",
            "calendar_source_version": CALENDAR_VERSION,
            "calendar_checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "market": market,
            "checked_date": today.isoformat(),
            "skip_reason": "calendar_lookup_error",
            "details": {},
        }

    # Check if the queried date is in the schedule
    # pandas-market-calendars returns tz-aware or tz-naive depending on version;
    # normalize both to plain dates for comparison
    sched_dates = set()
    for idx in sched.index:
        if hasattr(idx, 'tz_convert') and idx.tzinfo is not None:
            sched_dates.add(idx.tz_convert('UTC').date())
        elif hasattr(idx, 'date'):
            sched_dates.add(idx.date())
        else:
            sched_dates.add(_to_date(idx))
    today_in_schedule = today in sched_dates

    if not today_in_schedule:
        # Date is not a trading day
        return {
            "calendar_status": "closed",
            "market_session": "closed",
            "calendar_source": "production_calendar",
            "calendar_source_version": CALENDAR_VERSION,
            "calendar_checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "market": market,
            "checked_date": today.isoformat(),
            "skip_reason": "holiday_or_weekend",
            "details": {},
        }

    # Date is a trading day — check for half-day (early close)
    tz = _TZ_MAP.get(market, "UTC")
    row = sched.iloc[0]
    open_time = row["market_open"]
    close_time = row["market_close"]

    # Get the "normal" session length for this calendar to detect half-days
    # pandas-market-calendars tags early closes; we can check via .early_closes
    try:
        early_closes = cal.early_closes(sched)
        is_half_day = len(early_closes) > 0
    except Exception:
        is_half_day = False

    calendar_status = "half_day" if is_half_day else "open"

    return {
        "calendar_status": calendar_status,
        "market_session": "half_day" if is_half_day else "regular",
        "calendar_source": "production_calendar",
        "calendar_source_version": CALENDAR_VERSION,
        "calendar_checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "market": market,
        "checked_date": today.isoformat(),
        "skip_reason": "none",
        "details": {
            "market_open_utc": open_time.isoformat() if open_time is not None else None,
            "market_close_utc": close_time.isoformat() if close_time is not None else None,
            "timezone": tz,
        },
    }


def is_trading_day(market: str, check_date: dt.date | str | None = None) -> bool:
    """Convenience: True if *market* is open (regular or half-day) on *check_date*."""
    status = get_calendar_status(market, check_date)
    return status["calendar_status"] in {"open", "half_day"}
