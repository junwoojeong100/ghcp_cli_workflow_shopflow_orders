"""시간 공급자. 테스트에서 monkeypatch 하기 쉽도록 한 곳에 모은다."""

from datetime import date, datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


def today() -> date:
    return now().date()
