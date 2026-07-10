"""Price = USDC per V.

Computed from ``(F + μ·ExtRev) / Supply`` (Invariant I5). Always
non-negative. Eight-decimal precision — finer than V/USDC because price
is a derived ratio and we want to avoid stair-stepping.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import TYPE_CHECKING, Self

from pydantic import RootModel, field_validator

_QUANTUM = Decimal("0.00000001")
_Numeric = Decimal | int | str | float


class Price(RootModel[Decimal]):
    """USDC per V. Non-negative, 8 decimal places."""

    model_config = {"frozen": True}

    if TYPE_CHECKING:

        def __init__(self, root: _Numeric | Price = ..., /) -> None: ...

    @field_validator("root", mode="before")
    @classmethod
    def _coerce(cls, value: object) -> Decimal:
        if isinstance(value, Price):
            return value.root
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
        if decimal_value < 0:
            raise ValueError(f"Price must be non-negative, got {decimal_value}")
        return decimal_value.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)

    @classmethod
    def zero(cls) -> Self:
        return cls(Decimal(0))

    def __mul__(self, factor: Decimal | int) -> Price:
        if isinstance(factor, Price):
            return NotImplemented
        return Price(self.root * Decimal(str(factor)))

    __rmul__ = __mul__

    def __lt__(self, other: Price) -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.root < other.root

    def __le__(self, other: Price) -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.root <= other.root

    def __gt__(self, other: Price) -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.root > other.root

    def __ge__(self, other: Price) -> bool:
        if not isinstance(other, Price):
            return NotImplemented
        return self.root >= other.root

    def __str__(self) -> str:
        return f"Price({self.root} USDC/V)"
