"""Value objects — small, immutable, type-safe wrappers.

Re-exports keep import paths short:

    from app.domain.value_objects import V, USDC, R, Confidence, Price
"""

from __future__ import annotations

from app.domain.value_objects.category import CategoryId, LoanState, MemberKind
from app.domain.value_objects.confidence import Confidence
from app.domain.value_objects.ids import (
    LoanId,
    MemberId,
    TransactionId,
    loan_id,
    member_id,
    new_loan_id,
    new_member_id,
    new_transaction_id,
    transaction_id,
)
from app.domain.value_objects.money import USDC, V
from app.domain.value_objects.price import Price
from app.domain.value_objects.reputation import R

__all__ = [
    "USDC",
    "CategoryId",
    "Confidence",
    "LoanId",
    "LoanState",
    "MemberId",
    "MemberKind",
    "Price",
    "R",
    "TransactionId",
    "V",
    "loan_id",
    "member_id",
    "new_loan_id",
    "new_member_id",
    "new_transaction_id",
    "transaction_id",
]
