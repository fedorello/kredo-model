"""Concrete Clock implementations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


class SystemClock:
    """UTC wall-clock used in production."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class ManualClock:
    """Fixed clock used in tests; time advances only when ``advance`` is called."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: int) -> None:
        self._now = self._now + timedelta(seconds=seconds)


class FlagToken:
    """Trivial CancellationToken used by tests and the in-process runner."""

    def __init__(self) -> None:
        self._cancelled = False

    def is_cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True
