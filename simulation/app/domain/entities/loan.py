"""Loan — an open or closed credit position from a Transact operation.

Each Loan freezes its ε at creation time (math §6.1: ``ΔE_released =
Δd · ε(τ_B)``) so that escrow accounting stays correct even as the
system-wide ε changes between the loan's open and close ticks.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.value_objects import LoanId, LoanState, MemberId, V


class Loan(BaseModel):
    """A credit position opened during a transaction with insufficient buyer balance."""

    model_config = ConfigDict(frozen=True)

    id: LoanId
    borrower: MemberId
    principal: V
    """Total credit emitted (N_credit at the originating transaction)."""
    repaid: V
    """Cumulative amount that has been repaid."""
    opened_at: int
    epsilon_at_creation: Decimal
    """Compensation rate ε at the moment this loan was opened — frozen."""
    escrow_reserved: V
    """Amount held in DistributionEscrow specifically against this loan."""
    state: LoanState

    @field_validator("principal", "repaid", "escrow_reserved")
    @classmethod
    def _non_negative(cls, value: V) -> V:
        if value.is_negative():
            raise ValueError(f"loan amount must be non-negative, got {value}")
        return value

    @field_validator("epsilon_at_creation")
    @classmethod
    def _epsilon_in_range(cls, value: Decimal) -> Decimal:
        if value < 0 or value > 1:
            raise ValueError(f"epsilon must lie in [0, 1], got {value}")
        return value

    def outstanding(self) -> V:
        """Principal not yet repaid."""
        return self.principal - self.repaid

    def is_open(self) -> bool:
        return self.state == LoanState.OPEN

    def is_repaid(self) -> bool:
        return self.state == LoanState.REPAID

    def is_defaulted(self) -> bool:
        return self.state == LoanState.DEFAULTED
