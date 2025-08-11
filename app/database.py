"""Simple JSON-based user store.

This module implements a very lightweight persistence layer using a JSON file
(`users.json`) stored alongside the application code.  It is **not** suitable
for production use because it does not hash passwords, handle concurrent
writes or enforce uniqueness beyond basic checks.  It exists solely to make
the prototype self‑contained and allow development without external services.

Replace this module with a proper database client (e.g. Supabase) when
migrating to production.
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional, Any
import uuid


# Path to the JSON file that holds user records.  The parent directory is
# created automatically if it doesn’t exist.
DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_FILE = DATA_DIR / "users.json"

# Default starting number of points for new accounts
INITIAL_POINTS = 30

def _ensure_storage() -> None:
    """Make sure the data directory and JSON file exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}", encoding="utf-8")


def _load_users() -> Dict[str, Dict[str, Any]]:
    """Load the users dictionary from disk."""
    _ensure_storage()
    raw = USERS_FILE.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
        assert isinstance(data, dict)
        return data
    except Exception:
        # Corrupted file or invalid JSON; reset to empty
        return {}


def _save_users(users: Dict[str, Dict[str, Any]]) -> None:
    """Persist the users dictionary to disk."""
    _ensure_storage()
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Return the user record matching the email, if any."""
    users = _load_users()
    for user in users.values():
        if user.get("email") == email:
            return user
    return None


def create_user(email: str, password: str) -> Dict[str, Any]:
    """Create a new user with the given email and password.

    Raises a `ValueError` if the email is already registered.
    """
    users = _load_users()
    if any(u.get("email") == email for u in users.values()):
        raise ValueError("Email is already registered")
    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "email": email,
        "password": password,
        "points": INITIAL_POINTS,
        "last_signin": None  # ISO date string of last daily sign‑in
    }
    users[user_id] = new_user
    _save_users(users)
    return new_user


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Return the user record if the email/password match, else None."""
    users = _load_users()
    for user in users.values():
        if user.get("email") == email and user.get("password") == password:
            return user
    return None


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Return the user with the given ID, or None if not found."""
    users = _load_users()
    return users.get(user_id)


def update_user(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a user record with the provided fields.

    Returns the updated record.  Raises KeyError if the user does not exist.
    """
    users = _load_users()
    if user_id not in users:
        raise KeyError("User not found")
    users[user_id].update(updates)
    _save_users(users)
    return users[user_id]