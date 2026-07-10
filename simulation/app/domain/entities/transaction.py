"""TransactionRecord — immutable append-only entry in the Club's history."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.value_objects import (
    CategoryId,
    Confidence,
    LoanId,
    MemberId,
    TransactionId,
    V,
)


class TransactionRecord(BaseModel):
    """Outcome of a successful Transact operation.

    Includes everything needed to audit emission decisions retroactively:
    confidence at the time of approval, the credit portion (which drove ε
    accrual), and which loans were repaid as part of the same transaction.
    """

    model_config = ConfigDict(frozen=True)

    id: TransactionId
    tick: int
    actor: MemberId
    """The member providing the service (executor)."""
    receiver: MemberId
    """The member paying for the service."""
    amount: V
    """Total transaction value declared. Must be positive."""
    category: CategoryId
    confidence: Confidence
    n_credit: V
    """Emission portion: ``max(0, amount - max(0, receiver.balance))``."""
    loan_id: LoanId | None = None
    """The loan opened by this transaction, if any."""
    repaid_loans: tuple[LoanId, ...] = ()
    """Loans of `actor` that were automatically repaid by V flowing in."""

    @field_validator("amount")
    @classmethod
    def _amount_positive(cls, value: V) -> V:
        if not value.is_positive():
            raise ValueError(f"transaction amount must be positive, got {value}")
        return value

    @field_validator("n_credit")
    @classmethod
    def _credit_non_negative(cls, value: V) -> V:
        if value.is_negative():
            raise ValueError(f"n_credit must be non-negative, got {value}")
        return value
