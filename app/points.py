"""Points management logic.

Users accumulate points through actions such as daily sign‑ins and spend them
when submitting inquiries or using analysis tools.  This module defines
functions to earn and spend points and encapsulates the business rules around
these operations.
"""

from datetime import datetime, date
from dateutil import tz
from typing import Tuple

from . import database

# Number of points awarded for a successful daily sign‑in
DAILY_SIGNIN_POINTS = 5


def _today_in_user_tz() -> date:
    """Return today's date in the America/Los_Angeles timezone."""
    pacific = tz.gettz("America/Los_Angeles")
    return datetime.now(pacific).date()


def earn_daily_signin(user_id: str) -> int:
    """Award points for a daily sign‑in.

    If the user has already signed in today, a `ValueError` is raised.  On
    success, the user's point balance is increased and their `last_signin`
    field is updated.  The function returns the new point balance.
    """
    user = database.get_user(user_id)
    if not user:
        raise ValueError("User not found")
    today = _today_in_user_tz()
    last = user.get("last_signin")
    if last:
        # Attempt to parse the stored ISO date.  If parsing fails we treat it as
        # if the user has not signed in before.  Only raise an error after
        # successful parsing.
        try:
            last_date = date.fromisoformat(last)
        except Exception:
            last_date = None
        if last_date and last_date == today:
            raise ValueError("User has already signed in today")
    new_points = user.get("points", 0) + DAILY_SIGNIN_POINTS
    database.update_user(user_id, {"points": new_points, "last_signin": today.isoformat()})
    return new_points


def spend_points(user_id: str, amount: int) -> int:
    """Deduct a number of points from the user's balance.

    Raises a `ValueError` if the user has insufficient points.  Returns the
    updated balance.
    """
    if amount <= 0:
        raise ValueError("Amount must be positive")
    user = database.get_user(user_id)
    if not user:
        raise ValueError("User not found")
    current = user.get("points", 0)
    if current < amount:
        raise ValueError("Insufficient points")
    new_balance = current - amount
    database.update_user(user_id, {"points": new_balance})
    return new_balance