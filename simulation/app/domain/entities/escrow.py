"""Distribution Escrow — compensatory emission staged for release on repayment.

Architecture §4.2: per-loan reservation lives on the Loan entity itself
(`Loan.escrow_reserved`). This entity holds the *aggregate* total, kept
in sync with ``sum(loan.escrow_reserved for loan in loans if loan.is_open())``.
The redundancy is intentional — the running total is read on every tick
to compute Supply, and recomputing it from all loans would be O(loans).
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.value_objects import V


class DistributionEscrow(BaseModel):
    """Aggregate amount held in escrow against open loans."""

    model_config = ConfigDict(frozen=True)

    total: V

    @field_validator("total")
    @classmethod
    def _non_negative(cls, value: V) -> V:
        if value.is_negative():
            raise ValueError(f"escrow total must be non-negative, got {value}")
        return value

    @classmethod
    def empty(cls) -> Self:
        return cls(total=V.zero())
