"""Withdrawal Queue — pending Convert requests when fund coverage is low.

Architecture §4.2 / math §7.3: when ρ = F/(P·S) drops below ρ*, new
Convert calls land in the queue with a delay (1–30 days) and a discount.
The entry below is what we actually park in the queue tuple inside
ClubState.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.domain.value_objects import MemberId, V


class WithdrawalQueueEntry(BaseModel):
    """One pending Convert request."""

    model_config = ConfigDict(frozen=True)

    member: MemberId
    amount: V
    """V the member wants to convert. Must be positive."""
    requested_at: int
    execute_at: int

    @field_validator("amount")
    @classmethod
    def _positive(cls, value: V) -> V:
        if not value.is_positive():
            raise ValueError(f"withdrawal amount must be positive, got {value}")
        return value

    @model_validator(mode="after")
    def _execute_after_request(self) -> WithdrawalQueueEntry:
        if self.execute_at < self.requested_at:
            raise ValueError(
                f"execute_at ({self.execute_at}) cannot be before "
                f"requested_at ({self.requested_at})"
            )
        return self
