from datetime import datetime

from homeassistant.util import dt as dt_util


def parse_datetime_with_kind(value: str) -> tuple[datetime | None, str | None]:
    """Parse an ISO datetime, ISO date or HH:MM[:SS] time into a timezone-aware datetime.

    Returns (datetime, kind) where kind is one of "datetime", "date", "time", or None.
    Naive ISO datetimes are interpreted as **local** time (HA's configured timezone),
    not UTC, since users typically store local timestamps.
    """
    local_tz = dt_util.DEFAULT_TIME_ZONE
    dt = dt_util.parse_datetime(value)
    if dt is not None:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=local_tz)
        return dt, "datetime"
    d = dt_util.parse_date(value)
    if d is not None:
        return datetime(d.year, d.month, d.day, tzinfo=local_tz), "date"
    t = dt_util.parse_time(value)
    if t is not None:
        today = dt_util.now().date()
        return datetime.combine(today, t, tzinfo=local_tz), "time"
    return None, None


def parse_datetime(value: str) -> datetime | None:
    """Parse an ISO datetime, ISO date, or HH:MM[:SS] time into a timezone-aware datetime."""
    dt, _ = parse_datetime_with_kind(value)
    return dt