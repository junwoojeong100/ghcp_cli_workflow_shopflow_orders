"""Time provider. Kept in one place so tests can monkeypatch it easily."""

from datetime import date, datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


def today() -> date:
    return now().date()
