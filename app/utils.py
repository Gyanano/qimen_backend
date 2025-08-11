"""Miscellaneous helper functions."""

from datetime import datetime, date, time
from dateutil import tz


def now_in_pacific() -> datetime:
    """Return the current time in America/Los_Angeles timezone."""
    pacific = tz.gettz("America/Los_Angeles")
    return datetime.now(pacific)


def parse_birth_datetime(birth_date: date, birth_time: time) -> datetime:
    """Combine separate date and time objects into a timezone-aware datetime.

    The resulting datetime is localised to America/Los_Angeles.  If the input
    time object has no tzinfo, one is added.  If tzinfo is present, the
    datetime is converted to Pacific.
    """
    pacific = tz.gettz("America/Los_Angeles")
    dt = datetime.combine(birth_date, birth_time)
    if birth_time.tzinfo is None:
        return dt.replace(tzinfo=pacific)
    else:
        return dt.astimezone(pacific)