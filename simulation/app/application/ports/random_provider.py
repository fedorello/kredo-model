"""RandomProvider — deterministic source of randomness.

Implementations must support snapshotting their internal state to
``bytes`` so the engine can pause and resume a run without losing
determinism. The ``app.infrastructure`` package provides the concrete
``random.Random``-based implementation; tests can supply their own.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

T = TypeVar("T")


class RandomProvider(Protocol):
    """Deterministic random number generator behind a port."""

    def random(self) -> float:
        """Return a float in [0.0, 1.0)."""
        ...

    def randint(self, low: int, high: int) -> int:
        """Return an integer N such that low <= N <= high."""
        ...

    def choice(self, seq: list[T]) -> T:
        """Return a random element from a non-empty sequence."""
        ...

    def sample(self, population: list[T], k: int) -> list[T]:
        """Return ``k`` unique elements from ``population``."""
        ...

    def shuffle(self, items: list[T]) -> None:
        """Shuffle ``items`` in place."""
        ...

    def get_state(self) -> bytes:
        """Serialise the internal state — passed back to ``set_state``."""
        ...

    def set_state(self, state: bytes) -> None:
        """Restore a previously serialised state."""
        ...
