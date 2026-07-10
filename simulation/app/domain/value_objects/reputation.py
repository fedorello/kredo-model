"""Reputation R — soulbound, non-negative, four-decimal precision.

R is the second token, but it never moves between members (Invariant I6).
Only `mint` (rewards) and `burn` (sanctions) are allowed; arithmetic on
balances is in this module, but transfer is not implemented anywhere.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import TYPE_CHECKING, Self

from pydantic import RootModel, field_validator

_QUANTUM = Decimal("0.0001")
_Numeric = Decimal | int | str | float


class R(RootModel[Decimal]):
    """Reputation score. Always non-negative, 4 decimal places."""

    model_config = {"frozen": True}

    if TYPE_CHECKING:

        def __init__(self, root: _Numeric | R = ..., /) -> None: ...

    @field_validator("root", mode="before")
    @classmethod
    def _coerce(cls, value: object) -> Decimal:
        if isinstance(value, R):
            return value.root
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
        if decimal_value < 0:
            raise ValueError(f"R must be non-negative, got {decimal_value}")
        return decimal_value.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)

    @classmethod
    def zero(cls) -> Self:
        return cls(Decimal(0))

    def add(self, delta: R) -> R:
        """Mint reputation. Always increases R."""
        if not isinstance(delta, R):
            raise TypeError(f"expected R, got {type(delta).__name__}")
        return R(self.root + delta.root)

    def burn(self, delta: R) -> R:
        """Burn reputation. Floors at zero — repeated burns can't push below 0."""
        if not isinstance(delta, R):
            raise TypeError(f"expected R, got {type(delta).__name__}")
        new_value = self.root - delta.root
        return R(max(Decimal(0), new_value))

    def __lt__(self, other: R) -> bool:
        if not isinstance(other, R):
            return NotImplemented
        return self.root < other.root

    def __le__(self, other: R) -> bool:
        if not isinstance(other, R):
            return NotImplemented
        return self.root <= other.root

    def __gt__(self, other: R) -> bool:
        if not isinstance(other, R):
            return NotImplemented
        return self.root > other.root

    def __ge__(self, other: R) -> bool:
        if not isinstance(other, R):
            return NotImplemented
        return self.root >= other.root

    def is_zero(self) -> bool:
        return self.root == 0

    def __str__(self) -> str:
        return f"R({self.root})"
