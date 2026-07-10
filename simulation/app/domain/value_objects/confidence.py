"""Confidence ∈ [0, 1] for a transaction.

Used in Invariant I2: emission only when ``confidence ≥ θ_min``.
Bounded on both sides by construction; downstream code never needs to
clip or check.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import TYPE_CHECKING, Self

from pydantic import RootModel, field_validator

_QUANTUM = Decimal("0.0001")
_Numeric = Decimal | int | str | float


class Confidence(RootModel[Decimal]):
    """A bounded confidence score in the closed interval [0, 1]."""

    model_config = {"frozen": True}

    if TYPE_CHECKING:

        def __init__(self, root: _Numeric | Confidence = ..., /) -> None: ...

    @field_validator("root", mode="before")
    @classmethod
    def _coerce(cls, value: object) -> Decimal:
        if isinstance(value, Confidence):
            return value.root
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
        if decimal_value < 0 or decimal_value > 1:
            raise ValueError(f"Confidence must lie in [0, 1], got {decimal_value}")
        return decimal_value.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)

    @classmethod
    def zero(cls) -> Self:
        return cls(Decimal(0))

    @classmethod
    def one(cls) -> Self:
        return cls(Decimal(1))

    def __lt__(self, other: Confidence) -> bool:
        if not isinstance(other, Confidence):
            return NotImplemented
        return self.root < other.root

    def __le__(self, other: Confidence) -> bool:
        if not isinstance(other, Confidence):
            return NotImplemented
        return self.root <= other.root

    def __gt__(self, other: Confidence) -> bool:
        if not isinstance(other, Confidence):
            return NotImplemented
        return self.root > other.root

    def __ge__(self, other: Confidence) -> bool:
        if not isinstance(other, Confidence):
            return NotImplemented
        return self.root >= other.root

    def __str__(self) -> str:
        return f"Confidence({self.root})"
