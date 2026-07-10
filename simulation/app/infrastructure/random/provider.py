"""``random.Random``-based RandomProvider with state serialisation.

Pickle is used for state because ``random.Random.getstate()`` returns a
nested tuple; pickle round-trips it cleanly. This keeps state opaque
to the rest of the system.
"""

from __future__ import annotations

import pickle
import random
from typing import TypeVar

T = TypeVar("T")


class StdRandomProvider:
    """Concrete RandomProvider using Python's ``random.Random``."""

    def __init__(self, seed: int = 0) -> None:
        self._rng = random.Random(seed)

    def random(self) -> float:
        return self._rng.random()

    def randint(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)

    def choice(self, seq: list[T]) -> T:
        return self._rng.choice(seq)

    def sample(self, population: list[T], k: int) -> list[T]:
        return self._rng.sample(population, k)

    def shuffle(self, items: list[T]) -> None:
        self._rng.shuffle(items)

    def get_state(self) -> bytes:
        return pickle.dumps(self._rng.getstate())

    def set_state(self, state: bytes) -> None:
        self._rng.setstate(pickle.loads(state))
